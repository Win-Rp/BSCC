import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest


@pytest.fixture
def backend(tmp_path: Path):
    """Run the real backend against a temporary SQLite DB and storage directory."""
    backend_python = os.environ.get("BSCC_TEST_BACKEND_PYTHON")
    if not backend_python:
        pytest.skip("Set BSCC_TEST_BACKEND_PYTHON to a Python with backend/requirements.txt installed")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    test_dir = tmp_path / "backend"
    test_dir.mkdir()
    env = os.environ.copy()
    env.update({"BSCC_TEST_DIR": str(test_dir), "BSCC_TEST_PORT": str(port), "PYTHONUTF8": "1"})
    env.pop("DATABASE_URL", None)
    log_path = tmp_path / "backend.log"
    log = log_path.open("wb")
    process = subprocess.Popen(
        [backend_python, "-u", str(Path(__file__).with_name("backend_fixture.py"))],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(200):
            if process.poll() is not None:
                log.flush()
                raise RuntimeError(f"Backend exited during startup: {log_path.read_text(encoding='utf-8', errors='replace')}")
            try:
                if httpx.get(f"{base_url}/api/health", timeout=0.5, trust_env=False).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.1)
        else:
            log.flush()
            raise RuntimeError(f"Backend did not start: {log_path.read_text(encoding='utf-8', errors='replace')}")
        yield {"url": base_url, "db": test_dir / "data" / "bscc-test.sqlite3", "storage": test_dir / "storage"}
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        log.close()
