"""Builders HTML para componentes del dashboard."""

from __future__ import annotations

import html
import json
from typing import Any

import streamlit as st

from ceo_radar.models import Event, Feedback
from ceo_radar.ui.formatters import (
    build_event_short_title,
    format_country_label,
    format_feedback_banner_text,
    format_feedback_summary,
    format_source_label,
    get_status_badge_info,
)
from ceo_radar.ui.theme import icon


def _esc(value: Any) -> str:
    return html.escape(str(value)) if value is not None else ""


def render_html(markup: str) -> None:
    """Renderiza HTML colapsando la indentación.

    Markdown interpreta las líneas indentadas con 4+ espacios como bloque de
    código, así que el markup se aplana a una sola línea antes de inyectarlo.
    """
    flattened = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(flattened, unsafe_allow_html=True)


def sidebar_brand() -> None:
    render_html(
        """
        <div class="sidebar-brand">
            <div class="brand-name">CEO Radar</div>
            <p>Executive Intelligence</p>
        </div>
        """
    )


def page_header() -> None:
    render_html(
        """
        <div class="glass-header">
            <div class="page-header-inner">
                <div class="page-header-title">
                    <div class="header-title">CEO Radar: Oportunidades Ejecutivas</div>
                    <span class="live-badge">Live System</span>
                </div>
            </div>
        </div>
        """
    )


def meta_row(generated_at: str) -> None:
    render_html(
        f"""
        <div class="meta-row">
            {icon("history", size="16px")}
            <span>Última actualización: {_esc(generated_at)}</span>
        </div>
        """
    )


def stat_card(
    icon_name: str,
    value: int | str,
    label: str,
    *,
    icon_class: str = "primary",
) -> str:
    return f"""
    <div class="stat-card">
        <div>
            <span class="material-symbols-outlined stat-card-icon {icon_class}">{icon_name}</span>
        </div>
        <div>
            <div class="stat-card-value">{_esc(value)}</div>
            <div class="stat-card-label">{_esc(label)}</div>
        </div>
    </div>
    """


def stats_grid(result_count: int, source_counts: dict[str, Any]) -> None:
    cards = [
        stat_card("visibility", result_count, "Eventos Detectados"),
        stat_card("article", source_counts.get("cnv", 0), "CNV", icon_class="tertiary"),
        stat_card(
            "news",
            source_counts.get("google_news", 0),
            "Google News",
            icon_class="tertiary",
        ),
        stat_card(
            "gavel",
            source_counts.get("boletin_oficial", 0),
            "Boletín Oficial",
            icon_class="tertiary",
        ),
        stat_card(
            "book",
            source_counts.get("revistas_nicho", 0),
            "Revistas Nicho",
            icon_class="tertiary",
        ),
    ]
    render_html(f'<div class="stats-grid">{"".join(cards)}</div>')


def section_title(title: str, icon_name: str = "event_list") -> None:
    render_html(
        f"""
        <div class="section-title">
            {icon(icon_name, size="28px")}
            <div class="section-heading">{_esc(title)}</div>
        </div>
        """
    )


def section_label(text: str) -> None:
    render_html(f'<span class="action-section-label">{_esc(text)}</span>')


def status_badge(latest: Feedback | None) -> str:
    label, css_class = get_status_badge_info(latest)
    return f'<span class="badge {css_class}">{_esc(label)}</span>'


def event_header_html(event: Event, latest: Feedback | None) -> str:
    country = format_country_label(event.entities.get("country"))
    news_count = len(event.articles)
    plural = "s" if news_count != 1 else ""
    news_label = f"{news_count} Noticia{plural} encontrada{plural}"

    return f"""
    <div class="event-header">
        <div>
            <div class="event-header-title">{_esc(build_event_short_title(event))}</div>
            <div class="event-meta">
                <span class="event-meta-item">
                    {icon("location_on", size="14px")} {_esc(country)}
                </span>
                <span class="event-meta-dot">•</span>
                <span class="event-meta-item">{_esc(news_label)}</span>
            </div>
            <p class="event-dates">
                Primera vez visto: {event.first_seen.strftime("%Y-%m-%d")}
                · Última vez visto: {event.last_seen.strftime("%Y-%m-%d")}
            </p>
        </div>
        <div class="event-header-badges">{status_badge(latest)}</div>
    </div>
    """


def news_block(event: Event) -> str:
    if not event.articles:
        return """
        <div>
            <div class="news-block-header">
                <span class="section-label">Sin artículos</span>
            </div>
            <div class="news-block-content">
                <p>No hay artículos asociados a este evento.</p>
            </div>
        </div>
        """

    primary = event.articles[0]
    body = primary.description or primary.title

    primary_link = ""
    if primary.url:
        primary_link = (
            f'<p style="margin-top:0.75rem;font-size:13px;">'
            f'<a href="{_esc(primary.url)}" target="_blank">Ver fuente original</a></p>'
        )

    extra_articles = ""
    if len(event.articles) > 1:
        links = "".join(
            f'<li><a href="{_esc(article.url)}" target="_blank">{_esc(article.title)}</a>'
            f' <span style="color:var(--on-surface-variant);font-size:11px;">'
            f"({_esc(format_source_label(article.source))})</span></li>"
            for article in event.articles[1:]
        )
        extra_articles = f"""
        <div class="extra-articles">
            <p class="extra-articles-title">Otros artículos ({len(event.articles) - 1})</p>
            <ul>{links}</ul>
        </div>
        """

    return f"""
    <div>
        <div class="news-block-header">
            <span class="section-label">{_esc(format_source_label(primary.source))}</span>
            <span class="news-block-date">{primary.published_at.strftime("%d %b %Y")}</span>
        </div>
        <div class="news-block-content">
            <p>{_esc(body)}</p>
            {primary_link}
            {extra_articles}
        </div>
    </div>
    """


def _extraction_row(key: str, value: Any) -> str:
    return (
        '<div class="extraction-row">'
        f'<span class="extraction-key">"{_esc(key)}":</span>'
        f'<span class="extraction-value">{_esc(value)}</span>'
        "</div>"
    )


def extraction_panel(entities: dict[str, Any]) -> str:
    rows = ""
    for key, value in entities.items():
        if key == "confidence" and isinstance(value, dict):
            for sub_key, sub_value in value.items():
                rows += _extraction_row(f"confidence.{sub_key}", sub_value)
        elif isinstance(value, (dict, list)):
            rows += _extraction_row(key, json.dumps(value, ensure_ascii=False))
        else:
            rows += _extraction_row(key, value)

    if not rows:
        rows = (
            '<div class="extraction-row">'
            '<span class="extraction-value">Sin datos de extracción</span></div>'
        )

    return f"""
    <div>
        <div class="extraction-header">
            <span class="section-label">Detalles de Extracción</span>
            {icon("code", size="18px")}
        </div>
        <div class="extraction-panel">{rows}</div>
    </div>
    """


def feedback_banner_html(entry: Feedback) -> str:
    return f"""
    <div class="feedback-banner">
        {icon("info", filled=True, size="20px")}
        <div>
            <p class="feedback-banner-text">
                <strong>Estado vigente:</strong> {_esc(format_feedback_banner_text(entry))}
            </p>
            <p class="feedback-banner-meta">
                Actualizado el {entry.timestamp.strftime("%Y-%m-%d %H:%M")}
                por {_esc(entry.user_id or "Sistema")}
            </p>
        </div>
    </div>
    """


def collapsed_card_content(event: Event, latest: Feedback | None) -> str:
    """Contenido interno de una card colapsada (sin el contenedor)."""
    country = format_country_label(event.entities.get("country"))

    error_line = ""
    if not event.entities.get("company"):
        error_line = (
            '<p class="collapsed-card-error">Empresa sin identificar en la extracción</p>'
        )

    return f"""
    <div>
        <div>{status_badge(latest)}</div>
        <div class="collapsed-card-title">{_esc(build_event_short_title(event))}</div>
        <div class="event-meta">
            <span class="event-meta-item">
                {icon("location_on", size="14px")} {_esc(country)}
            </span>
            <span class="event-meta-dot">•</span>
            <span class="event-meta-item">{len(event.articles)} noticia(s)</span>
        </div>
        {error_line}
    </div>
    """


def feedback_history_html(history: list[Feedback]) -> str:
    if not history:
        return ""

    items = "".join(f"<li>{_esc(format_feedback_summary(entry))}</li>" for entry in history)
    return f"""
    <div class="feedback-history">
        <p class="feedback-history-title">Historial de feedback</p>
        <ul>{items}</ul>
    </div>
    """


def refresh_summary_html(ok_count: int, total: int, fail_count: int) -> str:
    if fail_count == 0:
        css_class = "success"
        message = f"Actualización completa: {ok_count}/{total} pasos exitosos."
    else:
        css_class = "warning"
        message = (
            f"Actualización parcial: {ok_count}/{total} pasos exitosos, "
            f"{fail_count} con error."
        )

    return f'<div class="refresh-summary {css_class}"><p>{_esc(message)}</p></div>'


def footer(source_count: int) -> None:
    render_html(
        f"""
        <div class="app-footer">
            <span class="app-footer-text">© 2026 CEO Radar Intelligence Platform</span>
            <span class="app-footer-text">{source_count} fuentes monitoreadas</span>
        </div>
        """
    )


def empty_state(message: str) -> None:
    render_html(f'<div class="empty-state"><p>{_esc(message)}</p></div>')
