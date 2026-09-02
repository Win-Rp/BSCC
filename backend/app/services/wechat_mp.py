import hashlib
import logging
import threading
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.database import db_session
from app.utils.time import now_iso

logger = logging.getLogger("bscc.wechat_mp")

ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
TEMPLATE_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"

# 服务号 access_token 独立缓存（与小程序 token 互不覆盖）
_mp_token_cache: dict[str, Any] = {"app_id": "", "access_token": "", "expires_at": 0.0}
_mp_token_lock = threading.Lock()


def get_mp_config() -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT key, value FROM settings
            WHERE key IN ('mp_notify_enabled', 'mp_app_id', 'mp_app_secret',
                          'mp_verify_token', 'mp_notify_template_id', 'wechat_mini_app_id')
            """
        ).fetchall()
    settings = {row["key"]: (row["value"] or "") for row in rows}
    app_id = settings.get("mp_app_id", "")
    app_secret = settings.get("mp_app_secret", "")
    template_id = settings.get("mp_notify_template_id", "")
    enabled = settings.get("mp_notify_enabled", "false").lower() == "true"
    return {
        "enabled": enabled and bool(app_id and app_secret and template_id),
        "app_id": app_id,
        "app_secret": app_secret,
        "verify_token": settings.get("mp_verify_token", ""),
        "template_id": template_id,
        "mini_app_id": settings.get("wechat_mini_app_id") or settings.get("wechat_app_id", ""),
    }


def verify_signature(token: str, signature: str, timestamp: str, nonce: str) -> bool:
    if not token or not signature:
        return False
    parts = sorted([token, timestamp, nonce])
    digest = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    return digest == signature


def parse_event_xml(body: str) -> dict[str, str]:
    root = ET.fromstring(body)
    return {child.tag: (child.text or "") for child in root}


def handle_callback_event(event: dict[str, str]) -> str:
    msg_type = event.get("MsgType", "")
    if msg_type != "event":
        return "success"

    event_name = event.get("Event", "")
    openid = event.get("FromUserName", "")
    union_id = event.get("UnionID", "")
    if not openid:
        return "success"

    if event_name == "subscribe":
        upsert_follower(union_id, openid, active=True)
        logger.info("mp follower subscribed openid=%s unionid=%s", openid, union_id)
    elif event_name == "unsubscribe":
        upsert_follower(union_id, openid, active=False)
        logger.info("mp follower unsubscribed openid=%s", openid)
    elif event_name == "SCAN":
        # 已关注用户扫带参二维码进入
        upsert_follower(union_id, openid, active=True)
    return "success"


def upsert_follower(union_id: str, mp_openid: str, active: bool) -> None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, union_id FROM mp_followers WHERE mp_openid = ?",
            (mp_openid,),
        ).fetchone()
        if row:
            # 事件未带 UnionID 时保留已有值
            effective_union = union_id or row["union_id"]
            conn.execute(
                """
                UPDATE mp_followers
                SET union_id = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (effective_union, 1 if active else 0, now_iso(), row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO mp_followers (union_id, mp_openid, is_active, subscribed_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (union_id, mp_openid, 1 if active else 0, now_iso(), now_iso()),
            )


def _fetch_mp_access_token(app_id: str, app_secret: str) -> str:
    with _mp_token_lock:
        now_ts = time.time()
        if (
            _mp_token_cache["access_token"]
            and _mp_token_cache["app_id"] == app_id
            and now_ts < _mp_token_cache["expires_at"] - 120
        ):
            return _mp_token_cache["access_token"]
        params = {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
        with httpx.Client(timeout=10) as client:
            resp = client.get(ACCESS_TOKEN_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        if "access_token" not in data:
            raise ValueError(f"MP_TOKEN_FAILED:{data.get('errcode')}:{data.get('errmsg')}")
        _mp_token_cache["app_id"] = app_id
        _mp_token_cache["access_token"] = data["access_token"]
        _mp_token_cache["expires_at"] = now_ts + int(data.get("expires_in", 7200))
        return _mp_token_cache["access_token"]


def _follower_openid_by_union(union_id: str) -> str:
    if not union_id:
        return ""
    with db_session() as conn:
        row = conn.execute(
            "SELECT mp_openid FROM mp_followers WHERE union_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
            (union_id,),
        ).fetchone()
    return row["mp_openid"] if row else ""


def send_mp_template_message(
    app_id: str,
    app_secret: str,
    template_id: str,
    mp_openid: str,
    service_no: str,
    service_result: str,
    mini_app_id: str = "",
    page: str = "pages/results/index",
) -> bool:
    token = _fetch_mp_access_token(app_id, app_secret)
    payload: dict[str, Any] = {
        "touser": mp_openid,
        "template_id": template_id,
        "data": {
            "first": {"value": "您的查重任务已完成", "color": "#126e6a"},
            "keyword1": {"value": service_no},
            "keyword2": {"value": service_result},
            "remark": {"value": "点击查看详细查重结果"},
        },
    }
    if mini_app_id:
        payload["miniprogram"] = {"appid": mini_app_id, "pagepath": page}
    url = TEMPLATE_SEND_URL.format(token=token)
    with httpx.Client(timeout=10) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        result = resp.json()
    if result.get("errcode") not in (None, 0):
        logger.warning(
            "mp template send failed task=%s errcode=%s errmsg=%s",
            service_no,
            result.get("errcode"),
            result.get("errmsg"),
        )
        return False
    return True


def mp_notify_task_finished(task_no: str, result_text: str) -> bool:
    """服务号模板消息推送（用户已关注且配置完整时生效，强通知无需逐次授权）。"""
    config = get_mp_config()
    if not config["enabled"]:
        return False
    with db_session() as conn:
        row = conn.execute(
            "SELECT notify_unionid FROM tasks WHERE task_no = ?",
            (task_no,),
        ).fetchone()
    if not row or not row["notify_unionid"]:
        return False
    mp_openid = _follower_openid_by_union(row["notify_unionid"])
    if not mp_openid:
        return False
    try:
        return send_mp_template_message(
            config["app_id"],
            config["app_secret"],
            config["template_id"],
            mp_openid,
            task_no,
            result_text,
            mini_app_id=config["mini_app_id"],
            page=f"pages/results/index?taskNo={task_no}",
        )
    except Exception as exc:
        logger.warning("mp_notify_task_finished error task=%s err=%s", task_no, exc)
        return False
