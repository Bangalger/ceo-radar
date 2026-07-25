import json
import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[0]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "src"))

from ceo_radar.models import Event  # noqa: E402
from ceo_radar.pipeline import run_pipeline  # noqa: E402

OUTPUT_FILE = ROOT_DIR / ".planning" / "results" / "oportunidades_unificadas.json"

ROLE_LABELS = {
    "ceo": "Nuevo CEO",
    "director ejecutivo": "Nuevo director ejecutivo",
    "diretor executivo": "Nuevo director ejecutivo",
    "gerente comercial": "Nuevo gerente comercial",
    "director comercial": "Nuevo director comercial",
    "diretor comercial": "Nuevo director comercial",
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


st.set_page_config(layout="wide", page_title="CEO Radar Dashboard")


@st.cache_data
def load_data():
    if not OUTPUT_FILE.exists():
        st.warning("No se encontraron datos unificados. Ejecutando el pipeline...")
        run_pipeline()

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = [Event(**item) for item in data["results"]]
    return events, data["generated_at"], data["source_counts"], data["result_count"]


st.title("CEO Radar: Oportunidades Ejecutivas")

events, generated_at, source_counts, result_count = load_data()

st.write(f"Última actualización de datos: {generated_at}")
st.write(f"Total de eventos detectados: {result_count}")
st.write(f"Artículos procesados (CNV): {source_counts.get('cnv', 0)}")
st.write(f"Artículos procesados (Google News): {source_counts.get('google_news', 0)}")

st.sidebar.header("Filtros")
st.sidebar.caption("Filtros avanzados próximamente.")

st.header("Eventos Recientes")

if events:
    for event in events:
        st.subheader(build_event_title(event))
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

        st.markdown("---")
else:
    st.info(
        "No hay eventos disponibles para mostrar. "
        "Asegúrate de que el pipeline de datos se haya ejecutado correctamente."
    )

st.sidebar.header("Gestión de Reglas")
st.sidebar.caption("Panel de reglas próximamente.")
