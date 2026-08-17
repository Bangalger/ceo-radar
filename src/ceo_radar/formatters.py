"""Etiquetas legibles para persona, rol y timing de anuncios."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ceo_radar.models import Event

ROLE_LABELS = {
    "ceo": "CEO",
    "director ejecutivo": "Director ejecutivo",
    "diretor executivo": "Director ejecutivo",
    "gerente comercial": "Gerente comercial",
    "director comercial": "Director comercial",
    "diretor comercial": "Director comercial",
    "gerente general": "Gerente general",
    "presidente": "Presidente",
    "vicepresidente": "Vicepresidente",
    "director titular": "Director titular",
    "directora titular": "Directora titular",
    "director suplente": "Director suplente",
    "directora suplente": "Directora suplente",
    "directorio": "Directorio",
    "gerente": "Gerente",
    "director": "Director",
}

MONTHS_SHORT = {
    1: "ene",
    2: "feb",
    3: "mar",
    4: "abr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dic",
}


def format_role_label(role: str | None) -> str:
    if not role:
        return "Posición no identificada"
    return ROLE_LABELS.get(role.lower(), role)


def format_person_display(entities: dict[str, Any]) -> str:
    person = (entities.get("person") or "").strip()
    return person or "Persona no identificada"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _relative_timing(when: datetime, now: datetime) -> str:
    delta = _as_utc(now) - _as_utc(when)
    days = max(delta.days, 0)
    if days <= 0:
        return "hoy"
    if days == 1:
        return "ayer"
    if days < 30:
        return f"hace {days} días"
    months = max(days // 30, 1)
    if months < 12:
        label = "mes" if months == 1 else "meses"
        return f"hace {months} {label}"
    years = max(months // 12, 1)
    label = "año" if years == 1 else "años"
    return f"hace {years} {label}"


def format_timing(event: Event, now: datetime | None = None) -> str:
    """Fecha de anuncio (publicación) con texto relativo."""
    when = event.first_seen
    current = now or datetime.now(UTC)
    date_label = f"{when.day} {MONTHS_SHORT[when.month]} {when.year}"
    return f"{date_label} ({_relative_timing(when, current)})"
