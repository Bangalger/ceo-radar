"""Carga y regeneración de eventos unificados."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ceo_radar.models import Event
from ceo_radar.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_FILE = ROOT / ".planning" / "results" / "oportunidades_unificadas.json"


def get_output_file() -> Path:
    return OUTPUT_FILE


def ensure_events_file() -> None:
    if not OUTPUT_FILE.exists():
        run_pipeline()


def regenerate_events() -> None:
    run_pipeline()


def load_events() -> tuple[list[Event], str, dict[str, Any], int]:
    ensure_events_file()
    data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    events = [Event(**item) for item in data["results"]]
    return (
        events,
        data["generated_at"],
        data["source_counts"],
        data["result_count"],
    )


def get_events_file_mtime() -> float:
    ensure_events_file()
    return OUTPUT_FILE.stat().st_mtime
