"""Conexión centralizada a MongoDB."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ceo_radar.config import get_mongodb_uri

DB_NAME = "ceo_radar"
FEEDBACK_COLLECTION = "feedback"
LINKEDIN_COLLECTION = "linkedin_lookups"


def _require_mongodb_uri() -> str:
    uri = get_mongodb_uri()
    if not uri:
        raise RuntimeError(
            "Falta MONGODB_URI en .env o variables de entorno. "
            "Configurala con la connection string de MongoDB Atlas."
        )
    return uri


@lru_cache(maxsize=1)
def get_client() -> Any:
    from pymongo import MongoClient

    return MongoClient(_require_mongodb_uri())


def get_feedback_collection() -> Any:
    return get_client()[DB_NAME][FEEDBACK_COLLECTION]


def get_linkedin_collection() -> Any:
    collection = get_client()[DB_NAME][LINKEDIN_COLLECTION]
    collection.create_index("key", unique=True)
    return collection
