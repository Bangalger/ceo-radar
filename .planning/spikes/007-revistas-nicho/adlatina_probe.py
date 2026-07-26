"""Spike 007b: busca nombramientos en Marketers by Adlatina (revista de nicho).

Uso:
    py .planning/spikes/007-revistas-nicho/adlatina_probe.py
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent / "results" / "adlatina_latest.json"
BASE_URL = "https://www.marketersbyadlatina.com"
CATEGORY_URL = f"{BASE_URL}/categoria/nombramientos"
MAX_PAGES = 5

HEADERS = {
    "User-Agent": "CEO-Radar/0.1 (+public niche media monitor)",
    "Accept-Language": "es-AR,es;q=0.9",
}


def parse_date(raw: str) -> str:
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", raw)
    if not match:
        return raw.strip()
    day, month, year = match.groups()
    return f"{month}/{day}/{year}"


def parse_page(html: str, page: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, str]] = []

    for article in soup.select("article"):
        title_el = article.select_one("h2, h3")
        link_el = article.select_one("a[href*='/articulo/']")
        date_el = article.select_one("small.text-muted")
        excerpt_el = article.select_one("p")

        title = title_el.get_text(strip=True) if title_el else ""
        link = link_el.get("href", "") if link_el else ""
        if not title or not link:
            continue

        raw_date = date_el.get_text(strip=True) if date_el else ""
        results.append(
            {
                "market": "latam_es",
                "page": str(page),
                "query": "nombramientos",
                "title": title,
                "source": "Marketers by Adlatina",
                "date": parse_date(raw_date),
                "link": urljoin(BASE_URL, link),
                "snippet": excerpt_el.get_text(" ", strip=True)[:400] if excerpt_el else "",
            }
        )
    return results


def fetch_page(page: int) -> list[dict[str, str]]:
    url = CATEGORY_URL if page == 1 else f"{CATEGORY_URL}?page={page}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return parse_page(response.text, page)


def main() -> int:
    pages: list[dict[str, object]] = []
    seen_links: set[str] = set()
    unique_results: list[dict[str, str]] = []

    try:
        for page in range(1, MAX_PAGES + 1):
            results = fetch_page(page)
            pages.append({"page": page, "result_count": len(results)})
            print(f"Página {page}: {len(results)} artículos")

            if not results:
                break

            for result in results:
                link = result["link"]
                if link not in seen_links:
                    seen_links.add(link)
                    unique_results.append(result)
    except requests.RequestException as error:
        print(f"Error al consultar Adlatina: {error}")
        return 1

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Nombramientos ejecutivos en marketing, comunicación y negocios "
            "publicados en Marketers by Adlatina. Foco inicial: Argentina y Latam."
        ),
        "source_url": CATEGORY_URL,
        "access_status": "ok",
        "pages": pages,
        "unique_result_count": len(unique_results),
        "results": unique_results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Total único: {len(unique_results)}")
    print(f"Guardado en {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
