import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks

from app.database import db_session
from app.utils.security import hash_password, make_admin_token, verify_admin_token, verify_password
from app.utils.site_url import join_base_url, normalize_base_url
from app.utils.time import TZ, now_iso, days_from_now_iso
from app.services.tasks import process_task_safely
from app.services.storage import task_storage_dir


def login(username: str, password: str) -> dict[str, Any]:
    with db_session() as conn:
        admin = conn.execute(
            "SELECT * FROM admin_users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
        if not admin or not verify_password(password, admin["password_hash"]):
            raise PermissionError("ADMIN_UNAUTHORIZED")
        version = admin["updated_at"] or ""
        token = make_admin_token(admin["id"], admin["username"], version)
        conn.execute("UPDATE admin_users SET last_login_at = ? WHERE id = ?", (now_iso(), admin["id"]))
        return {"token": token, "username": admin["username"], "display_name": admin["display_name"]}


def require_admin(token: str) -> dict[str, Any]:
    payload = verify_admin_token(token)
    if not payload:
        raise PermissionError("ADMIN_UNAUTHORIZED")

    with db_session() as conn:
        admin = conn.execute(
            "SELECT id, username, display_name, is_active, updated_at FROM admin_users WHERE id = ?",
            (payload["id"],),
        ).fetchone()
        if not admin or admin["is_active"] != 1:
            raise PermissionError("ADMIN_UNAUTHORIZED")
        if admin["username"] != payload.get("username"):
            raise PermissionError("ADMIN_UNAUTHORIZED")
        if (admin["updated_at"] or "") != str(payload.get("ver", "")):
            raise PermissionError("ADMIN_UNAUTHORIZED")

        return {
            "id": admin["id"],
            "username": admin["username"],
            "display_name": admin["display_name"],
        }


def change_password(admin_user_id: int, current_password: str, new_password: str, confirm_password: str) -> dict[str, Any]:
    if not current_password or not new_password or not confirm_password:
        raise ValueError("密码不能为空")
    if new_password != confirm_password:
        raise ValueError("两次输入的新密码不一致")
    if len(new_password) < 6:
        raise ValueError("新密码长度不能少于 6 位")

    with db_session() as conn:
        admin = conn.execute("SELECT * FROM admin_users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin or not verify_password(current_password, admin["password_hash"]):
            raise PermissionError("ADMIN_UNAUTHORIZED")

        conn.execute(
            "UPDATE admin_users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (hash_password(new_password), now_iso(), admin_user_id),
        )
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, detail_json, created_at)
            VALUES (?, 'change_password', 'admin_user', ?, NULL, ?)
            """,
            (admin_user_id, str(admin_user_id), now_iso()),
        )

    return {"force_relogin": True}


def list_orders(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    keyword: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> dict[str, Any]:
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 10)))
    offset = (page - 1) * page_size
    where_sql, params = _build_list_filters(
        [
            ("t.status != ?", "deleted"),
            ("o.status = ?", status),
            ("o.created_at >= ?", _normalize_datetime_filter(created_from, is_end=False)),
            ("o.created_at <= ?", _normalize_datetime_filter(created_to, is_end=True)),
        ],
        keyword,
        [
            "o.order_no",
            "t.task_no",
            "o.contact",
        ],
    )
    with db_session() as conn:
        total = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM orders o JOIN tasks t ON t.id = o.task_id
            {where_sql}
            """,
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT o.order_no, t.task_no, o.status, o.amount_cents, o.b_file_count, o.contact,
                   o.created_at, o.paid_at
            FROM orders o JOIN tasks t ON t.id = o.task_id
            {where_sql}
            ORDER BY o.id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "page": page, "page_size": page_size}


def list_tasks(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    keyword: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> dict[str, Any]:
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 10)))
    offset = (page - 1) * page_size
    where_sql, params = _build_list_filters(
        [
            ("status != ?", "deleted"),
            ("status = ?", status),
            ("created_at >= ?", _normalize_datetime_filter(created_from, is_end=False)),
            ("created_at <= ?", _normalize_datetime_filter(created_to, is_end=True)),
        ],
        keyword,
        [
            "task_no",
            "error_message",
            "mode",
            "unlock_status",
        ],
    )
    with db_session() as conn:
        total = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM tasks
            {where_sql}
            """,
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT task_no, mode, status, unlock_status, b_file_count, progress, error_message,
                   created_at, completed_at, expires_at
            FROM tasks
            {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "page": page, "page_size": page_size}


def get_overview() -> dict[str, Any]:
    with db_session() as conn:
        order_counts = conn.execute(
            """
            SELECT
                COUNT(*) AS total_orders,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_orders,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_orders,
                SUM(CASE WHEN status = 'paid' THEN amount_cents ELSE 0 END) AS paid_amount_cents,
                SUM(CASE WHEN status = 'pending' THEN amount_cents ELSE 0 END) AS pending_amount_cents
            FROM orders
            WHERE task_id IN (SELECT id FROM tasks WHERE status != 'deleted')
            """
        ).fetchone()
        task_counts = conn.execute(
            """
            SELECT
                COUNT(*) AS total_tasks,
                SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) AS processing_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_tasks,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_tasks
            FROM tasks
            WHERE status != 'deleted'
            """
        ).fetchone()
        log_count = conn.execute("SELECT COUNT(*) AS total_logs FROM operation_logs").fetchone()
        recent_orders = conn.execute(
            """
            SELECT o.order_no, t.task_no, o.status, o.amount_cents, o.b_file_count, o.contact,
                   o.created_at, o.paid_at
            FROM orders o
            JOIN tasks t ON t.id = o.task_id
            WHERE t.status != 'deleted'
            ORDER BY o.id DESC
            LIMIT 5
            """
        ).fetchall()
        recent_tasks = conn.execute(
            """
            SELECT task_no, mode, status, unlock_status, b_file_count, progress, error_message,
                   created_at, completed_at, expires_at
            FROM tasks
            WHERE status != 'deleted'
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()
        recent_logs = conn.execute(
            """
            SELECT l.id, l.action, l.target_type, l.target_id, l.detail_json, l.created_at,
                   u.username AS admin_username
            FROM operation_logs l
            LEFT JOIN admin_users u ON u.id = l.admin_user_id
            ORDER BY l.id DESC
            LIMIT 6
            """
        ).fetchall()
        settings_rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()

    settings = _format_settings({row["key"]: row["value"] for row in settings_rows})
    normalized_site_base_url = normalize_base_url(settings["site_base_url"])
    default_alipay_notify_url = join_base_url(normalized_site_base_url, "/api/payments/alipay/notify")
    default_wechat_notify_url = join_base_url(normalized_site_base_url, "/api/payments/wechat/notify")

    alipay_configured = bool(
        settings["alipay_gateway"]
        and settings["alipay_app_id"]
        and settings["alipay_private_key"]
        and settings["alipay_public_key"]
        and (settings["alipay_notify_url"] or default_alipay_notify_url)
    )
    wechat_configured = bool(
        settings["wechat_app_id"]
        and settings["wechat_mch_id"]
        and settings["wechat_api_v2_key"]
        and (settings["wechat_notify_url"] or default_wechat_notify_url)
    )

    return {
        "totals": {
            "orders": int(order_counts["total_orders"] or 0),
            "orders_pending": int(order_counts["pending_orders"] or 0),
            "orders_paid": int(order_counts["paid_orders"] or 0),
            "tasks": int(task_counts["total_tasks"] or 0),
            "tasks_processing": int(task_counts["processing_tasks"] or 0),
            "tasks_completed": int(task_counts["completed_tasks"] or 0),
            "tasks_failed": int(task_counts["failed_tasks"] or 0),
            "logs": int(log_count["total_logs"] or 0),
        },
        "revenue": {
            "paid_amount_cents": int(order_counts["paid_amount_cents"] or 0),
            "pending_amount_cents": int(order_counts["pending_amount_cents"] or 0),
        },
        "system": {
            "site_base_url": normalized_site_base_url,
            "home_tags_count": len(settings["home_tags"]),
            "system_notice_enabled": bool(str(settings["system_notice"]).strip()),
            "result_retention_days": int(settings["result_retention_days"]),
        },
        "payment": {
            "alipay_enabled": bool(settings["alipay_enabled"]),
            "alipay_configured": alipay_configured,
            "alipay_notify_url": settings["alipay_notify_url"] or default_alipay_notify_url,
            "wechat_enabled": bool(settings["wechat_enabled"]),
            "wechat_configured": wechat_configured,
            "wechat_notify_url": settings["wechat_notify_url"] or default_wechat_notify_url,
        },
        "recent_orders": [dict(row) for row in recent_orders],
        "recent_tasks": [dict(row) for row in recent_tasks],
        "recent_logs": [dict(row) for row in recent_logs],
    }


def get_settings() -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
        raw = {row["key"]: row["value"] for row in rows}
        return _format_settings(raw)


def update_settings(payload: dict[str, Any], admin_user_id: int) -> dict[str, Any]:
    allowed = {key: _serialize_setting_value(key, value) for key, value in payload.items() if value is not None}
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


def list_logs(page: int = 1, page_size: int = 10, keyword: str | None = None) -> dict[str, Any]:
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 10)))
    offset = (page - 1) * page_size
    where_sql, params = _build_keyword_where(
        keyword,
        [
            "l.action",
            "l.target_type",
            "l.target_id",
            "l.detail_json",
            "u.username",
        ],
    )
    with db_session() as conn:
        total = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM operation_logs l
            LEFT JOIN admin_users u ON u.id = l.admin_user_id
            {where_sql}
            """,
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT l.id, l.action, l.target_type, l.target_id, l.detail_json, l.created_at,
                   u.username AS admin_username
            FROM operation_logs l
            LEFT JOIN admin_users u ON u.id = l.admin_user_id
            {where_sql}
            ORDER BY l.id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "page": page, "page_size": page_size}


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
        task = conn.execute("SELECT id, task_no, status, storage_dir FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        storage_dir = task["storage_dir"]

    _delete_task_storage_dir(task_no, storage_dir)

    with db_session() as conn:
        task = conn.execute("SELECT id, task_no FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")

        _delete_task_dependencies(conn, task["id"])
        conn.execute("DELETE FROM task_files WHERE task_id = ?", (task["id"],))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task["id"],))
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, created_at)
            VALUES (?, 'delete_task', 'task', ?, ?)
            """,
            (admin_user_id, task_no, now_iso()),
        )


def delete_task_data_batch(task_nos: list[str], admin_user_id: int) -> dict[str, Any]:
    normalized_task_nos: list[str] = []
    seen: set[str] = set()
    for raw_task_no in task_nos:
        task_no = str(raw_task_no or "").strip()
        if not task_no or task_no in seen:
            continue
        normalized_task_nos.append(task_no)
        seen.add(task_no)

    if not normalized_task_nos:
        raise ValueError("请至少选择一条任务")

    deleted_task_nos: list[str] = []
    for task_no in normalized_task_nos:
        delete_task_data(task_no, admin_user_id)
        deleted_task_nos.append(task_no)

    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, detail_json, created_at)
            VALUES (?, 'batch_delete_task', 'task_batch', ?, ?, ?)
            """,
            (
                admin_user_id,
                f"{len(deleted_task_nos)} tasks",
                json.dumps({"task_nos": deleted_task_nos}, ensure_ascii=False),
                now_iso(),
            ),
        )

    return {
        "requested_count": len(normalized_task_nos),
        "deleted_count": len(deleted_task_nos),
        "task_nos": deleted_task_nos,
    }


def purge_deleted_tasks(admin_user_id: int | None = None) -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT task_no
            FROM tasks
            WHERE status = 'deleted'
            ORDER BY id ASC
            """
        ).fetchall()

    task_nos = [str(row["task_no"]).strip() for row in rows if str(row["task_no"]).strip()]
    purged_task_nos: list[str] = []
    for task_no in task_nos:
        delete_task_data(task_no, admin_user_id)
        purged_task_nos.append(task_no)

    if purged_task_nos:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, detail_json, created_at)
                VALUES (?, 'purge_deleted_tasks', 'task_batch', ?, ?, ?)
                """,
                (
                    admin_user_id,
                    f"{len(purged_task_nos)} tasks",
                    json.dumps({"task_nos": purged_task_nos}, ensure_ascii=False),
                    now_iso(),
                ),
            )

    return {
        "requested_count": len(task_nos),
        "deleted_count": len(purged_task_nos),
        "task_nos": purged_task_nos,
    }


def _delete_task_storage_dir(task_no: str, storage_dir_value: str | None) -> None:
    storage_dir = Path(storage_dir_value).expanduser() if storage_dir_value else task_storage_dir(task_no)
    if not storage_dir.exists():
        return
    if not storage_dir.is_dir():
        raise ValueError("任务存储目录异常，已阻止数据库删除，请检查文件系统状态")
    try:
        shutil.rmtree(storage_dir)
    except OSError as exc:
        raise ValueError(f"任务文件删除失败：{exc}") from exc


def _delete_task_dependencies(conn, task_id: int) -> None:
    conn.execute("DELETE FROM format_results WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task_id,))
    conn.execute("DELETE FROM metadata_results WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task_id,))
    conn.execute("DELETE FROM matched_segments WHERE compare_result_id IN (SELECT id FROM compare_results WHERE task_id = ?)", (task_id,))
    conn.execute("DELETE FROM keyword_hits WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM compare_results WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM orders WHERE task_id = ?", (task_id,))


def _format_settings(raw: dict[str, str]) -> dict[str, Any]:
    return {
        "price_per_b_file_cents": int(raw.get("price_per_b_file_cents", "1000") or 1000),
        "free_b_file_limit": max(1, min(int(raw.get("free_b_file_limit", "1") or 1), 10)),
        "promo_enabled": raw.get("promo_enabled", "false").lower() == "true",
        "promo_price_per_b_file_cents": int(raw.get("promo_price_per_b_file_cents", "100") or 100),
        "promo_ends_at": raw.get("promo_ends_at", ""),
        "promo_note": raw.get("promo_note", ""),
        "promo_badge": raw.get("promo_badge", "限时特惠"),
        "promo_countdown_enabled": raw.get("promo_countdown_enabled", "true").lower() == "true",
        "promo_loss_aversion_text": raw.get("promo_loss_aversion_text", "错过后将恢复原价"),
        "preview_segment_limit": int(raw.get("preview_segment_limit", "3") or 3),
        "result_retention_days": int(raw.get("result_retention_days", "7") or 7),
        "customer_service_wechat": raw.get("customer_service_wechat", ""),
        "customer_service_email": raw.get("customer_service_email", ""),
        "system_notice": raw.get("system_notice", ""),
        "site_base_url": raw.get("site_base_url", ""),
        "site_title": raw.get("site_title", "标书查重系统"),
        "home_tags": _parse_json_list(raw.get("home_tags", "")),
        "threshold_exact": float(raw.get("threshold_exact", "1.0") or 1.0),
        "threshold_rewrite": float(raw.get("threshold_rewrite", "0.82") or 0.82),
        "threshold_semantic": float(raw.get("threshold_semantic", "0.68") or 0.68),
        "alipay_enabled": raw.get("alipay_enabled", "false").lower() == "true",
        "alipay_gateway": raw.get("alipay_gateway", ""),
        "alipay_app_id": raw.get("alipay_app_id", ""),
        "alipay_notify_url": raw.get("alipay_notify_url", ""),
        "alipay_private_key": raw.get("alipay_private_key", ""),
        "alipay_public_key": raw.get("alipay_public_key", ""),
        "wechat_enabled": raw.get("wechat_enabled", "false").lower() == "true",
        "wechat_app_id": raw.get("wechat_app_id", ""),
        "wechat_mch_id": raw.get("wechat_mch_id", ""),
        "wechat_api_v2_key": raw.get("wechat_api_v2_key", ""),
        "wechat_notify_url": raw.get("wechat_notify_url", ""),
    }


def _parse_json_list(value: str) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in value.split(",") if item.strip()]


def _serialize_setting_value(key: str, value: Any) -> str:
    if key == "home_tags":
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            return json.dumps(cleaned, ensure_ascii=False)
        return json.dumps([], ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _build_list_filters(
    exact_filters: list[tuple[str, str | None]],
    keyword: str | None,
    keyword_columns: list[str],
) -> tuple[str, tuple[Any, ...]]:
    clauses: list[str] = []
    params: list[Any] = []

    for clause, value in exact_filters:
        if value:
            clauses.append(clause)
            params.append(value)

    keyword_where, keyword_params = _build_keyword_where(keyword, keyword_columns)
    if keyword_where:
        clauses.append(keyword_where.replace("WHERE ", "", 1))
        params.extend(keyword_params)

    if not clauses:
        return "", tuple()
    return f"WHERE {' AND '.join(clauses)}", tuple(params)


def _build_keyword_where(keyword: str | None, columns: list[str]) -> tuple[str, tuple[Any, ...]]:
    normalized = (keyword or "").strip()
    if not normalized:
        return "", tuple()

    like_value = f"%{normalized}%"
    clauses = [f"COALESCE({column}, '') LIKE ?" for column in columns]
    return f"WHERE ({' OR '.join(clauses)})", tuple(like_value for _ in columns)


def _normalize_datetime_filter(value: str | None, is_end: bool = False) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None

    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)

    if is_end and len(normalized) == 10:
        parsed = parsed.replace(hour=23, minute=59, second=59)
    elif not is_end and len(normalized) == 10:
        parsed = parsed.replace(hour=0, minute=0, second=0)

    return parsed.isoformat(timespec="seconds")

