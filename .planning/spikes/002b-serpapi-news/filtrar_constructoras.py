"""Genera una vista curada del resultado amplio de constructoras."""

from __future__ import annotations

import json
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
SOURCE = RESULTS_DIR / "constructoras_latest.json"
OUTPUT = RESULTS_DIR / "constructoras_curadas.json"

SECTOR_MARKERS = (
    "constructora",
    "construtora",
    "incorporadora",
    "inmobiliaria",
    "desarrolladora inmobiliaria",
    "empreendimentos",
    "realty",
)

KNOWN_LATAM_COMPANIES = (
    "gcdi",
    "cgdi",
    "tglt",
    "urbanova",
    "milicic",
    "bonatti",
    "contract workplaces",
    "tenda",
    "trisul",
    "dasart",
    "pdg",
    "tarraf",
    "allterra",
    "grupo marquise",
    "gafisa",
    "vci",
    "novonor",
    "odebrecht",
    "caparao",
    "rossi",
    "grupo diagonal",
    "consciente",
    "mota machado",
    "rni",
)

NON_LATAM_COMPANIES = (
    "tektia",
    "ulma",
    "seyses",
    "rubau",
    "fcc",
    "mota-engil",
    "mota engil",
    "fortera",
    "grupo afa",
    "teixeira duarte",
    "algeco",
    "berkshire hathaway",
)

TARGET_ROLES = (
    "ceo",
    "director ejecutivo",
    "diretor executivo",
    "gerente comercial",
    "director comercial",
    "diretor comercial",
)

CURRENT_YEAR = datetime.now(UTC).year


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def is_relevant(title: str) -> bool:
    normalized = normalize(title)
    if any(company in normalized for company in NON_LATAM_COMPANIES):
        return False
    has_target_role = any(role in normalized for role in TARGET_ROLES)
    has_sector = any(marker in normalized for marker in SECTOR_MARKERS) or any(
        company in normalized for company in KNOWN_LATAM_COMPANIES
    )
    return has_target_role and has_sector


def is_current_year(date: str) -> bool:
    try:
        return datetime.strptime(date[:10], "%m/%d/%Y").year == CURRENT_YEAR
    except ValueError:
        return False


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    curated = [
        result
        for result in data["results"]
        if is_relevant(str(result["title"]))
        and is_current_year(str(result["date"]))
    ]
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": data["generated_at"],
                "scope": data["scope"],
                "selection": (
                    "Selección heurística: el titular identifica el sector o una "
                    "empresa constructora/desarrolladora conocida de Latinoamérica, "
                    f"con fecha dentro de {CURRENT_YEAR}."
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
