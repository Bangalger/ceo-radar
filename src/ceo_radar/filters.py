"""Filtros de exploración para el dashboard CEO Radar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ceo_radar.catalogs import (
    DECISION_ROLE_GROUPS,
    ROLE_GROUP_LABELS,
    ROLE_GROUPS,
    SECTOR_CATALOG,
    get_role_group,
)
from ceo_radar.models import Event

SECTOR_LABELS: dict[str, str] = {
    "construccion": "Construcción",
    "inmobiliario": "Inmobiliario",
    "retail_consumo": "Retail / Consumo",
    "alimentos_bebidas": "Alimentos y Bebidas",
    "tecnologia": "Tecnología",
    "finanzas": "Finanzas",
    "salud": "Salud",
    "marketing_publicidad": "Marketing / Publicidad",
    "energia": "Energía",
    "industria_manufactura": "Industria / Manufactura",
    "agro": "Agro",
    "logistica": "Logística",
    "telecomunicaciones": "Telecomunicaciones",
    "sin_clasificar": "Sin clasificar",
}

PERIOD_PRESETS: dict[str, int] = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
}

DEFAULT_ROLE_GROUP = "decision"
DEFAULT_PERIOD = "todo"
DEFAULT_SECTOR = "construccion"


@dataclass(frozen=True)
class FilterState:
    role_group: str  # "decision" | "todos" | <grupo>
    period: str  # "todo" | "1m" | "3m" | "6m" | "<año>"
    sector: str  # "construccion" | "todos" | <sector> | "sin_clasificar"


@dataclass(frozen=True)
class FilterOptions:
    role_options: list[tuple[str, str]]
    period_options: list[tuple[str, str]]
    sector_options: list[tuple[str, str]]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _get_year_options(events: list[Event]) -> list[str]:
    years = {event.first_seen.year for event in events}
    return [str(year) for year in sorted(years, reverse=True)]


def _count_by_role_group(events: list[Event]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        group = get_role_group(event.entities.get("role"))
        counts[group] = counts.get(group, 0) + 1
    return counts


def _count_by_sector(events: list[Event]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        sector = event.entities.get("sector") or "sin_clasificar"
        counts[sector] = counts.get(sector, 0) + 1
    return counts


def _find_index(options: list[str], value: str) -> int:
    try:
        return options.index(value)
    except ValueError:
        return 0


def build_options(events: list[Event]) -> FilterOptions:
    """Opciones de dropdown derivadas de los eventos, con conteo."""
    role_counts = _count_by_role_group(events)
    sector_counts = _count_by_sector(events)
    year_options = _get_year_options(events)

    decision_count = sum(role_counts.get(group, 0) for group in DECISION_ROLE_GROUPS)
    role_options = [
        ("decision", f"Toma de decisiones ({decision_count})"),
        ("todos", f"Todos los roles ({len(events)})"),
    ]
    for group_key in list(ROLE_GROUPS.keys()) + ["sin_clasificar"]:
        count = role_counts.get(group_key, 0)
        if count > 0:
            label = ROLE_GROUP_LABELS.get(group_key, group_key)
            role_options.append((group_key, f"{label} ({count})"))

    period_options = [
        ("todo", "Todo el período"),
        ("1m", "Último mes"),
        ("3m", "Últimos 3 meses"),
        ("6m", "Últimos 6 meses"),
    ]
    for year_str in year_options:
        year_count = sum(1 for event in events if str(event.first_seen.year) == year_str)
        period_options.append((year_str, f"Año {year_str} ({year_count})"))

    sector_options: list[tuple[str, str]] = [
        ("construccion", f"Construcción ({sector_counts.get('construccion', 0)})"),
        ("todos", f"Todas las industrias ({len(events)})"),
    ]
    for sector_key in sorted(SECTOR_CATALOG.keys()):
        if sector_key == "construccion":
            continue
        count = sector_counts.get(sector_key, 0)
        if count > 0:
            label = SECTOR_LABELS.get(sector_key, sector_key)
            sector_options.append((sector_key, f"{label} ({count})"))
    sin_count = sector_counts.get("sin_clasificar", 0)
    if sin_count > 0:
        sector_options.append(("sin_clasificar", f"Sin clasificar ({sin_count})"))

    return FilterOptions(
        role_options=role_options,
        period_options=period_options,
        sector_options=sector_options,
    )


def _reset_filters() -> None:
    import streamlit as st

    st.session_state["filter_role_group"] = DEFAULT_ROLE_GROUP
    st.session_state["filter_period"] = DEFAULT_PERIOD
    st.session_state["filter_sector"] = DEFAULT_SECTOR


def render_filter_bar(events: list[Event]) -> FilterState:
    """Renderiza la barra de filtros y devuelve el estado seleccionado."""
    import streamlit as st

    options = build_options(events)

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        role_keys = [key for key, _ in options.role_options]
        selected_role = st.selectbox(
            "Posición",
            options=role_keys,
            format_func=dict(options.role_options).get,
            index=_find_index(
                role_keys, st.session_state.get("filter_role_group", DEFAULT_ROLE_GROUP)
            ),
            key="filter_role_group",
        )

    with col2:
        period_keys = [key for key, _ in options.period_options]
        selected_period = st.selectbox(
            "Período",
            options=period_keys,
            format_func=dict(options.period_options).get,
            index=_find_index(
                period_keys, st.session_state.get("filter_period", DEFAULT_PERIOD)
            ),
            key="filter_period",
        )

    with col3:
        sector_keys = [key for key, _ in options.sector_options]
        selected_sector = st.selectbox(
            "Industria",
            options=sector_keys,
            format_func=dict(options.sector_options).get,
            index=_find_index(
                sector_keys, st.session_state.get("filter_sector", DEFAULT_SECTOR)
            ),
            key="filter_sector",
        )

    with col4:
        st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
        st.button(
            "Limpiar filtros",
            key="btn_clear_filters",
            use_container_width=True,
            on_click=_reset_filters,
        )

    return FilterState(
        role_group=selected_role,
        period=selected_period,
        sector=selected_sector,
    )


def apply_filters(
    events: list[Event],
    state: FilterState,
    *,
    now: datetime | None = None,
) -> list[Event]:
    """Aplica los filtros sobre la lista de eventos."""
    filtered = events

    if state.role_group == "decision":
        filtered = [
            event
            for event in filtered
            if get_role_group(event.entities.get("role")) in DECISION_ROLE_GROUPS
        ]
    elif state.role_group != "todos":
        filtered = [
            event
            for event in filtered
            if get_role_group(event.entities.get("role")) == state.role_group
        ]

    if state.period != "todo":
        if state.period in PERIOD_PRESETS:
            current = _as_utc(now or datetime.now(UTC))
            cutoff = current - timedelta(days=PERIOD_PRESETS[state.period])
            filtered = [
                event for event in filtered if _as_utc(event.first_seen) >= cutoff
            ]
        else:
            try:
                year = int(state.period)
            except ValueError:
                year = None
            if year is not None:
                filtered = [
                    event for event in filtered if event.first_seen.year == year
                ]

    if state.sector != "todos":
        if state.sector == "sin_clasificar":
            filtered = [event for event in filtered if not event.entities.get("sector")]
        else:
            filtered = [
                event
                for event in filtered
                if event.entities.get("sector") == state.sector
            ]

    return filtered
