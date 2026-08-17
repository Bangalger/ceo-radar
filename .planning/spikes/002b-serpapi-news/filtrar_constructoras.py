"""Genera una vista curada del resultado amplio de constructoras."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from ceo_radar.catalogs import (  # noqa: E402
    LATAM_COMPANIES,
    NON_LATAM_COMPANIES,
    SECTOR_MARKERS,
    TARGET_ROLES,
    normalize,
)
from ceo_radar.timeframe import allowed_years, is_year_allowed  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
SOURCE = RESULTS_DIR / "constructoras_latest.json"
OUTPUT = RESULTS_DIR / "constructoras_curadas.json"


def is_relevant(title: str) -> bool:
    normalized = normalize(title)
    if any(company in normalized for company in NON_LATAM_COMPANIES):
        return False
    has_target_role = any(role in normalized for role in TARGET_ROLES)
    has_sector = any(marker in normalized for marker in SECTOR_MARKERS) or any(
        company in normalized for company in LATAM_COMPANIES
    )
    return has_target_role and has_sector


def is_date_in_window(date: str) -> bool:
    try:
        return is_year_allowed(datetime.strptime(date[:10], "%m/%d/%Y").year)
    except ValueError:
        return False


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    curated = [
        result
        for result in data["results"]
        if is_relevant(str(result["title"]))
        and is_date_in_window(str(result["date"]))
    ]
    years_str = ", ".join(str(y) for y in sorted(allowed_years()))
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": data["generated_at"],
                "scope": data["scope"],
                "selection": (
                    "Selección heurística: el titular identifica el sector o una "
                    "empresa constructora/desarrolladora conocida de Latinoamérica, "
                    f"con fecha dentro de [{years_str}]."
                ),
                "source_result": SOURCE.name,
                "raw_result_count": data["unique_result_count"],
                "curated_result_count": len(curated),
                "results": curated,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Resultado curado: {len(curated)} noticias")
    print(f"Guardado en {OUTPUT}")


if __name__ == "__main__":
    main()
