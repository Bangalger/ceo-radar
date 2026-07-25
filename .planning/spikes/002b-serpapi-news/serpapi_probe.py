"""Spike 002b: valida SerpAPI/Google News para cambios ejecutivos en Latam.

Uso:
    py .planning/spikes/002b-serpapi-news/serpapi_probe.py

Lee SERPAPI_API_KEY o SERPAPI_KEY desde .env. El segundo nombre permite
reutilizar la configuración existente en corralito_radar.
"""

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
ENV_FILE = ROOT / ".env"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

QUERIES = (
    '"nuevo CEO" OR "designó CEO" Argentina OR Brasil',
    '"nuevo gerente comercial" OR "director comercial" Argentina OR Brasil',
)


def load_env(path: Path) -> dict[str, str]:
    """Carga un .env simple sin requerir paquetes externos."""
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


def search_news(api_key: str, query: str) -> list[dict[str, str]]:
    params = urlencode(
        {
            "engine": "google_news",
            "q": query,
            "gl": "ar",
            "hl": "es-419",
            "api_key": api_key,
        }
    )
    url = f"https://serpapi.com/search.json?{params}"
    with urlopen(url, timeout=30) as response:
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
        print(
            "Falta SERPAPI_API_KEY (o SERPAPI_KEY) en .env.",
            file=sys.stderr,
        )
        return 2

    collected: list[dict[str, object]] = []
    try:
        for query in QUERIES:
            results = search_news(api_key, query)
            collected.append({"query": query, "results": results})
            print(f"\nConsulta: {query}\nResultados: {len(results)}")
            for item in results[:5]:
                print(f"- {item['title']} ({item['source']}, {item['date']})")
                print(f"  {item['link']}")
    except (HTTPError, URLError, RuntimeError, TimeoutError) as error:
        print(f"Error al consultar SerpAPI: {error}", file=sys.stderr)
        return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / "latest.json"
    output.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "queries": collected,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados guardados en {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
