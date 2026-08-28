import json
import secrets
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, UploadFile

from app.database import db_session
from app.services.parser import load_parsed_json, parse_document, parse_keywords, write_parsed_files
from app.services.similarity import compare_documents, write_result_files
from app.services.storage import save_upload, task_storage_dir
from app.utils.time import days_from_now_iso, now, now_iso


def make_no(prefix: str) -> str:
    compact = now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{compact}{secrets.token_hex(2).upper()}"


async def create_task(
    a_file: UploadFile,
    b_files: list[UploadFile],
    keywords: str | None,
    background_tasks: BackgroundTasks | None = None,
) -> dict[str, Any]:
    if not b_files or len(b_files) > 10:
        raise ValueError("VALIDATION_ERROR:B 文件数量必须为 1 至 10 份")
    task_no = make_no("T")
    mode = "single" if len(b_files) == 1 else "multi"
    with db_session() as conn:
        preview_limit = int(_setting(conn, "preview_segment_limit", "3"))
        retention_days = int(_setting(conn, "result_retention_days", "7"))
        free_b_file_limit = max(1, min(int(_setting(conn, "free_b_file_limit", "1")), 10))
        payment_required = len(b_files) > free_b_file_limit
        conn.execute(
            """
            INSERT INTO tasks (
              task_no, mode, status, unlock_status, keyword_text, b_file_count, preview_limit,
              storage_dir, progress, created_at, updated_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_no,
                mode,
                "uploaded",
                "locked" if payment_required else "free",
                keywords,
                len(b_files),
                preview_limit,
                str(task_storage_dir(task_no)),
                5,
                now_iso(),
                now_iso(),
                days_from_now_iso(retention_days),
            ),
        )
        task_id = conn.execute("SELECT id FROM tasks WHERE task_no = ?", (task_no,)).fetchone()["id"]

    try:
        await _save_task_files(task_no, task_id, a_file, b_files)
        if background_tasks:
            background_tasks.add_task(process_task_safely, task_no)
        else:
            process_task_safely(task_no)
    except ValueError as exc:
        _mark_task_failed(task_no, str(exc))
        raise
    except Exception as exc:
        _mark_task_failed(task_no, str(exc))
        raise
    return get_status(task_no)


def process_task_safely(task_no: str) -> None:
    try:
        process_task(task_no)
    except Exception as exc:
        _mark_task_failed(task_no, str(exc))


def process_task(task_no: str) -> None:
    with db_session() as conn:
        task = _task_by_no(conn, task_no)
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        _update_task(conn, task["id"], status="parsing", progress=20)
        files = conn.execute("SELECT * FROM task_files WHERE task_id = ? ORDER BY role, id", (task["id"],)).fetchall()
        for file_row in files:
            _parse_file(conn, file_row, task_no)
        a_file = conn.execute("SELECT * FROM task_files WHERE task_id = ? AND role = 'A'", (task["id"],)).fetchone()
        b_files = conn.execute(
            "SELECT * FROM task_files WHERE task_id = ? AND role = 'B' AND parse_status = 'success'",
            (task["id"],),
        ).fetchall()
        if not a_file or a_file["parse_status"] != "success":
            raise ValueError("PARSE_FAILED:主标书 A 解析失败")
        if not b_files:
            raise ValueError("PARSE_FAILED:没有可用的 B 文件")

        _update_task(conn, task["id"], status="checking", progress=60)
        keywords = parse_keywords(task["keyword_text"])
        a_doc = load_parsed_json(a_file["parsed_json_path"])
        for b_file in b_files:
            b_doc = load_parsed_json(b_file["parsed_json_path"])
            result = compare_documents(
                a_file["id"],
                b_file["id"],
                a_doc,
                b_doc,
                keywords,
                task["preview_limit"],
            )
            _save_compare_result(conn, task, a_file, b_file, a_doc, b_doc, result)

        target_status = "awaiting_payment" if task["unlock_status"] == "locked" else "completed"
        _update_task(conn, task["id"], status=target_status, progress=100, completed_at=now_iso())


def get_status(task_no: str) -> dict[str, Any]:
    with db_session() as conn:
        task = _task_by_no(conn, task_no)
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        return {
            "task_no": task["task_no"],
            "mode": task["mode"],
            "status": task["status"],
            "unlock_status": task["unlock_status"],
            "progress": task["progress"],
            "message": _status_message(task["status"]),
            "error_message": task["error_message"],
        }


def get_summary(task_no: str) -> dict[str, Any]:
    with db_session() as conn:
        task = _task_by_no(conn, task_no)
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        a_file = conn.execute("SELECT id, original_name FROM task_files WHERE task_id = ? AND role = 'A'", (task["id"],)).fetchone()
        rows = conn.execute(
            """
            SELECT cr.*, tf.original_name AS b_file_name,
                   (SELECT COUNT(*) FROM matched_segments ms WHERE ms.compare_result_id = cr.id AND ms.match_type = 'exact') AS exact_count,
                   (SELECT COUNT(*) FROM matched_segments ms WHERE ms.compare_result_id = cr.id AND ms.match_type = 'rewrite') AS rewrite_count,
                   (SELECT COUNT(*) FROM matched_segments ms WHERE ms.compare_result_id = cr.id AND ms.match_type = 'semantic') AS semantic_count
            FROM compare_results cr
            JOIN task_files tf ON tf.id = cr.b_file_id
            WHERE cr.task_id = ?
            ORDER BY cr.total_similarity DESC
            """,
            (task["id"],),
        ).fetchall()
        return {
            "task_no": task["task_no"],
            "mode": task["mode"],
            "status": task["status"],
            "unlock_status": task["unlock_status"],
            "b_file_count": task["b_file_count"],
            "a_file": {"id": a_file["id"], "name": a_file["original_name"]} if a_file else None,
            "results": [
                {
                    "compare_result_id": row["id"],
                    "b_file_id": row["b_file_id"],
                    "b_file_name": row["b_file_name"],
                    "total_similarity": row["total_similarity"],
                    "exact_similarity": row["exact_similarity"],
                    "rewrite_similarity": row["rewrite_similarity"],
                    "semantic_similarity": row["semantic_similarity"],
                    "format_similarity": row["format_similarity"],
                    "metadata_similarity": row["metadata_similarity"],
                    "keyword_hit_count": row["keyword_hit_count"],
                    "matched_sentence_count": row["matched_sentence_count"],
                    "matched_paragraph_count": row["matched_paragraph_count"],
                    "exact_count": row["exact_count"],
                    "rewrite_count": row["rewrite_count"],
                    "semantic_count": row["semantic_count"],
                }
                for row in rows
            ],
            "payment_required": task["unlock_status"] == "locked",
            "expires_at": task["expires_at"],
        }


def get_preview(task_no: str, compare_result_id: int) -> dict[str, Any]:
    with db_session() as conn:
        _require_compare_in_task(conn, task_no, compare_result_id)
        row = conn.execute("SELECT preview_json_path FROM compare_results WHERE id = ?", (compare_result_id,)).fetchone()
        payload = json.loads(Path(row["preview_json_path"]).read_text(encoding="utf-8"))
        return {"compare_result_id": compare_result_id, "segments": payload["segments"]}


def get_detail(task_no: str, compare_result_id: int) -> dict[str, Any]:
    with db_session() as conn:
        task, compare_row = _require_compare_in_task(conn, task_no, compare_result_id)
        if task["unlock_status"] == "locked":
            raise PermissionError("ORDER_NOT_PAID")
        a_file = conn.execute("SELECT * FROM task_files WHERE id = ?", (compare_row["a_file_id"],)).fetchone()
        b_file = conn.execute("SELECT * FROM task_files WHERE id = ?", (compare_row["b_file_id"],)).fetchone()
        a_doc = load_parsed_json(a_file["parsed_json_path"])
        b_doc = load_parsed_json(b_file["parsed_json_path"])
        detail = json.loads(Path(compare_row["detail_json_path"]).read_text(encoding="utf-8"))
        return {
            "compare_result_id": compare_result_id,
            "a_document": {"file_id": a_file["id"], "name": a_file["original_name"], "blocks": a_doc["blocks"]},
            "b_document": {"file_id": b_file["id"], "name": b_file["original_name"], "blocks": b_doc["blocks"]},
            "matches": detail["matches"],
            "metadata_results": detail["metadata_results"],
            "format_results": detail["format_results"],
            "keyword_hits": detail["keyword_hits"],
        }


def recover(task_no: str | None, order_no: str | None, contact: str | None) -> dict[str, Any]:
    with db_session() as conn:
        if order_no:
            row = conn.execute(
                """
                SELECT t.*, o.order_no, o.status AS order_status, o.contact AS order_contact
                FROM orders o JOIN tasks t ON t.id = o.task_id
                WHERE o.order_no = ?
                """,
                (order_no,),
            ).fetchone()
        elif task_no:
            row = conn.execute(
                """
                SELECT t.*, o.order_no, o.status AS order_status, o.contact AS order_contact
                FROM tasks t LEFT JOIN orders o ON o.task_id = t.id
                WHERE t.task_no = ?
                """,
                (task_no,),
            ).fetchone()
        else:
            raise ValueError("VALIDATION_ERROR")
        if not row:
            raise ValueError("TASK_NOT_FOUND")
        if contact and row["order_contact"] and contact != row["order_contact"]:
            raise ValueError("VALIDATION_ERROR")
        return {
            "task_no": row["task_no"],
            "order_no": row["order_no"],
            "mode": row["mode"],
            "task_status": row["status"],
            "unlock_status": row["unlock_status"],
            "order_status": row["order_status"],
            "can_view_detail": row["unlock_status"] != "locked",
            "expires_at": row["expires_at"],
        }


async def _save_task_files(task_no: str, task_id: int, a_file: UploadFile, b_files: list[UploadFile]) -> None:
    with db_session() as conn:
        a_path, a_size = await save_upload(task_no, "A", a_file)
        _insert_file(conn, task_id, "A", a_file, a_path, a_size)
        for index, upload in enumerate(b_files, start=1):
            path, size = await save_upload(task_no, "B", upload, index)
            _insert_file(conn, task_id, "B", upload, path, size)
        _update_task(conn, task_id, status="queued", progress=10)


def _insert_file(conn, task_id: int, role: str, upload: UploadFile, path: Path, size: int) -> None:
    conn.execute(
        """
        INSERT INTO task_files (
          task_id, role, original_name, stored_name, file_path, file_ext, mime_type, file_size,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            role,
            upload.filename,
            path.name,
            str(path),
            path.suffix.lower(),
            upload.content_type,
            size,
            now_iso(),
            now_iso(),
        ),
    )


def _parse_file(conn, file_row, task_no: str) -> None:
    try:
        parsed = parse_document(Path(file_row["file_path"]), file_row["file_ext"])
        parsed_dir = task_storage_dir(task_no) / "parsed"
        stem = f"file-{file_row['id']}"
        text_path = parsed_dir / f"{stem}.txt"
        json_path = parsed_dir / f"{stem}.json"
        write_parsed_files(parsed, text_path, json_path)
        conn.execute(
            """
            UPDATE task_files
            SET parse_status = 'success', parsed_text_path = ?, parsed_json_path = ?, page_count = ?,
                word_count = ?, sentence_count = ?, paragraph_count = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                str(text_path),
                str(json_path),
                parsed.page_count,
                parsed.word_count,
                parsed.sentence_count,
                parsed.paragraph_count,
                now_iso(),
                file_row["id"],
            ),
        )
    except ValueError as exc:
        conn.execute(
            "UPDATE task_files SET parse_status = 'failed', error_message = ?, updated_at = ? WHERE id = ?",
            (str(exc), now_iso(), file_row["id"]),
        )


def _save_compare_result(conn, task, a_file, b_file, a_doc, b_doc, result: dict[str, Any]) -> None:
    summary = result["summary"]
    cursor = conn.execute(
        """
        INSERT INTO compare_results (
          task_id, a_file_id, b_file_id, status, total_similarity, exact_similarity,
          rewrite_similarity, semantic_similarity, sentence_similarity, paragraph_similarity,
          format_similarity, metadata_similarity, keyword_hit_count, matched_sentence_count,
          matched_paragraph_count, created_at, updated_at
        )
        VALUES (?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task["id"],
            a_file["id"],
            b_file["id"],
            summary["total_similarity"],
            summary["exact_similarity"],
            summary["rewrite_similarity"],
            summary["semantic_similarity"],
            summary["sentence_similarity"],
            summary["paragraph_similarity"],
            summary["format_similarity"],
            summary["metadata_similarity"],
            summary["keyword_hit_count"],
            summary["matched_sentence_count"],
            summary["matched_paragraph_count"],
            now_iso(),
            now_iso(),
        ),
    )
    compare_result_id = cursor.lastrowid
    result_dir = task_storage_dir(task["task_no"]) / "results"
    preview_path = result_dir / f"compare-{compare_result_id}-preview.json"
    detail_path = result_dir / f"compare-{compare_result_id}-detail.json"
    write_result_files(result, preview_path, detail_path)
    conn.execute(
        "UPDATE compare_results SET preview_json_path = ?, detail_json_path = ? WHERE id = ?",
        (str(preview_path), str(detail_path), compare_result_id),
    )
    for index, match in enumerate(result["matches"]):
        conn.execute(
            """
            INSERT INTO matched_segments (
              compare_result_id, match_type, similarity, a_text, b_text, a_position_json,
              b_position_json, a_char_count, is_preview, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compare_result_id,
                match["match_type"],
                match["similarity"],
                match["a_text"],
                match["b_text"],
                json.dumps(match["a_position"], ensure_ascii=False),
                json.dumps(match["b_position"], ensure_ascii=False),
                match["a_char_count"],
                1 if index < task["preview_limit"] else 0,
                now_iso(),
            ),
        )
    for hit in result["keyword_hits"]:
        conn.execute(
            """
            INSERT INTO keyword_hits (
              task_id, file_id, keyword, hit_text, position_json, context_before, context_after, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task["id"],
                hit["file_id"],
                hit["keyword"],
                hit["hit_text"],
                json.dumps(hit["position"], ensure_ascii=False),
                hit["context_before"],
                hit["context_after"],
                now_iso(),
            ),
        )
    for item in result["metadata_results"]:
        conn.execute(
            """
            INSERT INTO metadata_results (
              compare_result_id, field_name, a_value, b_value, similarity_type, is_highlighted, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compare_result_id,
                item["field_name"],
                item["a_value"],
                item["b_value"],
                item["similarity_type"],
                1 if item["is_highlighted"] else 0,
                now_iso(),
            ),
        )
    for item in result["format_results"]:
        conn.execute(
            """
            INSERT INTO format_results (compare_result_id, item_name, a_value, b_value, similarity, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compare_result_id,
                item["item_name"],
                item["a_value"],
                item["b_value"],
                item["similarity"],
                item["description"],
                now_iso(),
            ),
        )


def _require_compare_in_task(conn, task_no: str, compare_result_id: int):
    row = conn.execute(
        """
        SELECT t.*, cr.id AS compare_id, cr.a_file_id, cr.b_file_id, cr.detail_json_path, cr.preview_json_path
        FROM tasks t JOIN compare_results cr ON cr.task_id = t.id
        WHERE t.task_no = ? AND cr.id = ?
        """,
        (task_no, compare_result_id),
    ).fetchone()
    if not row:
        raise ValueError("TASK_NOT_FOUND")
    return row, row


def _task_by_no(conn, task_no: str):
    return conn.execute("SELECT * FROM tasks WHERE task_no = ?", (task_no,)).fetchone()


def _setting(conn, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def _update_task(conn, task_id: int, **fields) -> None:
    fields["updated_at"] = now_iso()
    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", (*fields.values(), task_id))


def _mark_task_failed(task_no: str, message: str) -> None:
    with db_session() as conn:
        task = _task_by_no(conn, task_no)
        if task:
            _update_task(conn, task["id"], status="failed", progress=100, error_message=message)


def _status_message(status: str) -> str:
    return {
        "uploaded": "文件已上传",
        "queued": "任务排队中",
        "parsing": "正在解析文档",
        "checking": "正在查重",
        "awaiting_payment": "查重完成，等待支付解锁",
        "completed": "查重完成",
        "failed": "任务失败",
        "deleted": "任务数据已删除",
    }.get(status, status)
