import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
from mcp import Client
import pytest

from test_stdio_integration import call_ok, stdio_parameters, wait_for_task


async def test_returned_links_open_real_frontend(backend, tmp_path: Path):
    node = os.environ.get("BSCC_TEST_BROWSER_NODE")
    playwright = os.environ.get("BSCC_TEST_PLAYWRIGHT")
    browser = os.environ.get("BSCC_TEST_BROWSER")
    if not all((node, playwright, browser)):
        pytest.skip("Set BSCC_TEST_BROWSER_NODE, BSCC_TEST_PLAYWRIGHT and BSCC_TEST_BROWSER for the browser check")

    repo = Path(__file__).resolve().parents[2]
    vite = repo / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite.exists():
        pytest.skip("Install frontend dependencies before running the browser check")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    frontend_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = backend["url"]
    log_path = tmp_path / "vite.log"
    log = log_path.open("wb")
    process = subprocess.Popen(
        [node, str(vite), "--host", "127.0.0.1", "--port", str(port), "--strictPort"],
        cwd=repo / "frontend", env=env, stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    try:
        for _ in range(200):
            if process.poll() is not None:
                log.flush()
                raise RuntimeError(log_path.read_text(encoding="utf-8", errors="replace"))
            try:
                if httpx.get(frontend_url, timeout=0.5, trust_env=False).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Vite did not start")

        allowed = tmp_path / "documents"
        allowed.mkdir()
        first = allowed / "a.txt"
        second = allowed / "b.txt"
        content = "标书查重网页链接验证。\n\n这里是用于核对网页结果的重复文本。"
        first.write_text(content, encoding="utf-8")
        second.write_text(content, encoding="utf-8")
        params = stdio_parameters(backend["url"], allowed)
        params.env["BSCC_FRONTEND_BASE_URL"] = frontend_url
        async with Client(params, read_timeout_seconds=30) as client:
            created = await call_ok(client, "create_similarity_check", {"a_file_path": str(first), "b_file_paths": [str(second)]})
            assert (await wait_for_task(client, created["task_no"]))["status"] == "completed"
            summary = await call_ok(client, "get_check_summary", {"task_no": created["task_no"]})
            result_url = created["result_url"]
            compare_url = summary["results"][0]["compare_url"]
            check = subprocess.run(
                [node, str(Path(__file__).with_name("browser_links.cjs")), result_url, compare_url, created["task_no"]],
                env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            assert check.returncode == 0, check.stderr
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        log.close()
