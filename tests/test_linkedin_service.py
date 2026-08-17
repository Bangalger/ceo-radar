from ceo_radar.services.linkedin_service import (
    JsonLookupStore,
    build_query,
    cache_key,
    lookup,
)


class MemoryStore:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    def find_one(self, key: str):
        return self.docs.get(key)

    def upsert(self, document: dict) -> None:
        self.docs[document["key"]] = document


def test_build_query_includes_context_and_linkedin_site():
    query = build_query(
        "Ana Pérez",
        "Trisul",
        "gerente comercial",
        "brasil",
    )
    assert '"Ana Pérez"' in query
    assert '"Trisul"' in query
    assert "gerente comercial" in query
    assert "brasil" in query
    assert "site:linkedin.com/in" in query


def test_cache_key_is_stable_for_normalized_names():
    assert cache_key("Ana Pérez", "Trisul") == cache_key("ana perez", "trisul")


def test_lookup_returns_cache_hit_without_search():
    store = MemoryStore()
    calls: list[str] = []

    def search_fn(query: str, api_key: str):
        calls.append(query)
        return [{"title": "Ana Pérez | LinkedIn", "link": "https://www.linkedin.com/in/ana", "snippet": ""}]

    first = lookup(
        "Ana Pérez",
        "Trisul",
        store=store,
        search_fn=search_fn,
    )
    assert first["cached"] is False
    assert first["error"] is None
    assert len(calls) == 1

    second = lookup(
        "Ana Pérez",
        "Trisul",
        store=store,
        search_fn=search_fn,
    )
    assert second["cached"] is True
    assert second["results"][0]["link"].endswith("/in/ana")
    assert len(calls) == 1


def test_force_refresh_ignores_cache():
    store = MemoryStore()
    calls = {"count": 0}

    def search_fn(query: str, api_key: str):
        calls["count"] += 1
        return [
            {
                "title": f"Resultado {calls['count']}",
                "link": f"https://www.linkedin.com/in/ana-{calls['count']}",
                "snippet": "",
            }
        ]

    lookup("Ana Pérez", "Trisul", store=store, search_fn=search_fn)
    refreshed = lookup(
        "Ana Pérez",
        "Trisul",
        store=store,
        search_fn=search_fn,
        force_refresh=True,
    )
    assert calls["count"] == 2
    assert refreshed["cached"] is False
    assert refreshed["results"][0]["link"].endswith("/in/ana-2")


def test_json_store_roundtrip(tmp_path):
    store = JsonLookupStore(tmp_path / "linkedin.json")
    store.upsert({"key": "abc", "person": "Ana", "results": []})
    assert store.find_one("abc")["person"] == "Ana"
    assert store.find_one("missing") is None
