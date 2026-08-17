"""Detecta cambios ejecutivos publicados como hechos relevantes en la CNV."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from ceo_radar.timeframe import is_year_allowed  # noqa: E402

SOURCE_URL = "https://www.cnv.gov.ar/SitioWeb/HechosRelevantes"
OUTPUT = Path(__file__).resolve().parent / "results" / "cnv_cambios_ejecutivos.json"

TARGET_ROLES = (
    "CEO",
    "DIRECTOR EJECUTIVO",
    "DIRECTORA EJECUTIVA",
    "GERENTE COMERCIAL",
    "DIRECTOR COMERCIAL",
    "DIRECTORA COMERCIAL",
)

CHANGE_MARKERS = (
    "RENUNC",
    "REEMPLAZ",
    "DESIGN",
    "NOMBR",
    "ASUME",
    "CESE",
    "CAMBIO",
    "BAJA",
    "LICENCIA",
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(
        char for char in decomposed if not unicodedata.combining(char)
    ).upper()


def clean(text: str) -> str:
    return " ".join(text.split())


def field(record: dict[str, str], prefix: str) -> str:
    for key, value in record.items():
        if normalize(key).startswith(prefix):
            return value
    return ""


def is_target_change(description: str) -> bool:
    normalized = normalize(description)
    has_role = any(role in normalized for role in TARGET_ROLES)
    has_change = any(marker in normalized for marker in CHANGE_MARKERS)
    return has_role and has_change


def is_date_in_window(date: str) -> bool:
    match = re.search(r"\b(20\d{2})\b", date)
    return bool(match and is_year_allowed(int(match.group(1))))


def parse_table(table: Tag, table_index: int) -> list[dict[str, str | int]]:
    headers = [clean(cell.get_text(" ", strip=True)) for cell in table.select("thead th")]
    records: list[dict[str, str | int]] = []

    for row in table.select("tbody tr"):
        cells = row.select("td")
        if not cells:
            continue

        values = [clean(cell.get_text(" ", strip=True)) for cell in cells]
        record = dict(zip(headers, values, strict=False))
        date = field(record, "FECHA")
        description = field(record, "DESCRIPCI")
        entity = (
            field(record, "ENTIDAD")
            or field(record, "RAZ")
            or field(record, "FIDEICOMISO")
        )

        if not is_date_in_window(date) or not is_target_change(description):
            continue

        link = row.select_one("a[href]")
        records.append(
            {
                "date": date,
                "entity": entity,
                "description": description,
                "document": field(record, "DOCUMENTO"),
                "presentation_url": str(link["href"]) if link else "",
                "table_index": table_index,
            }
        )

    return records


def main() -> int:
    try:
        response = requests.get(
            SOURCE_URL,
            headers={"User-Agent": "CEO-Radar/0.1 (+public CNV data monitor)"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Error al consultar CNV: {error}")
        return 1

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict[str, str | int]] = []
    for index, table in enumerate(soup.select("table")):
        results.extend(parse_table(table, index))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "fetched_at": datetime.now(UTC).isoformat(),
                "source": "Comisión Nacional de Valores (CNV) — Hechos Relevantes",
                "source_url": SOURCE_URL,
                "year": datetime.now(UTC).year,
                "criteria": {
                    "roles": TARGET_ROLES,
                    "change_markers": CHANGE_MARKERS,
                },
                "result_count": len(results),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Cambios ejecutivos detectados: {len(results)}")
    for result in results:
        print(f"- {result['date']} | {result['entity']}")
        print(f"  {result['description']}")
    print(f"Guardado en {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
