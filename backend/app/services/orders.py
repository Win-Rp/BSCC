from datetime import datetime, timedelta
from typing import Any

from app.database import db_session
from app.services.alipay_service import get_alipay_config
from app.services.pricing import build_order_pricing_payload, load_pricing_settings
from app.services.tasks import make_no
from app.utils.time import now, now_iso
from app.services.alipay_service import (
    get_alipay_notify_url,
    trade_precreate,
    trade_query,
    trade_refund,
    trade_refund_query,
)
from app.services.wechatpay_service import (
    close_order as wechat_close_order,
    get_wechatpay_config,
    get_wechat_notify_url,
    trade_native_precreate,
    trade_query as wechat_trade_query,
)


def create_order(task_no: str, contact: str, pay_channel: str = "alipay", client_ip: str = "127.0.0.1") -> dict[str, Any]:
    if not contact.strip():
        raise ValueError("VALIDATION_ERROR")
    pay_channel = (pay_channel or "alipay").strip().lower()
    if pay_channel not in {"alipay", "wechat"}:
        raise ValueError("UNSUPPORTED_PAY_CHANNEL")
    if pay_channel == "wechat" and not bool(get_wechatpay_config()["enabled"]):
        raise ValueError("PAY_CHANNEL_DISABLED")
    if pay_channel == "alipay" and not bool(get_alipay_config()["enabled"]):
        raise ValueError("PAY_CHANNEL_DISABLED")
    with db_session() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise ValueError("TASK_NOT_FOUND")
        if task["mode"] != "multi":
            raise ValueError("VALIDATION_ERROR")
        pricing_settings = load_pricing_settings(conn)
        existing_paid = conn.execute(
            "SELECT * FROM orders WHERE task_id = ? AND status = 'paid' ORDER BY id DESC LIMIT 1",
            (task["id"],),
        ).fetchone()
        if existing_paid:
            return _order_payload(existing_paid, task, pricing_settings)

        pending_orders = conn.execute(
            "SELECT order_no, pay_channel, created_at FROM orders WHERE task_id = ? AND status = 'pending'",
            (task["id"],),
        ).fetchall()
        if pending_orders:
            for pending_order in pending_orders:
                _best_effort_close_remote_order(pending_order)
            conn.execute(
                """
                UPDATE orders
                SET status = 'closed', closed_at = ?, error_message = ?, updated_at = ?
                WHERE task_id = ? AND status = 'pending'
                """,
                (now_iso(), "用户重新生成支付二维码，旧订单已自动关闭", now_iso(), task["id"]),
            )
        pricing_payload = build_order_pricing_payload(pricing_settings, task["b_file_count"])
        unit_price = pricing_payload["effective_unit_price_cents"]
        amount = pricing_payload["effective_amount_cents"]
        amount_yuan = amount / 100.0
        order_no = make_no("O")
        order_error_message = None
        try:
            if pay_channel == "wechat":
                wechat_res = trade_native_precreate(
                    out_trade_no=order_no,
                    total_fee=amount,
                    body=f"BSCC标书查重解锁-{task_no}",
                    notify_url=get_wechat_notify_url(),
                    client_ip=client_ip or "127.0.0.1",
                )
                qr_code_url = wechat_res.get("code_url")
                if not qr_code_url:
                    order_error_message = "微信支付未返回可用的扫码串，请检查商户配置"
            else:
                alipay_res = trade_precreate(
                    out_trade_no=order_no,
                    total_amount=amount_yuan,
                    subject=f"BSCC标书查重解锁-{task_no}",
                    notify_url=get_alipay_notify_url()
                )
                qr_code_url = alipay_res.get("qr_code")
                if not qr_code_url:
                    order_error_message = "支付宝未返回可用的扫码串，请检查应用配置"
        except Exception as e:
            print(f"{pay_channel} 预下单失败: {e}")
            qr_code_url = None
            pay_label = "微信支付" if pay_channel == "wechat" else "支付宝"
            order_error_message = f"{pay_label}预下单失败：{e}"

        conn.execute(
            """
            INSERT INTO orders (
              order_no, task_id, contact, status, b_file_count, unit_price_cents, amount_cents,
              pay_channel, qr_code_url, error_message, created_at, updated_at
            )
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_no,
                task["id"],
                contact,
                task["b_file_count"],
                unit_price,
                amount,
                pay_channel,
                qr_code_url,
                order_error_message,
                now_iso(),
                now_iso(),
            ),
        )
        conn.execute("UPDATE tasks SET contact = ?, updated_at = ? WHERE id = ?", (contact, now_iso(), task["id"]))
        order = conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
        return _order_payload(order, task, pricing_settings)


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
            
        # 如果订单是待支付状态，尝试主动查询第三方支付最新状态
        if row["status"] == "pending":
            try:
                if row["pay_channel"] == "wechat":
                    wechat_res = wechat_trade_query(order_no)
                    if wechat_res.get("trade_state") == "SUCCESS":
                        return mark_order_paid(order_no)
                else:
                    alipay_res = trade_query(order_no)
                    trade_status = alipay_res.get("trade_status")
                    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
                        return mark_order_paid(order_no)
            except Exception:
                pass

        return {
            "order_no": row["order_no"],
            "task_no": row["task_no"],
            "status": row["status"],
            "unlock_status": row["unlock_status"],
            "paid_at": row["paid_at"],
            "pay_channel": row["pay_channel"],
        }


def mark_order_paid(order_no: str, admin_user_id: int | None = None) -> dict[str, Any]:
    with db_session() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
        if not order:
            raise ValueError("ORDER_NOT_FOUND")
        if order["status"] == "paid":
            # 已经支付过，直接返回状态（幂等）
            return get_order_status(order_no)
            
        conn.execute(
            "UPDATE orders SET status = 'paid', paid_at = ?, error_message = NULL, updated_at = ? WHERE id = ?",
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


def _order_payload(order, task, pricing_settings: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_no": order["order_no"],
        "task_no": task["task_no"],
        "amount_cents": order["amount_cents"],
        "b_file_count": order["b_file_count"],
        "qr_code_url": order["qr_code_url"],
        "payment_message": order["error_message"],
        "status": order["status"],
        "pay_channel": order["pay_channel"],
        "pricing": build_order_pricing_payload(
            pricing_settings,
            order["b_file_count"],
            effective_unit_price_cents=order["unit_price_cents"],
            effective_amount_cents=order["amount_cents"],
        ),
    }


def _best_effort_close_remote_order(order) -> None:
    if order["pay_channel"] != "wechat":
        return

    created_at = str(order["created_at"] or "").strip()
    if not created_at:
        return

    try:
        created_time = datetime.fromisoformat(created_at)
    except ValueError:
        return

    # 兼容历史数据中不带时区的时间串，统一补齐为当前系统时区。
    current_time = now()
    if created_time.tzinfo is None:
        created_time = created_time.replace(tzinfo=current_time.tzinfo)

    if current_time - created_time < timedelta(minutes=5):
        return

    try:
        wechat_close_order(order["order_no"])
    except Exception:
        pass
