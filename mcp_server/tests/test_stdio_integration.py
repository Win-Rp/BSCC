import asyncio
from pathlib import Path
import sqlite3
import sys

import httpx
from docx import Document
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from reportlab.pdfgen import canvas


def stdio_parameters(backend_url: str, allowed_dir: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "bscc_mcp"],
        cwd=Path(__file__).resolve().parents[1],
        env={
            "BSCC_API_BASE_URL": backend_url,
            "BSCC_FRONTEND_BASE_URL": "http://127.0.0.1:5173",
            "BSCC_ALLOWED_DIRS": str(allowed_dir),
            "PYTHONUTF8": "1",
        },
    )


def error_text(result) -> str:
    return " ".join(getattr(block, "text", "") for block in result.content)


async def call_ok(client: Client, name: str, arguments: dict):
    result = await client.call_tool(name, arguments)
    assert not result.is_error, error_text(result)
    assert isinstance(result.structured_content, dict), result
    return result.structured_content


async def wait_for_task(client: Client, task_no: str) -> dict:
    for _ in range(150):
        status = await call_ok(client, "get_check_status", {"task_no": task_no})
        if status["status"] in {"completed", "awaiting_payment", "failed"}:
            return status
        await asyncio.sleep(0.2)
    raise AssertionError(f"Task did not finish: {task_no}")


async def test_real_mcp_stdio_and_backend(backend, tmp_path: Path):
    allowed = tmp_path / "documents"
    allowed.mkdir()
    content = "\n\n".join(f"第{i}章，项目采用统一数据平台并提供运维支持。" for i in range(1, 16))
    a_path, b1_path, b2_path = (allowed / name for name in ("主标书.txt", "对比一.txt", "对比二.txt"))
    a_path.write_text(content, encoding="utf-8-sig")
    b1_path.write_text(content, encoding="utf-8")
    b2_path.write_text(content, encoding="utf-8")

    async with Client(stdio_parameters(backend["url"], allowed), read_timeout_seconds=30) as client:
        tools = await client.list_tools()
        assert {item.name for item in tools.tools} == {
            "create_similarity_check", "get_check_status", "get_check_summary",
            "get_comparison_preview", "get_comparison_detail",
        }

        created = await call_ok(client, "create_similarity_check", {
            "a_file_path": str(a_path), "b_file_paths": [str(b1_path)], "keywords": ["运维"],
        })
        task_no = created["task_no"]
        assert created["b_file_count"] == 1
        assert created["result_url"] == f"http://127.0.0.1:5173/results?task={task_no}"
        assert created["expires_at"]
        assert (await wait_for_task(client, task_no))["status"] == "completed"

        summary = await call_ok(client, "get_check_summary", {"task_no": task_no})
        assert summary["payment_required"] is False
        result_id = summary["results"][0]["compare_result_id"]
        assert summary["results"][0]["total_similarity"] > 0.9
        assert summary["results"][0]["compare_url"] == f"http://127.0.0.1:5173/compare?task={task_no}&result={result_id}"
        preview = await call_ok(client, "get_comparison_preview", {"task_no": task_no, "compare_result_id": result_id})
        assert preview["segments"]
        first_preview = await call_ok(client, "get_comparison_preview", {"task_no": task_no, "compare_result_id": result_id, "limit": 1})
        assert first_preview["pagination"]["next_offset"] == 1
        second_preview = await call_ok(client, "get_comparison_preview", {"task_no": task_no, "compare_result_id": result_id, "limit": 1, "offset": 1})
        assert second_preview["segments"][0] != first_preview["segments"][0]

        page = await call_ok(client, "get_comparison_detail", {
            "task_no": task_no, "compare_result_id": result_id, "limit": 1,
        })
        assert len(page["matches"]) == 1
        assert len(page["keyword_hits"]) == 1
        assert "blocks" not in page["a_document"]
        assert page["pagination"]["matches"]["next_offset"] == 1
        assert page["pagination"]["keyword_hits"]["next_offset"] == 1
        page_two = await call_ok(client, "get_comparison_detail", {
            "task_no": task_no, "compare_result_id": result_id, "limit": 1,
            "match_offset": 1, "keyword_offset": 1,
        })
        assert page_two["matches"][0] != page["matches"][0]
        assert page_two["keyword_hits"][0] != page["keyword_hits"][0]

        # Existing web clients still receive full blocks when no paging options are supplied.
        url = f"{backend['url']}/api/tasks/{task_no}/results/{result_id}/detail"
        original = httpx.get(url, trust_env=False).json()["data"]
        assert original["a_document"]["blocks"]
        assert len(original["matches"]) >= 2
        assert "pagination" not in original
        assert httpx.get(url, params={"limit": 101}, trust_env=False).status_code == 422

        locked = await call_ok(client, "create_similarity_check", {
            "a_file_path": str(a_path), "b_file_paths": [str(b1_path), str(b2_path)],
        })
        locked_no = locked["task_no"]
        assert (await wait_for_task(client, locked_no))["status"] == "awaiting_payment"
        locked_summary = await call_ok(client, "get_check_summary", {"task_no": locked_no})
        assert locked_summary["payment_required"] is True
        locked_id = locked_summary["results"][0]["compare_result_id"]
        assert locked_summary["results"][0]["compare_url"] is None
        assert (await call_ok(client, "get_comparison_preview", {"task_no": locked_no, "compare_result_id": locked_id}))["segments"]
        locked_detail = await client.call_tool("get_comparison_detail", {"task_no": locked_no, "compare_result_id": locked_id})
        assert locked_detail.is_error
        assert "ORDER_NOT_PAID" in error_text(locked_detail)
        assert f"/results?task={locked_no}&result={locked_id}" in error_text(locked_detail)
        assert httpx.get(f"{backend['url']}/api/tasks/{locked_no}/results/{locked_id}/detail", params={"include_blocks": "false", "limit": 1}, trust_env=False).status_code == 402

        # Insert a synthetic order into the isolated database, then use the real
        # admin endpoint to exercise the paid-to-unlocked transition without a payment provider.
        with sqlite3.connect(backend["db"]) as conn:
            task_id = conn.execute("SELECT id FROM tasks WHERE task_no = ?", (locked_no,)).fetchone()[0]
            conn.execute(
                "INSERT INTO orders (order_no, task_id, contact, status, b_file_count, unit_price_cents, amount_cents, created_at, updated_at) "
                "VALUES (?, ?, ?, 'pending', 2, 1000, 2000, ?, ?)",
                ("O_TEST_MCP", task_id, "test@example.invalid", "2026-01-01", "2026-01-01"),
            )
        login = httpx.post(f"{backend['url']}/api/admin/login", json={"username": "admin", "password": "admin123"}, trust_env=False)
        assert login.status_code == 200
        token = login.json()["data"]["token"]
        paid = httpx.post(f"{backend['url']}/api/admin/orders/O_TEST_MCP/mark-paid", headers={"Authorization": f"Bearer {token}"}, trust_env=False)
        assert paid.status_code == 200 and paid.json()["data"]["status"] == "paid"
        unlocked = await call_ok(client, "get_check_summary", {"task_no": locked_no})
        assert unlocked["payment_required"] is False
        assert unlocked["results"][0]["compare_url"].endswith(f"/compare?task={locked_no}&result={locked_id}")
        assert (await call_ok(client, "get_comparison_detail", {"task_no": locked_no, "compare_result_id": locked_id}))["matches"]

        outside = tmp_path / "outside.txt"
        outside.write_text(content, encoding="utf-8")
        denied = await client.call_tool("create_similarity_check", {"a_file_path": str(outside), "b_file_paths": [str(b1_path)]})
        assert denied.is_error and "FILE_OUTSIDE_ALLOWED_DIRS" in error_text(denied)
        too_many = await client.call_tool("create_similarity_check", {"a_file_path": str(a_path), "b_file_paths": [str(b1_path)] * 11})
        assert too_many.is_error

        max_batch = await call_ok(client, "create_similarity_check", {"a_file_path": str(a_path), "b_file_paths": [str(b1_path)] * 10})
        assert (await wait_for_task(client, max_batch["task_no"]))["status"] == "awaiting_payment"
        assert len((await call_ok(client, "get_check_summary", {"task_no": max_batch["task_no"]}))["results"]) == 10

        invalid = allowed / "wrong-encoding.txt"
        invalid.write_bytes(b"\xff\xfe\xff")
        failed = await call_ok(client, "create_similarity_check", {"a_file_path": str(invalid), "b_file_paths": [str(b1_path)]})
        failed_status = await wait_for_task(client, failed["task_no"])
        assert failed_status["status"] == "failed"
        assert "UTF-8" in failed_status["error_message"]

        blank_pdf = allowed / "scan.pdf"
        blank = canvas.Canvas(str(blank_pdf))
        blank.showPage()
        blank.save()
        scan = await client.call_tool("create_similarity_check", {"a_file_path": str(blank_pdf), "b_file_paths": [str(b1_path)]})
        assert scan.is_error and "SCAN_PDF_NOT_SUPPORTED" in error_text(scan)
        assert "扫描件" in error_text(scan)

        corrupt_pdf = allowed / "corrupt.pdf"
        corrupt_pdf.write_bytes(b"%PDF-1.4\nnot a valid PDF")
        invalid_pdf = await client.call_tool("create_similarity_check", {"a_file_path": str(corrupt_pdf), "b_file_paths": [str(b1_path)]})
        assert invalid_pdf.is_error and "PDF_INVALID" in error_text(invalid_pdf)

        # DOCX and selectable-text PDF use the same existing parser and task pipeline.
        word = allowed / "a.docx"
        doc = Document()
        doc.add_paragraph("The project provides deployment and maintenance services.")
        doc.save(word)
        pdf = allowed / "b.pdf"
        document = canvas.Canvas(str(pdf))
        document.drawString(72, 720, "The project provides deployment and maintenance services.")
        document.save()
        mixed = await call_ok(client, "create_similarity_check", {"a_file_path": str(word), "b_file_paths": [str(pdf)]})
        assert (await wait_for_task(client, mixed["task_no"]))["status"] == "completed"
        assert (await call_ok(client, "get_check_summary", {"task_no": mixed["task_no"]}))["results"]

        with sqlite3.connect(backend["db"]) as conn:
            conn.execute("UPDATE tasks SET expires_at = ? WHERE task_no = ?", ("2000-01-01T00:00:00+08:00", task_no))
        expired = await client.call_tool("get_check_status", {"task_no": task_no})
        assert expired.is_error and "TASK_EXPIRED" in error_text(expired)


async def test_legacy_mcp_client_can_discover_tools(backend, tmp_path: Path):
    allowed = tmp_path / "documents"
    allowed.mkdir()
    first = allowed / "legacy-a.txt"
    second = allowed / "legacy-b.txt"
    first.write_text("历史协议客户端也可以查询标书重复内容。", encoding="utf-8")
    second.write_text("历史协议客户端也可以查询标书重复内容。", encoding="utf-8")
    async with Client(stdio_parameters(backend["url"], allowed), mode="legacy", read_timeout_seconds=30) as client:
        assert client.protocol_version != "2026-07-28"
        assert len((await client.list_tools()).tools) == 5
        created = await call_ok(client, "create_similarity_check", {"a_file_path": str(first), "b_file_paths": [str(second)]})
        assert "/results?task=" in created["result_url"]
        assert (await wait_for_task(client, created["task_no"]))["status"] == "completed"
        assert (await call_ok(client, "get_check_summary", {"task_no": created["task_no"]}))["results"]
        missing = await client.call_tool("get_check_status", {"task_no": "T000"})
        assert missing.is_error and "TASK_NOT_FOUND" in error_text(missing)
