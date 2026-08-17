"""Búsqueda de perfiles de LinkedIn vía SerpAPI, con caché."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.parse import urlencode
from urllib.request import urlopen

from ceo_radar.catalogs import normalize
from ceo_radar.config import get_serpapi_key

ROOT = Path(__file__).resolve().parents[3]
JSON_CACHE_FILE = ROOT / "data" / "linkedin_lookups.json"


class LookupStore(Protocol):
    def find_one(self, key: str) -> dict[str, Any] | None: ...

    def upsert(self, document: dict[str, Any]) -> None: ...


class JsonLookupStore:
    def __init__(self, path: Path = JSON_CACHE_FILE) -> None:
        self.path = path

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        return {entry["key"]: entry for entry in entries if "key" in entry}

    def _save(self, entries: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"entries": list(entries.values())}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def find_one(self, key: str) -> dict[str, Any] | None:
        return self._load().get(key)

    def upsert(self, document: dict[str, Any]) -> None:
        entries = self._load()
        entries[document["key"]] = document
        self._save(entries)


class MongoLookupStore:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    def find_one(self, key: str) -> dict[str, Any] | None:
        document = self.collection.find_one({"key": key}, {"_id": 0})
        return dict(document) if document else None

    def upsert(self, document: dict[str, Any]) -> None:
        self.collection.update_one(
            {"key": document["key"]},
            {"$set": document},
            upsert=True,
        )


def cache_key(person: str, company: str | None = None) -> str:
    payload = f"{normalize(person)}|{normalize(company or '')}"
    return sha256(payload.encode()).hexdigest()


def build_query(
    person: str,
    company: str | None = None,
    role: str | None = None,
    country: str | None = None,
) -> str:
    parts = [f'"{person.strip()}"']
    if company:
        parts.append(f'"{company.strip()}"')
    if role:
        parts.append(role.strip())
    if country:
        parts.append(country.strip())
    parts.append("site:linkedin.com/in")
    return " ".join(parts)


def _is_linkedin_profile(url: str) -> bool:
    lowered = url.lower()
    return "linkedin.com/in/" in lowered or "linkedin.com/pub/" in lowered


def default_search(query: str, api_key: str) -> list[dict[str, str]]:
    params = urlencode(
        {
            "engine": "google",
            "q": query,
            "num": 5,
            "api_key": api_key,
        }
    )
    with urlopen(f"https://serpapi.com/search.json?{params}", timeout=30) as response:
        payload = json.load(response)
    if error := payload.get("error"):
        raise RuntimeError(str(error))

    results: list[dict[str, str]] = []
    for item in payload.get("organic_results", []):
        link = str(item.get("link") or "")
        if not _is_linkedin_profile(link):
            continue
        results.append(
            {
                "title": str(item.get("title") or ""),
                "link": link,
                "snippet": str(item.get("snippet") or ""),
            }
        )
        if len(results) >= 3:
            break
    return results


def get_default_store() -> LookupStore:
    try:
        from ceo_radar.db import get_linkedin_collection

        return MongoLookupStore(get_linkedin_collection())
    except Exception:
        return JsonLookupStore()


def lookup(
    person: str,
    company: str | None = None,
    role: str | None = None,
    country: str | None = None,
    *,
    force_refresh: bool = False,
    store: LookupStore | None = None,
    search_fn: Callable[[str, str], list[dict[str, str]]] | None = None,
) -> dict[str, Any]:
    """Busca perfiles de LinkedIn. Nunca lanza: errores van en el dict."""
    person = (person or "").strip()
    if not person:
        return {
            "key": "",
            "person": person,
            "company": company,
            "query": "",
            "results": [],
            "searched_at": None,
            "cached": False,
            "error": "No hay nombre de persona para buscar.",
        }

    key = cache_key(person, company)
    query = build_query(person, company, role, country)
    active_store = store or get_default_store()

    if not force_refresh:
        cached = active_store.find_one(key)
        if cached:
            return {**cached, "cached": True, "error": None}

    search = search_fn or default_search
    api_key = get_serpapi_key()
    if search_fn is None and not api_key:
        return {
            "key": key,
            "person": person,
            "company": company,
            "query": query,
            "results": [],
            "searched_at": None,
            "cached": False,
            "error": "Falta SERPAPI_API_KEY para buscar LinkedIn.",
        }

    try:
        results = search(query, api_key or "")
    except Exception as exc:  # noqa: BLE001
        return {
            "key": key,
            "person": person,
            "company": company,
            "query": query,
            "results": [],
            "searched_at": None,
            "cached": False,
            "error": str(exc),
        }

    document = {
        "key": key,
        "person": person,
        "company": company,
        "role": role,
        "country": country,
        "query": query,
        "results": results,
        "searched_at": datetime.now(UTC).isoformat(),
    }
    try:
        active_store.upsert(document)
    except Exception:
        pass

    return {**document, "cached": False, "error": None}
