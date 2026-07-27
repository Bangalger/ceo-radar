"""Persistencia y consulta de feedback de eventos."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ceo_radar.db import get_feedback_collection
from ceo_radar.models import Feedback

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


def _doc_to_feedback(doc: dict) -> Feedback:
    payload = {key: value for key, value in doc.items() if key != "_id"}
    return Feedback(**payload)


def load_feedback_log() -> list[Feedback]:
    collection = get_feedback_collection()
    docs = collection.find().sort("timestamp", 1)
    return [_doc_to_feedback(doc) for doc in docs]


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

    get_feedback_collection().insert_one(entry.model_dump(mode="json"))
    return entry


def is_rejected(event_id: str, latest_by_event: Optional[dict[str, Feedback]] = None) -> bool:
    latest = latest_by_event or latest_status_by_event()
    entry = latest.get(event_id)
    return entry is not None and entry.status == "no_relevante"


def get_latest_feedback(
    event_id: str,
    latest_by_event: Optional[dict[str, Feedback]] = None,
) -> Optional[Feedback]:
    latest = latest_by_event or latest_status_by_event()
    return latest.get(event_id)


def get_feedback_version() -> tuple[int, str]:
    """Versión liviana del log de feedback para invalidar caché en la UI."""
    collection = get_feedback_collection()
    count = collection.count_documents({})
    if count == 0:
        return 0, ""

    latest = collection.find_one({}, sort=[("timestamp", -1)], projection={"timestamp": 1})
    max_timestamp = latest["timestamp"] if latest else ""
    if isinstance(max_timestamp, datetime):
        max_timestamp = max_timestamp.isoformat()
    return count, str(max_timestamp)
