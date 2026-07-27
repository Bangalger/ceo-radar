"""Conexión centralizada a MongoDB."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DB_NAME = "ceo_radar"
FEEDBACK_COLLECTION = "feedback"


def _require_mongodb_uri() -> str:
    uri = os.environ.get("MONGODB_URI", "").strip().strip('"').strip("'")
    if not uri:
        raise RuntimeError(
            "Falta MONGODB_URI en .env o variables de entorno. "
            "Configurala con la connection string de MongoDB Atlas."
        )
    return uri


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    return MongoClient(_require_mongodb_uri())


def get_feedback_collection() -> Collection:
    return get_client()[DB_NAME][FEEDBACK_COLLECTION]
