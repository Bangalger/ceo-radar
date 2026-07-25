import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys

# Add src/ to the Python path to allow importing ceo_radar
ROOT_DIR = Path(__file__).resolve().parents[0]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "src"))

from ceo_radar.models import Event, Article # Import necessary models
from ceo_radar.pipeline import run_pipeline # To regenerate data if needed

# Define ROOT for consistent pathing
OUTPUT_FILE = ROOT_DIR / ".planning" / "results" / "oportunidades_unificadas.json"

st.set_page_config(layout="wide", page_title="CEO Radar Dashboard")

@st.cache_data
def load_data():
    if not OUTPUT_FILE.exists():
        st.warning("No se encontraron datos unificados. Ejecutando el pipeline...")
        run_pipeline()
    
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Deserialize events using Pydantic
    # Ensure datetime objects are handled correctly by Pydantic by parsing them after loading raw data
    events = [Event(**item) for item in data["results"]]
    return events, data["generated_at"], data["source_counts"], data["result_count"]

# --- Main Dashboard --- 
st.title("CEO Radar: Oportunidades Ejecutivas")

events, generated_at, source_counts, result_count = load_data()

st.write(f"Última actualización de datos: {generated_at}")
st.write(f"Total de eventos detectados: {result_count}")
st.write(f"Artículos procesados (CNV): {source_counts.get("cnv", 0)}")
st.write(f"Artículos procesados (Google News): {source_counts.get("google_news", 0)}")

st.sidebar.header("Filtros")
# Placeholder for filters
# Ejemplo: st.sidebar.multiselect("País", options=["Argentina", "Chile"], default=["Argentina"])

st.header("Eventos Recientes")

if events:
    for event in events:
        st.subheader(f"Evento: {event.id[:8]}...")
        st.write(f"**Entidades:** {event.entities}")
        st.write(f"**Score (placeholder):** {event.score}")
        st.write(f"**Primera vez visto:** {event.first_seen.strftime('%Y-%m-%d')}")
        st.write(f"**Última vez visto:** {event.last_seen.strftime('%Y-%m-%d')}")
        
        with st.expander("Ver artículos relacionados"):
            for article in event.articles:
                st.markdown(f"- [{article.title}]({article.url}) (Fuente: {article.source})")
                st.caption(f"Publicado: {article.published_at.strftime('%Y-%m-%d')}")
                if article.description: st.text(article.description)
                st.json(article.extracted_data)

        st.markdown("--- Jardín de feedback --- (próximamente)")

else:
    st.info("No hay eventos disponibles para mostrar. Asegúrate de que el pipeline de datos se haya ejecutado correctamente.")


# Placeholder para el panel de reglas
st.sidebar.header("Gestión de Reglas (próximamente)")
# Ejemplo: st.sidebar.button("Sugerir nueva regla")
