"""Conexión centralizada a MongoDB."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# #region agent log
import sys as _dbg_sys
import json as _dbg_json
import time as _dbg_time
import importlib.util as _dbg_ilu

try:
    _dbg_spec = _dbg_ilu.find_spec("pymongo")
    _dbg_spec_str = str(_dbg_spec) if _dbg_spec else "NOT_FOUND"
except Exception as _dbg_e:  # noqa: BLE001
    _dbg_spec_str = f"ERROR_FINDING_SPEC: {_dbg_e!r}"

_dbg_log_path = Path(__file__).resolve().parents[2] / "debug-515249.log"
try:
    with open(_dbg_log_path, "a", encoding="utf-8") as _dbg_f:
        _dbg_f.write(
            _dbg_json.dumps(
                {
                    "sessionId": "515249",
                    "runId": "run1",
                    "hypothesisId": "H1-H4",
                    "location": "src/ceo_radar/db.py:before-pymongo-import",
                    "message": "env snapshot right before importing pymongo",
                    "data": {
                        "sys_executable": _dbg_sys.executable,
                        "sys_prefix": _dbg_sys.prefix,
                        "sys_base_prefix": _dbg_sys.base_prefix,
                        "sys_version": _dbg_sys.version,
                        "VIRTUAL_ENV": __import__("os").environ.get("VIRTUAL_ENV"),
                        "PYTHONPATH": __import__("os").environ.get("PYTHONPATH"),
                        "PYTHONHOME": __import__("os").environ.get("PYTHONHOME"),
                        "pymongo_find_spec": _dbg_spec_str,
                        "sys_path": _dbg_sys.path,
                    },
                    "timestamp": int(_dbg_time.time() * 1000),
                }
            )
            + "\n"
        )
except Exception:  # noqa: BLE001
    pass
# #endregion agent log

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
