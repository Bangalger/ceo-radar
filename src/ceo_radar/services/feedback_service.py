"""Persistencia y consulta de feedback de eventos."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ceo_radar.models import Feedback

ROOT = Path(__file__).resolve().parents[3]
FEEDBACK_FILE = ROOT / "data" / "feedback.json"

LOCAL_USER_ID = "local"

STATUSES = ("buen_candidato", "revisar", "no_relevante")

STATUS_LABELS: dict[str, str] = {
    "buen_candidato": "Buen candidato",
    "revisar": "Revisar",
    "no_relevante": "No relevante",
}

REASONS_BY_STATUS: dict[str, list[str]] = {
    "no_relevante": [
        "empresa_no_objetivo",
        "rol_no_relevante",
        "duplicado",
        "fuera_de_alcance_geografico",
        "informacion_incorrecta",
        "otro",
    ],
    "revisar": [
        "extraccion_dudosa",
        "informacion_incompleta",
        "requiere_verificacion_manual",
        "otro",
    ],
    "buen_candidato": [],
}

REASON_LABELS: dict[str, str] = {
    "empresa_no_objetivo": "Empresa no objetivo",
    "rol_no_relevante": "Rol no relevante",
    "duplicado": "Duplicado",
    "fuera_de_alcance_geografico": "Fuera de alcance geográfico",
    "informacion_incorrecta": "Información incorrecta",
    "extraccion_dudosa": "Extracción dudosa",
    "informacion_incompleta": "Información incompleta",
    "requiere_verificacion_manual": "Requiere verificación manual",
    "otro": "Otro",
}


def get_feedback_file() -> Path:
    return FEEDBACK_FILE


def _ensure_feedback_dir() -> None:
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_feedback_log() -> list[Feedback]:
    if not FEEDBACK_FILE.exists():
        return []
    data = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    return [Feedback(**entry) for entry in data.get("entries", [])]


def save_feedback_log(entries: list[Feedback]) -> None:
    _ensure_feedback_dir()
    FEEDBACK_FILE.write_text(
        json.dumps(
            {"entries": [entry.model_dump(mode="json") for entry in entries]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def latest_status_by_event() -> dict[str, Feedback]:
    latest: dict[str, Feedback] = {}
    for entry in load_feedback_log():
        current = latest.get(entry.event_id)
        if current is None or entry.timestamp > current.timestamp:
            latest[entry.event_id] = entry
    return latest


def feedback_history_for_event(event_id: str) -> list[Feedback]:
    return sorted(
        (entry for entry in load_feedback_log() if entry.event_id == event_id),
        key=lambda e: e.timestamp,
    )


def submit_feedback(
    event_id: str,
    status: str,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    user_id: str = LOCAL_USER_ID,
) -> Feedback:
    if status not in STATUSES:
        raise ValueError(f"Estado inválido: {status}")

    allowed_reasons = REASONS_BY_STATUS.get(status, [])
    if status in ("no_relevante", "revisar"):
        if not reason or reason not in allowed_reasons:
            raise ValueError(f"Motivo requerido para estado '{status}'")
    else:
        reason = None

    comment = (comment or "").strip() or None

    entry = Feedback(
        event_id=event_id,
        user_id=user_id,
        status=status,
        reason=reason,
        comment=comment,
        timestamp=datetime.now(),
    )

    entries = load_feedback_log()
    entries.append(entry)
    save_feedback_log(entries)
    return entry


def is_rejected(event_id: str, latest_by_event: Optional[dict[str, Feedback]] = None) -> bool:
    latest = latest_by_event or latest_status_by_event()
    entry = latest.get(event_id)
    return entry is not None and entry.status == "no_relevante"


def get_latest_feedback(event_id: str, latest_by_event: Optional[dict[str, Feedback]] = None) -> Optional[Feedback]:
    latest = latest_by_event or latest_status_by_event()
    return latest.get(event_id)


def get_feedback_file_mtime() -> float:
    if not FEEDBACK_FILE.exists():
        return 0.0
    return FEEDBACK_FILE.stat().st_mtime
