from typing import Any

from app.database import db_session
from app.services.tasks import make_no
from app.utils.time import now_iso


def create_order(task_no: str, contact: str) -> dict[str, Any]:
    if not contact.strip():
        raise ValueError("VALIDATION_ERROR")
    with db_session() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        if task["mode"] != "multi":
            raise ValueError("VALIDATION_ERROR")
        existing = conn.execute("SELECT * FROM orders WHERE task_id = ? ORDER BY id DESC LIMIT 1", (task["id"],)).fetchone()
        if existing and existing["status"] != "closed":
            return _order_payload(existing, task)
        unit_price = int(_setting(conn, "price_per_b_file_cents", "1000"))
        amount = unit_price * task["b_file_count"]
        order_no = make_no("O")
        qr_code_url = f"https://example.com/alipay/qrcode/{order_no}"
        conn.execute(
            """
            INSERT INTO orders (
              order_no, task_id, contact, status, b_file_count, unit_price_cents, amount_cents,
              qr_code_url, created_at, updated_at
            )
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
            """,
            (
                order_no,
                task["id"],
                contact,
                task["b_file_count"],
                unit_price,
                amount,
                qr_code_url,
                now_iso(),
                now_iso(),
            ),
        )
        conn.execute("UPDATE tasks SET contact = ?, updated_at = ? WHERE id = ?", (contact, now_iso(), task["id"]))
        order = conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
        return _order_payload(order, task)


def get_order_status(order_no: str) -> dict[str, Any]:
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT o.*, t.task_no, t.unlock_status
            FROM orders o JOIN tasks t ON t.id = o.task_id
            WHERE o.order_no = ?
            """,
            (order_no,),
        ).fetchone()
        if not row:
            raise ValueError("ORDER_NOT_FOUND")
        return {
            "order_no": row["order_no"],
            "task_no": row["task_no"],
            "status": row["status"],
            "unlock_status": row["unlock_status"],
            "paid_at": row["paid_at"],
        }


def mark_order_paid(order_no: str, admin_user_id: int | None = None) -> dict[str, Any]:
    with db_session() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
        if not order:
            raise ValueError("ORDER_NOT_FOUND")
        conn.execute(
            "UPDATE orders SET status = 'paid', paid_at = ?, updated_at = ? WHERE id = ?",
            (now_iso(), now_iso(), order["id"]),
        )
        conn.execute(
            "UPDATE tasks SET unlock_status = 'unlocked', status = 'completed', updated_at = ? WHERE id = ?",
            (now_iso(), order["task_id"]),
        )
        conn.execute(
            """
            INSERT INTO operation_logs (admin_user_id, action, target_type, target_id, detail_json, created_at)
            VALUES (?, 'mark_paid', 'order', ?, NULL, ?)
            """,
            (admin_user_id, order_no, now_iso()),
        )
    return get_order_status(order_no)


def _order_payload(order, task) -> dict[str, Any]:
    return {
        "order_no": order["order_no"],
        "task_no": task["task_no"],
        "amount_cents": order["amount_cents"],
        "b_file_count": order["b_file_count"],
        "qr_code_url": order["qr_code_url"],
        "status": order["status"],
    }


def _setting(conn, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default
