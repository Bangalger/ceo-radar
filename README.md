# CEO Radar

Detecta cambios ejecutivos recientes (CEO, dirección, gerencia comercial) en
empresas de Latinoamérica que puedan abrir una ventana comercial.

## Qué hace

1. **Recolecta** datos de 4 fuentes independientes (scripts en `.planning/spikes/`):
   - Google News / SerpAPI (noticias generales y de constructoras/inmobiliarias).
   - CNV (hechos relevantes publicados por el regulador argentino).
   - Boletín Oficial Argentina (Sección 2, designaciones de autoridades).
   - Revistas de nicho (Adlatina).
2. **Consolida** todo en un único pipeline (`src/ceo_radar/pipeline.py`) que:
   - Extrae entidades (empresa, persona, rol, país, sector) de cada artículo.
   - Agrupa artículos que refieren al mismo evento (empresa + rol, ventana de 45 días).
   - Genera `.planning/results/oportunidades_unificadas.json`.
3. **Muestra** los resultados en un dashboard Streamlit (`app.py`) donde se puede
   marcar cada evento como buen candidato / revisar / no relevante, con motivo y
   comentario. El feedback se guarda en `data/feedback.json`.
   Desde el sidebar se puede **buscar y actualizar todas las fuentes** con un
   click (dispara los scripts de cada fuente y luego consolida), o **remezclar
   datos existentes** sin volver a consultar fuentes externas.

## Estructura

```
app.py                  Dashboard Streamlit
scripts/run_pipeline.py Ejecuta el pipeline de consolidación
src/ceo_radar/
  models.py             Modelos Pydantic (Article, Event, Feedback, Run)
  pipeline.py           Lee las fuentes, extrae entidades y arma eventos
  extraction.py         Heurísticas de extracción de empresa/persona/rol/país
  catalogs.py           Catálogos de empresas, sectores y países conocidos
  utils.py              Parsers de fecha por fuente
  services/             Carga de eventos, refresh de fuentes y feedback
.planning/spikes/       Scripts exploratorios por fuente (uno por spike)
.planning/results/      Salida consolidada del pipeline (generada, no versionada)
tests/                  Tests de extracción
```

## Cómo correrlo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar SERPAPI_API_KEY si se van a correr los spikes de noticias
```

Generar los datos consolidados:

```bash
python scripts/run_pipeline.py
```

Levantar el dashboard:

```bash
streamlit run app.py
```

En el sidebar del dashboard:
- **Buscar y actualizar todas las fuentes**: consulta SerpAPI, CNV, Boletín Oficial,
  Adlatina/Infocomercial, cura los resultados y consolida (~1-2 min, usa cuota SerpAPI).
- **Remezclar datos existentes (sin buscar)**: solo vuelve a correr el pipeline sobre
  los JSON ya descargados.

Correr los tests:

```bash
pytest
```

## Estado actual

- [x] Extracción y consolidación de 4 fuentes en un único JSON de eventos.
- [x] Dashboard con feedback por evento (estado, motivo, comentario) y vista de auditoría.
- [x] Curación heurística por sector, rol, país y año vigente.
- [x] Actualización de fuentes desde el dashboard (un click; no programada).
- [ ] Reglas automáticas a partir del feedback acumulado.
- [ ] Score comercial explicable por evento.
- [ ] Cobertura de fuentes oficiales fuera de Argentina.
- [ ] Ejecución periódica automática (cron/scheduler).

Más detalle de avances, limitaciones y próximos pasos en [`steps.md`](steps.md).
