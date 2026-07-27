import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[0]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "src"))

from ceo_radar.models import Event, Feedback  # noqa: E402
from ceo_radar.services import events_service, feedback_service, refresh_service  # noqa: E402
from ceo_radar.services.refresh_service import RefreshStepResult  # noqa: E402

ROLE_LABELS = {
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

COUNTRY_LABELS = {
    "argentina": "Argentina",
    "brasil": "Brasil",
    "chile": "Chile",
}


def format_role_label(role: str | None) -> str:
    if not role:
        return "Cambio ejecutivo"
    return ROLE_LABELS.get(role.lower(), f"Nuevo {role}")


def format_country_label(country: str | None) -> str:
    if not country:
        return "país desconocido"
    return COUNTRY_LABELS.get(country.lower(), country.title())


def build_event_title(event: Event) -> str:
    entities = event.entities
    company = entities.get("company") or "Empresa no identificada"
    role_label = format_role_label(entities.get("role"))
    country_label = format_country_label(entities.get("country"))
    person = entities.get("person")

    if person:
        return f"{company} — {person} — {role_label} — {country_label}"
    return f"{company} — {role_label} — {country_label}"


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


def render_event_details(event: Event) -> None:
    st.caption(
        f"{len(event.articles)} noticia(s) · "
        f"Primera vez visto: {event.first_seen.strftime('%Y-%m-%d')} · "
        f"Última vez visto: {event.last_seen.strftime('%Y-%m-%d')}"
    )

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


def render_refresh_summary(results: list[RefreshStepResult]) -> None:
    ok_count = sum(1 for result in results if result.ok)
    fail_count = len(results) - ok_count

    if fail_count == 0:
        st.success(f"Actualización completa: {ok_count}/{len(results)} pasos exitosos.")
    else:
        st.warning(
            f"Actualización parcial: {ok_count}/{len(results)} pasos exitosos, "
            f"{fail_count} con error."
        )

    for result in results:
        icon = "✅" if result.ok else "⚠️"
        with st.expander(f"{icon} {result.name}", expanded=not result.ok):
            st.text(result.message or "Sin detalle.")


def render_feedback_history(event: Event) -> None:
    history = feedback_service.feedback_history_for_event(event.id)
    if not history:
        st.caption("Sin feedback registrado.")
        return

    st.write("**Historial de feedback:**")
    for entry in history:
        st.markdown(f"- {format_feedback_summary(entry)}")


st.set_page_config(layout="wide", page_title="CEO Radar Dashboard")


@st.cache_data
def load_events_cached(_events_mtime: float, _feedback_version: tuple[int, str]):
    return events_service.load_events()


events_service.ensure_events_file()

st.sidebar.header("Datos")
st.sidebar.caption(
    "La búsqueda completa tarda ~1-2 minutos y consume cuota de SerpAPI."
)

if st.sidebar.button("Buscar y actualizar todas las fuentes"):
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
                icon = "✅" if result.ok else "⚠️"
                status_lines[name] = f"{icon} {name}"
            progress_placeholder.markdown("\n\n".join(status_lines.values()))

        refresh_results = refresh_service.run_full_refresh(on_progress=on_refresh_progress)
        status.update(
            label="Actualización finalizada",
            state="complete",
        )

    st.session_state["last_refresh_results"] = refresh_results
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("Remezclar datos existentes (sin buscar)"):
    with st.spinner("Remezclando datos existentes..."):
        events_service.regenerate_events()
    st.cache_data.clear()
    st.rerun()

events, generated_at, source_counts, result_count = load_events_cached(
    events_service.get_events_file_mtime(),
    feedback_service.get_feedback_version(),
)

latest_by_event = feedback_service.latest_status_by_event()

st.title("CEO Radar: Oportunidades Ejecutivas")

if "last_refresh_results" in st.session_state:
    render_refresh_summary(st.session_state["last_refresh_results"])

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

    if visible_events:
        for event in visible_events:
            st.subheader(build_event_title(event))
            render_event_details(event)
            render_feedback_form(event, latest_by_event.get(event.id))
            st.markdown("---")
    else:
        st.info("No hay eventos visibles en el radar (todos fueron marcados como no relevantes).")

elif view == "Auditoría":
    st.header("Auditoría de eventos")
    st.caption("Incluye rechazados y el historial completo de feedback por evento.")

    if events:
        for event in events:
            latest = latest_by_event.get(event.id)
            title = build_event_title(event)
            if latest and latest.status == "no_relevante":
                st.subheader(f"[Rechazado] {title}")
            else:
                st.subheader(title)

            render_event_details(event)
            render_feedback_history(event)
            render_feedback_form(event, latest)
            st.markdown("---")
    else:
        st.info("No hay eventos disponibles para auditar.")
