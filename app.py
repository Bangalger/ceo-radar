import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[0]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "src"))

from ceo_radar.models import Event, Feedback  # noqa: E402
from ceo_radar.services import events_service, feedback_service, refresh_service  # noqa: E402
from ceo_radar.services.refresh_service import RefreshStepResult  # noqa: E402
from ceo_radar.ui import components as ui  # noqa: E402
from ceo_radar.ui.theme import inject_theme  # noqa: E402

NAV_ITEMS = (("Radar", "radar"), ("Auditoría", "analytics"))


def _init_session_state() -> None:
    st.session_state.setdefault("view", "Radar")
    st.session_state.setdefault("expanded_event_id", None)


def _set_view(view: str) -> None:
    st.session_state["view"] = view
    st.session_state["expanded_event_id"] = None


def _resolve_expanded_id(events: list[Event]) -> str | None:
    """Resuelve qué evento va expandido; None si no hay ninguno o el id ya no existe."""
    current = st.session_state.get("expanded_event_id")

    if current is not None and not any(event.id == current for event in events):
        return None

    return current


def _card_key(prefix: str, event: Event, latest: Feedback | None) -> str:
    """Clave de contenedor; el infijo `arch` activa el estilo de archivado."""
    archived = latest is not None and latest.status == "no_relevante"
    infix = "arch_" if archived else ""
    return f"{prefix}_{infix}{event.id}"


def render_sidebar() -> None:
    ui.sidebar_brand()

    current_view = st.session_state["view"]

    for view_name, icon_name in NAV_ITEMS:
        state = "navactive" if view_name == current_view else "navinactive"
        with st.container(key=f"{state}_{view_name}"):
            if st.button(
                view_name,
                key=f"nav_{view_name}",
                icon=f":material/{icon_name}:",
                width="stretch",
            ):
                _set_view(view_name)
                st.rerun()

    st.markdown("---")

    st.caption("La búsqueda completa tarda ~1-2 minutos y consume cuota de SerpAPI.")

    if st.button(
        "Actualizar Datos",
        key="btn_refresh",
        icon=":material/refresh:",
        type="primary",
        width="stretch",
    ):
        run_full_refresh()

    with st.container(key="btn_regenerate"):
        if st.button(
            "Remezclar datos existentes",
            key="btn_regenerate_click",
            icon=":material/autorenew:",
            width="stretch",
        ):
            with st.spinner("Remezclando datos existentes..."):
                events_service.regenerate_events()
            st.cache_data.clear()
            st.rerun()


def run_full_refresh() -> None:
    status_lines: dict[str, str] = {}

    with st.status("Buscando y actualizando fuentes...", expanded=True) as status:
        progress_placeholder = st.empty()

        def on_refresh_progress(
            name: str,
            result: RefreshStepResult | None,
            is_pipeline: bool,
        ) -> None:
            del is_pipeline
            if result is None:
                status_lines[name] = f"⏳ {name}..."
            else:
                step_icon = "✅" if result.ok else "⚠️"
                status_lines[name] = f"{step_icon} {name}"
            progress_placeholder.markdown("\n\n".join(status_lines.values()))

        refresh_results = refresh_service.run_full_refresh(on_progress=on_refresh_progress)
        status.update(label="Actualización finalizada", state="complete")

    st.session_state["last_refresh_results"] = refresh_results
    st.cache_data.clear()
    st.rerun()


def render_feedback_form(event: Event, latest: Feedback | None) -> None:
    if latest:
        ui.render_html(ui.feedback_banner_html(latest))

    with st.form(key=f"feedback_form_{event.id}"):
        status_col, reason_col = st.columns(2)

        with status_col:
            status = st.selectbox(
                "Actualizar Estado",
                options=list(feedback_service.STATUSES),
                format_func=lambda s: feedback_service.STATUS_LABELS[s],
                key=f"status_{event.id}",
            )

        reason = None
        if status in ("no_relevante", "revisar"):
            with reason_col:
                reason = st.selectbox(
                    "Motivo",
                    options=feedback_service.REASONS_BY_STATUS[status],
                    format_func=lambda r: feedback_service.REASON_LABELS.get(r, r),
                    key=f"reason_{event.id}",
                )

        comment = st.text_area("Comentario (opcional)", key=f"comment_{event.id}")

        if st.form_submit_button("Guardar Cambios", width="stretch"):
            try:
                feedback_service.submit_feedback(
                    event_id=event.id,
                    status=status,
                    reason=reason,
                    comment=comment,
                )
                st.session_state["expanded_event_id"] = event.id
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def render_expanded_event(
    event: Event,
    latest: Feedback | None,
    *,
    show_history: bool = False,
) -> None:
    with st.container(key=_card_key("eventcard", event, latest)):
        ui.render_html(ui.event_header_html(event, latest))

        left_col, right_col = st.columns([2.2, 1], gap="large")

        with left_col:
            ui.render_html(ui.news_block(event))
            ui.section_label("Acción Ejecutiva")

            with st.container(key=f"action_{event.id}"):
                if show_history:
                    history = feedback_service.feedback_history_for_event(event.id)
                    ui.render_html(ui.feedback_history_html(history))

                render_feedback_form(event, latest)

        with right_col:
            ui.render_html(ui.extraction_panel(event.entities))

        with st.container(key=f"collapsebtn_{event.id}"):
            if st.button(
                "Contraer Detalles",
                key=f"collapse_{event.id}",
                icon=":material/expand_less:",
                width="stretch",
            ):
                st.session_state["expanded_event_id"] = None
                st.rerun()


def render_collapsed_event(event: Event, latest: Feedback | None) -> None:
    with st.container(key=_card_key("collapsed", event, latest)):
        ui.render_html(ui.collapsed_card_content(event, latest))

        if st.button(
            "Expandir Detalles",
            key=f"expand_{event.id}",
            icon=":material/expand_more:",
            width="stretch",
        ):
            st.session_state["expanded_event_id"] = event.id
            st.rerun()


def render_collapsed_grid(
    events: list[Event],
    latest_by_event: dict[str, Feedback],
) -> None:
    with st.container(horizontal=True, gap="medium", key="collapsedgrid"):
        for event in events:
            render_collapsed_event(event, latest_by_event.get(event.id))


def render_event_feed(
    events: list[Event],
    latest_by_event: dict[str, Feedback],
    *,
    show_history: bool = False,
) -> None:
    expanded_id = _resolve_expanded_id(events)
    expanded_event = next((event for event in events if event.id == expanded_id), None)

    if expanded_event:
        render_expanded_event(
            expanded_event,
            latest_by_event.get(expanded_event.id),
            show_history=show_history,
        )

    collapsed_events = [event for event in events if event.id != expanded_id]
    if collapsed_events:
        render_collapsed_grid(collapsed_events, latest_by_event)


def render_radar(events: list[Event], latest_by_event: dict[str, Feedback]) -> None:
    ui.section_title("Eventos Recientes")

    visible_events = [
        event
        for event in events
        if not feedback_service.is_rejected(event.id, latest_by_event)
    ]

    if not visible_events:
        ui.empty_state(
            "No hay eventos visibles en el radar "
            "(todos fueron marcados como no relevantes)."
        )
        return

    render_event_feed(visible_events, latest_by_event)


def render_auditoria(events: list[Event], latest_by_event: dict[str, Feedback]) -> None:
    ui.section_title("Auditoría de eventos", icon_name="analytics")

    if not events:
        ui.empty_state("No hay eventos disponibles para auditar.")
        return

    render_event_feed(events, latest_by_event, show_history=True)


def render_refresh_summary(results: list[RefreshStepResult]) -> None:
    ok_count = sum(1 for result in results if result.ok)
    ui.render_html(ui.refresh_summary_html(ok_count, len(results), len(results) - ok_count))

    for result in results:
        step_icon = "✅" if result.ok else "⚠️"
        with st.expander(f"{step_icon} {result.name}", expanded=not result.ok):
            st.text(result.message or "Sin detalle.")


@st.cache_data
def load_events_cached(_events_mtime: float, _feedback_version: tuple[int, str]):
    return events_service.load_events()


st.set_page_config(
    layout="wide",
    page_title="CEO Radar | Executive Intelligence",
    page_icon="📡",
    initial_sidebar_state="expanded",
)

_init_session_state()
inject_theme()
events_service.ensure_events_file()

with st.sidebar:
    render_sidebar()

events, generated_at, source_counts, result_count = load_events_cached(
    events_service.get_events_file_mtime(),
    feedback_service.get_feedback_version(),
)
latest_by_event = feedback_service.latest_status_by_event()

ui.page_header()

if "last_refresh_results" in st.session_state:
    render_refresh_summary(st.session_state["last_refresh_results"])

ui.meta_row(generated_at)
ui.stats_grid(result_count, source_counts)

if st.session_state["view"] == "Radar":
    render_radar(events, latest_by_event)
else:
    render_auditoria(events, latest_by_event)

ui.footer(len(source_counts))
