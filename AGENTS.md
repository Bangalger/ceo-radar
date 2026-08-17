# CEO Radar

Spanish-language business-intelligence tool (Latin America) that detects recent executive
changes to surface commercial opportunities. Single Streamlit app backed by local JSON files
(no database). See `steps.md` for product context.

## Cursor Cloud specific instructions

### Services

- **Streamlit dashboard** (`app.py`) — the only long-running service. Run with
  `python3 -m streamlit run app.py --server.port 8501` (the `streamlit` console script is
  installed under `~/.local/bin`, which is not on `PATH`; invoking `python3 -m streamlit`
  avoids that). Serves on port 8501.
- **Consolidation pipeline** (`scripts/run_pipeline.py`) — a batch step, not a server. It reads
  4 source JSON files and writes `.planning/results/oportunidades_unificadas.json`. The app runs
  it automatically on first load via `events_service.ensure_events_file()`.

### Startup gotcha: the app crashes on first load without all 4 pipeline inputs

`src/ceo_radar/pipeline.py` reads 4 input files unconditionally. Two are committed
(`006-boletin-oficial/results/latest.json`, `007-revistas-nicho/results/curadas.json`), but two
live in gitignored `results/` dirs and must be generated first, or the app raises
`FileNotFoundError` on startup:

- `.planning/spikes/005-cnv-hechos-relevantes/results/cnv_cambios_ejecutivos.json` — generate with
  `python3 .planning/spikes/005-cnv-hechos-relevantes/cnv_probe.py` (public CNV site, no key; may
  legitimately return 0 results for the current year).
- `.planning/spikes/002b-serpapi-news/results/constructoras_curadas.json` — requires
  `SERPAPI_API_KEY` (set in `.env`, copied from `.env.example`) plus outbound internet. Without the
  key, write a stub `{"results": []}` to this path so the pipeline can run on the other 3 sources.

The committed Boletín Oficial + Revistas de nicho sources alone yield ~57 real events, so the app
is fully functional for development without the SerpAPI key.

### Data / persistence

- Feedback is written to `data/feedback.json` (gitignored). Events are cached by Streamlit;
  click "Regenerar datos (correr pipeline)" in the sidebar to rebuild after regenerating inputs.

### Lint / test / build

- No linter, test suite, or build step is configured (no `pyproject.toml`, `ruff`, `pytest`, etc.).
  Use `python3 -m compileall -q app.py src scripts` as a basic syntax check. There is no build step
  (pure Python + Streamlit).
