"""Genera una vista curada de nombramientos desde revistas de nicho."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from ceo_radar.extraction import extract_entities_from_text  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
SOURCES = (
    RESULTS_DIR / "infocomercial_latest.json",
    RESULTS_DIR / "adlatina_latest.json",
)
OUTPUT = RESULTS_DIR / "curadas.json"
CURRENT_YEAR = datetime.now(UTC).year

NOMBRAMIENTO_MARKERS = (
    "nuevo",
    "nueva",
    "nombr",
    "design",
    "asume",
    "ascend",
    "director",
    "gerente",
    "ceo",
    "presidente",
    "marketing",
    "comercial",
)


def normalize(text: str) -> str:
    return text.lower()


def parse_year(date: str) -> int | None:
    for pattern in (r"(\d{2})/(\d{2})/(\d{4})", r"(\d{4})"):
        match = re.search(pattern, date)
        if match:
            if len(match.groups()) == 3:
                return int(match.group(3))
            return int(match.group(1))
    return None


def is_current_year(date: str) -> bool:
    year = parse_year(date)
    return year == CURRENT_YEAR if year else False


def looks_like_nombramiento(title: str, snippet: str) -> bool:
    text = normalize(f"{title} {snippet}")
    return any(marker in text for marker in NOMBRAMIENTO_MARKERS)


def has_extractable_signal(extracted: dict) -> bool:
    return bool(
        extracted.get("person")
        or extracted.get("role")
        or extracted.get("change_type")
        or (
            extracted.get("company")
            and extracted.get("company") != "Desconocida"
        )
    )


def load_results(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    source_name = path.stem.replace("_latest", "")
    results = []
    for item in data.get("results", []):
        results.append({**item, "source_file": source_name, "access_status": data.get("access_status", "ok")})
    return results


def main() -> None:
    raw_items = []
    source_stats: list[dict] = []

    for source in SOURCES:
        items = load_results(source)
        source_stats.append(
            {
                "source": source.name,
                "raw_count": len(items),
                "access_status": json.loads(source.read_text(encoding="utf-8")).get("access_status", "ok")
                if source.exists()
                else "missing",
            }
        )
        raw_items.extend(items)

    curated: list[dict] = []
    for item in raw_items:
        title = str(item.get("title", ""))
        snippet = str(item.get("snippet", ""))
        date = str(item.get("date", ""))

        if not looks_like_nombramiento(title, snippet):
            continue
        if date and not is_current_year(date):
            continue

        extracted = extract_entities_from_text(f"{title} {snippet}")
        if not has_extractable_signal(extracted):
            continue

        extracted.setdefault("country", "argentina")
        extracted.setdefault("confidence", {})["country"] = "media"

        curated.append(
            {
                **item,
                "extracted_data": extracted,
            }
        )

    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "year": CURRENT_YEAR,
                "scope": (
                    "Nombramientos curados desde revistas de nicho argentinas. "
                    "Se incluyen resultados del año vigente con señales de rol, "
                    "persona, empresa o tipo de cambio."
                ),
                "source_stats": source_stats,
                "raw_result_count": len(raw_items),
                "curated_result_count": len(curated),
                "results": curated,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Resultado curado: {len(curated)} nombramientos")
    print(f"Guardado en {OUTPUT}")


if __name__ == "__main__":
    main()
