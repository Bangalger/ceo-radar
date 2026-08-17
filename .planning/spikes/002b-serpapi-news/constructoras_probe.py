"""Busca cambios ejecutivos en empresas constructoras de Latinoamérica."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
ENV_FILE = ROOT / ".env"
OUTPUT = Path(__file__).resolve().parent / "results" / "constructoras_latest.json"

from ceo_radar.timeframe import allowed_years  # noqa: E402

SEARCHES = (
    {
        "market": "latam_es",
        "gl": "ar",
        "hl": "es-419",
        "query": (
            '("nuevo CEO" OR "nuevo director ejecutivo" OR "asume como CEO") '
            "(constructora OR construcción OR inmobiliaria OR desarrolladora) "
            "(Argentina OR México OR Chile OR Colombia OR Perú OR Uruguay)"
        ),
    },
    {
        "market": "latam_es_comercial",
        "gl": "ar",
        "hl": "es-419",
        "query": (
            '("nuevo gerente comercial" OR "nuevo director comercial" '
            'OR "asume como gerente comercial") '
            "(constructora OR construcción OR inmobiliaria OR desarrolladora) "
            "(Argentina OR México OR Chile OR Colombia OR Perú OR Uruguay)"
        ),
    },
    {
        "market": "brasil",
        "gl": "br",
        "hl": "pt-br",
        "query": (
            '("novo CEO" OR "novo diretor executivo" OR "assume como CEO") '
            "(construtora OR construção OR incorporadora)"
        ),
    },
    {
        "market": "brasil_comercial",
        "gl": "br",
        "hl": "pt-br",
        "query": (
            '("novo gerente comercial" OR "novo diretor comercial" '
            'OR "assume como diretor comercial") '
            "(construtora OR construção OR incorporadora)"
        ),
    },
)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def search_news(
    api_key: str, query: str, gl: str, hl: str
) -> list[dict[str, str]]:
    params = urlencode(
        {
            "engine": "google_news",
            "q": query,
            "gl": gl,
            "hl": hl,
            "api_key": api_key,
        }
    )
    with urlopen(f"https://serpapi.com/search.json?{params}", timeout=30) as response:
        payload = json.load(response)
    if error := payload.get("error"):
        raise RuntimeError(str(error))
    return [
        {
            "title": item.get("title", ""),
            "source": item.get("source", {}).get("name", ""),
            "date": item.get("date", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in payload.get("news_results", [])
    ]


def main() -> int:
    env = {**load_env(ENV_FILE), **os.environ}
    api_key = env.get("SERPAPI_API_KEY") or env.get("SERPAPI_KEY")
    if not api_key:
        print("Falta SERPAPI_API_KEY (o SERPAPI_KEY) en .env.", file=sys.stderr)
        return 2

    searches: list[dict[str, object]] = []
    seen_links: set[str] = set()
    unique_results: list[dict[str, str]] = []

    years = sorted(allowed_years())

    try:
        for search in SEARCHES:
            for year in years:
                date_filter = f" after:{year}-01-01 before:{year}-12-31"
                query_with_date = str(search["query"]) + date_filter
                results = search_news(
                    api_key,
                    query_with_date,
                    str(search["gl"]),
                    str(search["hl"]),
                )
                searches.append({**search, "year": year, "result_count": len(results)})
                print(f"{search['market']} ({year}): {len(results)} resultados")
                for result in results:
                    link = result["link"]
                    if link and link not in seen_links:
                        seen_links.add(link)
                        unique_results.append(
                            {
                                "market": str(search["market"]),
                                "year_window": year,
                                **result,
                            }
                        )
    except (HTTPError, URLError, RuntimeError, TimeoutError) as error:
        print(f"Error al consultar SerpAPI: {error}", file=sys.stderr)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "scope": (
                    "Cambios de CEO, directores ejecutivos y gerentes/directores "
                    "comerciales en constructoras, desarrolladoras e inmobiliarias "
                    "de Latinoamérica."
                ),
                "searches": searches,
                "unique_result_count": len(unique_results),
                "results": unique_results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Total único: {len(unique_results)}")
    print(f"Guardado en {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
