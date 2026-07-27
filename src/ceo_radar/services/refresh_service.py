"""Orquestación de búsqueda en fuentes y consolidación del pipeline."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ceo_radar.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[3]

REFRESH_SCRIPTS: tuple[tuple[str, Path], ...] = (
    (
        "Google News (SerpAPI)",
        ROOT / ".planning/spikes/002b-serpapi-news/constructoras_probe.py",
    ),
    (
        "Curación Google News",
        ROOT / ".planning/spikes/002b-serpapi-news/filtrar_constructoras.py",
    ),
    (
        "CNV — Hechos relevantes",
        ROOT / ".planning/spikes/005-cnv-hechos-relevantes/cnv_probe.py",
    ),
    (
        "Boletín Oficial",
        ROOT / ".planning/spikes/006-boletin-oficial/bo_probe.py",
    ),
    (
        "Infocomercial",
        ROOT / ".planning/spikes/007-revistas-nicho/infocomercial_probe.py",
    ),
    (
        "Adlatina",
        ROOT / ".planning/spikes/007-revistas-nicho/adlatina_probe.py",
    ),
    (
        "Curación revistas de nicho",
        ROOT / ".planning/spikes/007-revistas-nicho/curar_nombramientos.py",
    ),
)

SCRIPT_TIMEOUT_SECONDS = 300
OUTPUT_TAIL_LINES = 8

ProgressCallback = Callable[[str, Optional["RefreshStepResult"], bool], None]


@dataclass
class RefreshStepResult:
    name: str
    ok: bool
    message: str


def _tail_output(text: str, max_lines: int = OUTPUT_TAIL_LINES) -> str:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def _run_script(name: str, script_path: Path) -> RefreshStepResult:
    if not script_path.exists():
        return RefreshStepResult(
            name=name,
            ok=False,
            message=f"Script no encontrado: {script_path.relative_to(ROOT)}",
        )

    try:
        completed = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return RefreshStepResult(
            name=name,
            ok=False,
            message=f"Tiempo de espera agotado ({SCRIPT_TIMEOUT_SECONDS}s).",
        )
    except OSError as error:
        return RefreshStepResult(
            name=name,
            ok=False,
            message=f"Error al ejecutar script: {error}",
        )

    output_tail = _tail_output(
        "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    )
    if completed.returncode == 0:
        message = output_tail or "Completado."
        return RefreshStepResult(name=name, ok=True, message=message)

    message = output_tail or f"Código de salida {completed.returncode}."
    return RefreshStepResult(name=name, ok=False, message=message)


def _run_pipeline_step() -> RefreshStepResult:
    name = "Consolidación (pipeline)"
    try:
        run_pipeline()
    except Exception as error:  # noqa: BLE001 — reportar fallo al dashboard
        return RefreshStepResult(
            name=name,
            ok=False,
            message=str(error),
        )
    return RefreshStepResult(name=name, ok=True, message="Eventos unificados generados.")


def run_full_refresh(
    on_progress: ProgressCallback | None = None,
) -> list[RefreshStepResult]:
    """Ejecuta los scripts de fuentes y consolida con run_pipeline()."""
    results: list[RefreshStepResult] = []

    for name, script_path in REFRESH_SCRIPTS:
        if on_progress:
            on_progress(name, None, False)
        result = _run_script(name, script_path)
        results.append(result)
        if on_progress:
            on_progress(name, result, False)

    if on_progress:
        on_progress("Consolidación (pipeline)", None, True)
    pipeline_result = _run_pipeline_step()
    results.append(pipeline_result)
    if on_progress:
        on_progress("Consolidación (pipeline)", pipeline_result, True)

    return results
