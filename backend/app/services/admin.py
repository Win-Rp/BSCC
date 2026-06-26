import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks

from app.database import db_session
from app.utils.security import make_token, verify_password
from app.utils.time import now_iso, days_from_now_iso
from app.services.tasks import process_task_safely
from app.services.storage import task_storage_dir


TOKENS: dict[str, dict[str, Any]] = {}


def login(username: str, password: str) -> dict[str, Any]:
    with db_session() as conn:
        admin = conn.execute(
            "SELECT * FROM admin_users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
        if not admin or not verify_password(password, admin["password_hash"]):
            raise PermissionError("ADMIN_UNAUTHORIZED")
        token = make_token()
        TOKENS[token] = {"id": admin["id"], "username": admin["username"], "display_name": admin["display_name"]}
        conn.execute("UPDATE admin_users SET last_login_at = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), admin["id"]))
        return {"token": token, "username": admin["username"], "display_name": admin["display_name"]}


def require_admin(token: str) -> dict[str, Any]:
    admin = TOKENS.get(token)
    if not admin:
        raise PermissionError("ADMIN_UNAUTHORIZED")
    return admin


def list_orders() -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT o.order_no, t.task_no, o.status, o.amount_cents, o.b_file_count, o.contact,
                   o.created_at, o.paid_at
            FROM orders o JOIN tasks t ON t.id = o.task_id
            ORDER BY o.id DESC
            LIMIT 100
            """
        ).fetchall()
        return {"items": [dict(row) for row in rows], "total": len(rows)}


def list_tasks() -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT task_no, mode, status, unlock_status, b_file_count, progress, error_message,
                   created_at, completed_at, expires_at
            FROM tasks
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()
        return {"items": [dict(row) for row in rows], "total": len(rows)}


def get_settings() -> dict[str, str]:
    with db_session() as conn:
        rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
        return {row["key"]: row["value"] for row in rows}


def update_settings(payload: dict[str, str | None], admin_user_id: int) -> dict[str, str]:
    allowed = {key: value for key, value in payload.items() if value is not None}
    with db_session() as conn:
        for key, value in allowed.items():
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, value, now_iso()),
            )
            conn.execute(
                """
                INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, detail_json, created_at)
                VALUES (?, 'update_setting', 'setting', ?, ?, ?)
                """,
                (admin_user_id, key, value, now_iso()),
            )
    return get_settings()


def list_logs() -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT l.id, l.action, l.target_type, l.target_id, l.detail_json, l.created_at,
                   u.username AS admin_username
            FROM operation_logs l
            LEFT JOIN admin_users u ON u.id = l.admin_user_id
            ORDER BY l.id DESC
            LIMIT 100
            """
        ).fetchall()
        return {"items": [dict(row) for row in rows], "total": len(rows)}


def retry_task(task_no: str, admin_user_id: int, background_tasks: BackgroundTasks) -> None:
    with db_session() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        
        # delete compare_results dependencies
        conn.execute("DELETE FROM format_results WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task["id"],))
        conn.execute("DELETE FROM metadata_results WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task["id"],))
        conn.execute("DELETE FROM matched_segments WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task["id"],))
        conn.execute("DELETE FROM keyword_hits WHERE task_id = ?", (task["id"],))
        conn.execute("DELETE FROM compare_results WHERE task_id = ?", (task["id"],))
        
        # update task status
        conn.execute(
            "UPDATE tasks SET status = 'queued', progress = 10, error_message = NULL, updated_at = ? WHERE id = ?",
            (now_iso(), task["id"])
        )
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, created_at)
            VALUES (?, 'retry_task', 'task', ?, ?)
            """,
            (admin_user_id, task_no, now_iso()),
        )
    background_tasks.add_task(process_task_safely, task_no)


def extend_task(task_no: str, admin_user_id: int) -> None:
    with db_session() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        
        new_expires_at = days_from_now_iso(7, base_time=task["expires_at"])
        conn.execute(
            "UPDATE tasks SET expires_at = ?, updated_at = ? WHERE id = ?",
            (new_expires_at, now_iso(), task["id"])
        )
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, created_at)
            VALUES (?, 'extend_task', 'task', ?, ?)
            """,
            (admin_user_id, task_no, now_iso()),
        )


def delete_task_data(task_no: str, admin_user_id: int) -> None:
    with db_session() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        if task["status"] == "deleted":
            return
            
        # Delete task dependencies except task_files and tasks and orders
        conn.execute("DELETE FROM format_results WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task["id"],))
        conn.execute("DELETE FROM metadata_results WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task["id"],))
        conn.execute("DELETE FROM matched_segments WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task["id"],))
        conn.execute("DELETE FROM keyword_hits WHERE task_id = ?", (task["id"],))
        conn.execute("DELETE FROM compare_results WHERE task_id = ?", (task["id"],))
        
        # Note: Do not delete task_files, keep them for order display or debugging if needed. But we might want to clear file_path contents.
        conn.execute(
            "UPDATE tasks SET status = 'deleted', deleted_at = ?, updated_at = ? WHERE id = ?",
            (now_iso(), now_iso(), task["id"])
        )
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, created_at)
            VALUES (?, 'delete_task', 'task', ?, ?)
            """,
            (admin_user_id, task_no, now_iso()),
        )
        
    storage_dir = task_storage_dir(task_no)
    if storage_dir.exists() and storage_dir.is_dir():
        shutil.rmtree(storage_dir, ignore_errors=True)

