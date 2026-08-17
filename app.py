import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[0]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "src"))

from ceo_radar.filters import apply_filters, render_filter_bar  # noqa: E402
from ceo_radar.formatters import (  # noqa: E402
    format_person_display,
    format_role_label,
    format_timing,
)
from ceo_radar.models import Event, Feedback  # noqa: E402
from ceo_radar.services import events_service, feedback_service  # noqa: E402
from ceo_radar.services import linkedin_service  # noqa: E402

COUNTRY_LABELS = {
    "argentina": "Argentina",
    "brasil": "Brasil",
    "chile": "Chile",
}


def format_country_label(country: str | None) -> str:
    if not country:
        return "país desconocido"
    return COUNTRY_LABELS.get(country.lower(), country.title())


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


def render_event_identity(event: Event) -> None:
    entities = event.entities
    person = format_person_display(entities)
    role = format_role_label(entities.get("role"))
    company = entities.get("company") or "Empresa no identificada"
    country = format_country_label(entities.get("country"))
    timing = format_timing(event)

    st.subheader(person)
    st.markdown(f"**{role}** · `{company}` · {country}")
    st.caption(f"Anuncio: {timing}")
    if event.last_seen.date() != event.first_seen.date():
        st.caption(
            f"Detectado entre {event.first_seen.strftime('%Y-%m-%d')} "
            f"y {event.last_seen.strftime('%Y-%m-%d')}"
        )


def render_event_details(event: Event) -> None:
    st.caption(f"{len(event.articles)} noticia(s)")

    with st.expander("Ver artículos y detalle de extracción"):
        st.write("**Entidades consolidadas:**")
        st.json(event.entities)
        st.write("**Artículos relacionados:**")
        for article in event.articles:
            st.markdown(f"- [{article.title}]({article.url}) (Fuente: {article.source})")
            st.caption(f"Publicado: {article.published_at.strftime('%Y-%m-%d')}")
            if article.description:
                st.text(article.description)
            st.json(article.extracted_data)


def render_linkedin_search(event: Event) -> None:
    person = (event.entities.get("person") or "").strip()
    company = event.entities.get("company")
    role = event.entities.get("role")
    country = event.entities.get("country")
    state_key = f"linkedin_result_{event.id}"

    st.write("**Perfil de LinkedIn**")
    if not person:
        st.caption("Sin nombre de persona extraído; no se puede buscar el perfil.")
        return

    search_col, refresh_col = st.columns(2)
    with search_col:
        search_clicked = st.button(
            "Buscar LinkedIn",
            key=f"li_search_{event.id}",
            use_container_width=True,
        )
    with refresh_col:
        refresh_clicked = st.button(
            "Volver a buscar",
            key=f"li_refresh_{event.id}",
            use_container_width=True,
        )

    if search_clicked or refresh_clicked:
        with st.spinner("Buscando perfil en LinkedIn..."):
            st.session_state[state_key] = linkedin_service.lookup(
                person,
                company,
                role,
                country,
                force_refresh=refresh_clicked,
            )

    result = st.session_state.get(state_key)
    if not result:
        st.caption("La búsqueda usa SerpAPI solo al hacer click.")
        return

    if result.get("error"):
        st.warning(result["error"])
        return

    searched_at = result.get("searched_at")
    cached_label = " (caché)" if result.get("cached") else ""
    if searched_at:
        st.caption(f"Consulta: {searched_at}{cached_label}")

    profiles = result.get("results") or []
    if not profiles:
        st.info("No se encontraron perfiles de LinkedIn para esta persona.")
        return

    for profile in profiles[:3]:
        title = profile.get("title") or profile.get("link")
        link = profile.get("link")
        snippet = profile.get("snippet") or ""
        st.markdown(f"- [{title}]({link})")
        if snippet:
            st.caption(snippet)


def render_feedback_form(event: Event, latest: Feedback | None) -> None:
    st.write("**Feedback**")
    if latest:
        st.info(f"Estado vigente: {format_feedback_summary(latest)}")

    with st.form(key=f"feedback_form_{event.id}"):
        status = st.selectbox(
            "Estado",
            options=list(feedback_service.STATUSES),
            format_func=lambda s: feedback_service.STATUS_LABELS[s],
            key=f"status_{event.id}",
        )

        reason = None
        if status in ("no_relevante", "revisar"):
            reason_options = feedback_service.REASONS_BY_STATUS[status]
            reason = st.selectbox(
                "Motivo",
                options=reason_options,
                format_func=lambda r: feedback_service.REASON_LABELS.get(r, r),
                key=f"reason_{event.id}",
            )

        comment = st.text_area("Comentario (opcional)", key=f"comment_{event.id}")

        submitted = st.form_submit_button("Guardar feedback")
        if submitted:
            try:
                feedback_service.submit_feedback(
                    event_id=event.id,
                    status=status,
                    reason=reason,
                    comment=comment,
                )
                st.success("Feedback guardado.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def render_feedback_history(event: Event) -> None:
    history = feedback_service.feedback_history_for_event(event.id)
    if not history:
        st.caption("Sin feedback registrado.")
        return

    st.write("**Historial de feedback:**")
    for entry in history:
        st.markdown(f"- {format_feedback_summary(entry)}")


def render_event_card(event: Event, latest: Feedback | None, *, show_history: bool = False) -> None:
    render_event_identity(event)
    render_event_details(event)
    render_linkedin_search(event)
    if show_history:
        render_feedback_history(event)
    render_feedback_form(event, latest)
    st.markdown("---")


st.set_page_config(layout="wide", page_title="CEO Radar Dashboard")


@st.cache_data
def load_events_cached(_events_mtime: float, _feedback_mtime: float):
    return events_service.load_events()


events_service.ensure_events_file()

st.sidebar.caption(
    "La actualización de fuentes consume cuota de SerpAPI "
    "(búsquedas del año actual y del anterior)."
)

if st.sidebar.button("Regenerar datos (correr pipeline)"):
    with st.spinner("Corriendo pipeline..."):
        events_service.regenerate_events()
    st.cache_data.clear()
    st.rerun()

events, generated_at, source_counts, result_count = load_events_cached(
    events_service.get_events_file_mtime(),
    feedback_service.get_feedback_file_mtime(),
)

latest_by_event = feedback_service.latest_status_by_event()

st.title("CEO Radar: Oportunidades Ejecutivas")

st.write(f"Última actualización de datos: {generated_at}")
st.write(f"Total de eventos detectados: {result_count}")
st.write(f"Artículos procesados (CNV): {source_counts.get('cnv', 0)}")
st.write(f"Artículos procesados (Google News): {source_counts.get('google_news', 0)}")
st.write(f"Avisos procesados (Boletín Oficial): {source_counts.get('boletin_oficial', 0)}")
st.write(f"Notas procesadas (Revistas de nicho): {source_counts.get('revistas_nicho', 0)}")

view = st.sidebar.radio("Vista", ["Radar", "Auditoría"], index=0)

if view == "Radar":
    st.header("Eventos Recientes")
    visible_events = [
        event
        for event in events
        if not feedback_service.is_rejected(event.id, latest_by_event)
    ]

    filter_state = render_filter_bar(visible_events)
    filtered_events = apply_filters(visible_events, filter_state)

    st.caption(f"Mostrando {len(filtered_events)} de {len(visible_events)} eventos")

    if filtered_events:
        for event in filtered_events:
            render_event_card(event, latest_by_event.get(event.id))
    else:
        st.info("No hay eventos que coincidan con los filtros seleccionados.")

elif view == "Auditoría":
    st.header("Auditoría de eventos")
    st.caption("Incluye rechazados y el historial completo de feedback por evento.")

    filter_state = render_filter_bar(events)
    filtered_events = apply_filters(events, filter_state)

    st.caption(f"Mostrando {len(filtered_events)} de {len(events)} eventos")

    if filtered_events:
        for event in filtered_events:
            latest = latest_by_event.get(event.id)
            if latest and latest.status == "no_relevante":
                st.markdown("**[Rechazado]**")
            render_event_card(event, latest, show_history=True)
    else:
        st.info("No hay eventos que coincidan con los filtros seleccionados.")
