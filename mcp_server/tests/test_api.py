from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from bscc_mcp.api import BSCCClient, BSCCError
from bscc_mcp.config import Settings


def settings(root: Path, *, max_file_bytes: int = 1024, max_total_bytes: int = 2048) -> Settings:
    return Settings("http://127.0.0.1:8000", "http://127.0.0.1:5173", (root,), max_file_bytes, max_total_bytes, 10)


def test_file_access_and_limits(tmp_path: Path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    ok = allowed / "ok.TXT"
    ok.write_text("内容", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("内容", encoding="utf-8")
    client = BSCCClient(settings(allowed, max_file_bytes=6, max_total_bytes=12))
    assert client._resolve_files(str(ok), [str(ok)]) == [ok.resolve(), ok.resolve()]

    unconfigured = BSCCClient(Settings("http://127.0.0.1:8000", "http://127.0.0.1:5173", (), 100, 100, 10))
    with pytest.raises(BSCCError, match="ALLOWED_DIRS_REQUIRED"):
        unconfigured._resolve_files(str(ok), [str(ok)])

    with pytest.raises(BSCCError, match="FILE_OUTSIDE_ALLOWED_DIRS"):
        client._resolve_files(str(outside), [str(ok)])
    with pytest.raises(BSCCError, match="VALIDATION_ERROR"):
        client._resolve_files("relative.txt", [str(ok)])
    with pytest.raises(BSCCError, match="VALIDATION_ERROR"):
        client._resolve_files(str(ok), [str(ok)] * 11)
    unsupported = allowed / "old.doc"
    unsupported.write_text("old", encoding="utf-8")
    with pytest.raises(BSCCError, match="UNSUPPORTED_FILE_TYPE"):
        client._resolve_files(str(unsupported), [str(ok)])
    large = allowed / "large.txt"
    large.write_bytes(b"x" * 7)
    with pytest.raises(BSCCError, match="FILE_TOO_LARGE"):
        client._resolve_files(str(large), [str(ok)])
    with pytest.raises(BSCCError, match="UPLOAD_TOO_LARGE"):
        client._resolve_files(str(ok), [str(ok), str(ok)])


def test_symlink_cannot_escape_allowed_directory(tmp_path: Path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("text", encoding="utf-8")
    link = allowed / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks is unavailable on this machine")
    client = BSCCClient(settings(allowed))
    with pytest.raises(BSCCError, match="FILE_OUTSIDE_ALLOWED_DIRS"):
        client._resolve_files(str(link), [str(link)])


async def test_creation_timeout_never_retries(tmp_path: Path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("text", encoding="utf-8")
    calls = []

    def handler(request: httpx.Request):
        calls.append(request.method)
        raise httpx.ReadTimeout("simulated", request=request)

    client = BSCCClient(settings(tmp_path), httpx.MockTransport(handler))
    with pytest.raises(BSCCError, match="CREATE_OUTCOME_UNKNOWN"):
        await client.create(str(file_path), [str(file_path)], None)
    assert calls == ["POST"]


@pytest.mark.parametrize("response", [httpx.Response(500, json={"success": False}), httpx.Response(200, text="broken")])
async def test_creation_with_uncertain_response_never_retries(tmp_path: Path, response: httpx.Response):
    file_path = tmp_path / "a.txt"
    file_path.write_text("text", encoding="utf-8")
    calls = []

    def handler(request: httpx.Request):
        calls.append(request.method)
        return response

    client = BSCCClient(settings(tmp_path), httpx.MockTransport(handler))
    with pytest.raises(BSCCError, match="CREATE_OUTCOME_UNKNOWN"):
        await client.create(str(file_path), [str(file_path)], None)
    assert calls == ["POST"]


async def test_creation_keeps_task_number_if_summary_fails(tmp_path: Path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("text", encoding="utf-8")
    calls = []

    def handler(request: httpx.Request):
        calls.append(request.method)
        if request.method == "POST":
            return httpx.Response(200, json={"success": True, "data": {"task_no": "T123", "status": "queued"}})
        return httpx.Response(503, json={"success": False, "error": {"code": "BACKEND_ERROR", "message": "暂不可用"}})

    client = BSCCClient(settings(tmp_path), httpx.MockTransport(handler))
    result = await client.create(str(file_path), [str(file_path)], None)
    assert result["task_no"] == "T123"
    assert result["result_url"].endswith("/results?task=T123")
    assert result["expires_at"] is None
    assert calls == ["POST", "GET"]


async def test_expired_task_and_malformed_response(tmp_path: Path):
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    payload = {"success": True, "data": {"task_no": "T123", "expires_at": expired, "results": []}}
    client = BSCCClient(settings(tmp_path), httpx.MockTransport(lambda request: httpx.Response(200, json=payload)))
    with pytest.raises(BSCCError, match="TASK_EXPIRED"):
        await client.status("T123")

    client = BSCCClient(settings(tmp_path), httpx.MockTransport(lambda request: httpx.Response(200, text="not json")))
    with pytest.raises(BSCCError, match="INVALID_API_RESPONSE"):
        await client.summary("T123")


def test_config_disallows_insecure_remote(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("BSCC_ALLOWED_DIRS", raising=False)
    monkeypatch.setenv("BSCC_API_BASE_URL", "http://example.com")
    with pytest.raises(ValueError, match="HTTPS"):
        Settings.from_env()


def test_config_rejects_relative_allowed_directory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BSCC_ALLOWED_DIRS", "relative-directory")
    with pytest.raises(ValueError, match="绝对目录路径"):
        Settings.from_env()
