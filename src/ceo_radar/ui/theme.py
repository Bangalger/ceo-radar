"""Inyección de tema y helpers visuales."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).resolve().parent / "theme.css"


def inject_theme() -> None:
    """Inyecta el CSS del tema Executive Radar Dark."""
    # Reloj de mtime: invalida la caché cuando theme.css cambia en disco.
    mtime = _CSS_PATH.stat().st_mtime
    css = _load_css(mtime)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@lru_cache(maxsize=4)
def _load_css(mtime: float) -> str:
    del mtime
    return _CSS_PATH.read_text(encoding="utf-8")


def icon(name: str, *, filled: bool = False, size: str = "24px") -> str:
    """Genera markup HTML para un ícono Material Symbols Outlined."""
    fill_class = " filled" if filled else ""
    return (
        f'<span class="material-symbols-outlined{fill_class}" '
        f'style="font-size:{size}">{name}</span>'
    )
