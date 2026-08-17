"""Carga de configuración desde .env y variables de entorno."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def get_serpapi_key() -> str | None:
    value = (os.environ.get("SERPAPI_API_KEY") or os.environ.get("SERPAPI_KEY") or "").strip()
    value = value.strip('"').strip("'")
    return value or None


def get_mongodb_uri() -> str | None:
    value = (os.environ.get("MONGODB_URI") or "").strip().strip('"').strip("'")
    return value or None
