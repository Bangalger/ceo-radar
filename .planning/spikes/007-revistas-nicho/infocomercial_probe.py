"""Spike 007a: busca nombramientos en Infocomercial (revista de nicho, Argentina).

Uso:
    py .planning/spikes/007-revistas-nicho/infocomercial_probe.py
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent / "results" / "infocomercial_latest.json"
BASE_URL = "https://blog.infocomercial.com"
SEARCHES = (
    "nuevo+gerente",
    "nueva+gerente",
    "nuevo+director",
    "nuevo+presidente",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": f"{BASE_URL}/",
}


def parse_articles(html: str, query: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    articles: list[dict[str, str]] = []

    for article in soup.select("article"):
        title_el = article.select_one("h2 a, h3 a, .entry-title a")
        if not title_el:
            continue
        date_el = article.select_one("time, .entry-date, .posted-on")
        excerpt_el = article.select_one(".entry-summary, .excerpt, p")
        articles.append(
            {
                "market": "argentina",
                "query": query.replace("+", " "),
                "title": title_el.get_text(strip=True),
                "source": "Infocomercial",
                "date": date_el.get_text(strip=True) if date_el else "",
                "link": title_el.get("href", ""),
                "snippet": excerpt_el.get_text(" ", strip=True)[:400] if excerpt_el else "",
            }
        )
    return articles


def fetch_search(session: requests.Session, query: str) -> tuple[int, list[dict[str, str]]]:
    url = f"{BASE_URL}/?s={query}"
    response = session.get(url, timeout=30)
    if response.status_code != 200:
        return response.status_code, []
    return response.status_code, parse_articles(response.text, query)


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)

    searches: list[dict[str, object]] = []
    seen_links: set[str] = set()
    unique_results: list[dict[str, str]] = []
    access_blocked = False

    try:
        session.get(BASE_URL, timeout=30)
    except requests.RequestException as error:
        print(f"Error al acceder a Infocomercial: {error}")
        return 1

    for query in SEARCHES:
        try:
            status, results = fetch_search(session, query)
        except requests.RequestException as error:
            print(f"Error en búsqueda '{query}': {error}")
            searches.append({"query": query, "status": "error", "result_count": 0})
            continue

        if status == 403:
            access_blocked = True

        searches.append(
            {
                "query": query.replace("+", " "),
                "status": status,
                "result_count": len(results),
            }
        )
        print(f"{query}: HTTP {status}, {len(results)} resultados")

        for result in results:
            link = result["link"]
            if link and link not in seen_links:
                seen_links.add(link)
                unique_results.append(result)

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Nombramientos y cambios de gerencia/dirección detectados en "
            "Infocomercial (blog.infocomercial.com), foco Argentina."
        ),
        "source_url": BASE_URL,
        "access_status": "blocked" if access_blocked else "ok",
        "access_note": (
            "El sitio responde HTTP 403 a requests automatizados (incluso con "
            "User-Agent de navegador). Se requeriría acceso alternativo "
            "(p. ej. proxy, API de terceros o revisión manual) para obtener datos."
            if access_blocked
            else ""
        ),
        "searches": searches,
        "unique_result_count": len(unique_results),
        "results": unique_results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Total único: {len(unique_results)}")
    if access_blocked:
        print("AVISO: acceso bloqueado por el sitio (HTTP 403)")
    print(f"Guardado en {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
