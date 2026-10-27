"""Start a disposable BSCC backend for subprocess integration tests."""

import os
from pathlib import Path
import sys

import uvicorn

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "backend"))

from app import database  # noqa: E402
from app.services import storage  # noqa: E402

test_dir = Path(os.environ["BSCC_TEST_DIR"])
database.DATA_DIR = test_dir / "data"
database.DB_PATH = database.DATA_DIR / "bscc-test.sqlite3"
database.DATABASE_URL = "sqlite:///test"
storage.STORAGE_DIR = test_dir / "storage"

from app.main import app  # noqa: E402

uvicorn.run(app, host="127.0.0.1", port=int(os.environ["BSCC_TEST_PORT"]), log_level="warning")
