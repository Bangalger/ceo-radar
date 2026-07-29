"""Formateadores de texto para la UI del dashboard."""

from __future__ import annotations

from ceo_radar.models import Event, Feedback
from ceo_radar.services import feedback_service

ROLE_LABELS: dict[str, str] = {
    "ceo": "Nuevo CEO",
    "director ejecutivo": "Nuevo director ejecutivo",
    "diretor executivo": "Nuevo director ejecutivo",
    "gerente comercial": "Nuevo gerente comercial",
    "director comercial": "Nuevo director comercial",
    "diretor comercial": "Nuevo director comercial",
    "gerente general": "Nuevo gerente general",
    "presidente": "Nuevo presidente",
    "vicepresidente": "Nuevo vicepresidente",
    "director titular": "Nuevo director titular",
    "directora titular": "Nueva directora titular",
    "director suplente": "Nuevo director suplente",
    "directora suplente": "Nueva directora suplente",
    "directorio": "Cambio de directorio",
    "gerente": "Nuevo gerente",
    "director": "Nuevo director",
}

COUNTRY_LABELS: dict[str, str] = {
    "argentina": "Argentina",
    "brasil": "Brasil",
    "chile": "Chile",
}

SOURCE_LABELS: dict[str, str] = {
    "cnv": "CNV — Hechos Relevantes",
    "google_news": "Google News",
    "boletin_oficial": "Boletín Oficial",
    "adlatina": "Adlatina",
    "infocomercial": "Infocomercial",
}


def format_role_label(role: str | None) -> str:
    if not role:
        return "Cambio ejecutivo"
    return ROLE_LABELS.get(role.lower(), f"Nuevo {role}")


def format_country_label(country: str | None) -> str:
    if not country:
        return "país desconocido"
    return COUNTRY_LABELS.get(country.lower(), country.title())


def format_source_label(source: str | None) -> str:
    if not source:
        return "Fuente desconocida"
    return SOURCE_LABELS.get(source.lower(), source.replace("_", " ").title())


def build_event_title(event: Event) -> str:
    entities = event.entities
    company = entities.get("company") or "Empresa no identificada"
    role_label = format_role_label(entities.get("role"))
    country_label = format_country_label(entities.get("country"))
    person = entities.get("person")

    if person:
        return f"{company} — {person} — {role_label} — {country_label}"
    return f"{company} — {role_label} — {country_label}"


def build_event_short_title(event: Event) -> str:
    """Título corto para cards colapsadas (sin país)."""
    entities = event.entities
    company = entities.get("company") or "Empresa no identificada"
    role_label = format_role_label(entities.get("role"))
    person = entities.get("person")

    if person:
        return f"{company} — {person} — {role_label}"
    return f"{company} — {role_label}"


def format_feedback_summary(entry: Feedback) -> str:
    status_label = feedback_service.STATUS_LABELS.get(entry.status, entry.status)
    parts = [status_label]
    if entry.reason:
        reason_label = feedback_service.REASON_LABELS.get(entry.reason, entry.reason)
        parts.append(reason_label)
    if entry.comment:
        parts.append(f'"{entry.comment}"')
    parts.append(entry.timestamp.strftime("%Y-%m-%d %H:%M"))
    return " · ".join(parts)


def format_feedback_banner_text(entry: Feedback) -> str:
    """Texto del banner de estado vigente (sin timestamp)."""
    status_label = feedback_service.STATUS_LABELS.get(entry.status, entry.status)
    parts = [status_label]
    if entry.reason:
        reason_label = feedback_service.REASON_LABELS.get(entry.reason, entry.reason)
        parts.append(reason_label)
    if entry.comment:
        parts.append(f'"{entry.comment}"')
    return ". ".join(parts)


def get_status_badge_info(
    latest: Feedback | None,
) -> tuple[str, str]:
    """Retorna (label, css_class) para el badge de estado."""
    if latest is None:
        return "Pendiente", "badge-pending"
    if latest.status == "buen_candidato":
        return "Buen candidato", "badge-good"
    if latest.status == "revisar":
        return "Revisar", "badge-review"
    if latest.status == "no_relevante":
        return "Archivo", "badge-archive"
    return latest.status, "badge-pending"


def company_missing(event: Event) -> bool:
    return not event.entities.get("company")
