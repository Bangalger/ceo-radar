# CEO Radar — Estado del trabajo

**Fecha:** 2026-07-27  
**Enfoque:** Latinoamérica  
**Objetivo:** detectar cambios ejecutivos recientes que puedan abrir una ventana comercial.

## Resumen

Se validó un flujo inicial de descubrimiento que combina varios tipos de fuentes:

- Noticias encontradas mediante búsquedas de Google News/SerpAPI.
- Hechos relevantes publicados directamente por la CNV.
- Boletín Oficial (Sección 2, Argentina) — spike 006.
- Revistas de nicho argentinas (Adlatina; Infocomercial bloqueado) — spike 007.

Las búsquedas se orientan a cambios de CEO, dirección ejecutiva y gerencia o
dirección comercial. Los resultados pueden limitarse por sector y se filtran al
año vigente para evitar oportunidades que probablemente ya hayan envejecido.

Cada fuente conserva su resultado independiente y, además, existe un proceso de
consolidación que normaliza fechas y campos básicos, identifica el origen y
ordena todas las oportunidades desde la más reciente.

El flujo es reproducible mediante scripts locales. Desde el dashboard Streamlit
se puede disparar la búsqueda en todas las fuentes y la consolidación con un
click; también sigue siendo posible correr cada script por separado. La consulta
a SerpAPI requiere `SERPAPI_API_KEY` en `.env`. El feedback se persiste en
MongoDB Atlas (`MONGODB_URI`). La consulta a CNV usa información pública y no
necesita credenciales.

## Estado actual

- [x] Consulta de noticias generales mediante SerpAPI.
- [x] Búsqueda enfocada en constructoras, desarrolladoras e inmobiliarias.
- [x] Curación heurística por sector, rol y año vigente.
- [x] Consulta directa de hechos relevantes de la CNV.
- [x] Consolidación de resultados de CNV y Google News en un único JSON.
- [x] Separación entre resultados generados, scripts y secretos locales.
- [x] Spike Boletín Oficial (006): búsqueda en Sección 2 por texto libre y empresas argentinas del catálogo.
- [x] Spike revistas de nicho (007): Marketers by Adlatina + intento Infocomercial.
- [x] Curación de nombramientos desde revistas de nicho (`curadas.json`).
- [x] Orquestación de fuentes desde el dashboard (`refresh_service.py` + botón en `app.py`).
- [x] Persistencia de feedback en MongoDB Atlas (`ceo_radar.feedback`).

## Spikes Argentina (2026-07-25)

### 006 — Boletín Oficial

- **Hipótesis validada:** sí, es posible detectar designaciones de autoridades vía el buscador avanzado de la Sección 2.
- **Endpoint interno:** `POST /busquedaAvanzada/realizarBusqueda/segunda` (requests + BeautifulSoup; sin headless browser).
- **Última corrida:** 222 candidatos, 40 analizados en detalle, 37 relevantes (precisión ~92% en la muestra).
- **Resultado:** `.planning/spikes/006-boletin-oficial/results/latest.json`

### 007 — Revistas de nicho

- **Adlatina:** 60 nombramientos scrapeados (5 páginas), 20 curados para 2026.
- **Infocomercial:** HTTP 403 — el sitio bloquea requests automatizados.
- **Resultados:** `.planning/spikes/007-revistas-nicho/results/`

## Limitaciones conocidas

- La clasificación sectorial todavía es heurística y puede producir falsos
  positivos o dejar afuera empresas relevantes.
- Varias noticias pueden describir el mismo cambio ejecutivo.
- Las noticias aún no extraen de forma estructurada empresa, persona, rol y tipo
  de cambio.
- La CNV cubre entidades reguladas y su página pública no ofrece una API JSON
  documentada; el extractor debe revisarse si cambia el HTML.
- Un rechazo aislado no debería convertirse automáticamente en una regla
  general: las reglas aprendidas necesitan confirmación del usuario.
- El Boletín Oficial no tiene API documentada; usa endpoint interno que puede
  cambiar. Alto volumen de avisos comerciales no ejecutivos (convocatorias,
  balances). El lenguaje societario usa Presidente/Directorio/Gerente General,
  no CEO.
- Infocomercial bloquea scraping automatizado (HTTP 403). Adlatina funciona pero
  cubre principalmente marketing/comunicaciones, no construcción.
- La extracción de roles en titulares de marketing sigue siendo débil para cargos
  como CMO, head de marketing o gerenta general (muchas detecciones con confianza baja).
- Los eventos consolidados siguen en archivos locales (`.planning/results/`); solo
  el feedback persiste en MongoDB. En Streamlit Cloud hay que correr el refresh al
  menos una vez por sesión de contenedor para tener datos de eventos.

## Próximos pasos

### Interfaz y feedback

- [x] Crear una interfaz para visualizar las oportunidades consolidadas.
- [ ] Permitir filtrar por fecha, fuente, mercado, empresa, rol y estado.
- [x] Permitir votar cada resultado como:
  - buen candidato;
  - revisar más tarde;
  - no relevante.
- [x] Permitir indicar el motivo del rechazo: sector incorrecto, cargo no
  relevante, noticia vieja, empresa fuera del mercado objetivo, duplicado,
  cambio sin intención comercial u otro.
- [x] Generar un identificador estable para cada resultado y persistir las
  decisiones en MongoDB (`ceo_radar.feedback`).
- [x] Mantener en el feedback el estado, motivo, comentario, fecha y regla
  sugerida, sin modificar el resultado original.
- [x] Ocultar resultados rechazados en la vista normal, conservándolos para
  auditoría.
- [ ] Proponer reglas de exclusión a partir del feedback y aplicarlas sólo
  después de confirmarlas; por ejemplo, omitir una categoría, empresa, fuente o
  patrón que el usuario considere inválido.
- [ ] Incorporar las reglas confirmadas al proceso de curación para que futuras
  ejecuciones reduzcan resultados similares.

### Calidad de datos

- [x] Extraer `{empresa, persona, rol, tipo_cambio}` de cada oportunidad (heurístico).
- [x] Agrupar noticias que representen el mismo evento.
- [x] Enriquecer entidades con país, sector y tamaño (parcial, vía catálogos).
- [ ] Crear un score comercial explicable basado en recencia, cargo, sector,
  fuente y feedback histórico.
- [ ] Ampliar y validar cobertura de fuentes oficiales de otros países.
- [x] Integrar Boletín Oficial y revistas de nicho al pipeline de consolidación.
- [ ] Resolver acceso a Infocomercial (proxy, API alternativa o ingesta manual).
- [ ] Mejorar extracción de entidades para titulares de marketing/gerencia general.

### Operación

- [x] Automatizar consultas, curación y consolidación desde el dashboard (manual con un click).
- [ ] Programar ejecución periódica (cron/scheduler).
- [x] Registrar cuándo se vio cada resultado por primera y última vez (`first_seen` / `last_seen`).
- [ ] Incorporar alertas para oportunidades nuevas con score alto.
- [x] Diseñar el producto y crear el scaffold de la aplicación.
