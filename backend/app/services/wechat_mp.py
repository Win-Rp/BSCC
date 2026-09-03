import base64
import hashlib
import logging
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import httpx

from app.database import db_session
from app.utils.time import now_iso

logger = logging.getLogger("bscc.wechat_mp")

ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
TEMPLATE_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
QRCODE_CREATE_URL = "https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={token}"
QRCODE_SHOW_URL = "https://mp.weixin.qq.com/cgi-bin/showqrcode"

# 临时二维码最长有效期 30 天；缓存时提前 1 天失效，避免边缘时刻拿到已过期的图
QRCODE_EXPIRE_SECONDS = 2592000
QRCODE_CACHE_SAFETY = 86400

# 扫码关注事件中 EventKey 的前缀：未关注用户扫码关注时由微信自动添加
QRSCENE_PREFIX = "qrscene_"

# 服务号 access_token 独立缓存（与小程序 token 互不覆盖）
_mp_token_cache: dict[str, Any] = {"app_id": "", "access_token": "", "expires_at": 0.0}
_mp_token_lock = threading.Lock()

# 二维码 data URL 缓存：{ mini_openid: (data_url, expire_at) }
_mp_qr_cache: dict[str, tuple[str, float]] = {}
_mp_qr_lock = threading.Lock()


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


def extract_scene_openid(event: dict[str, str]) -> str:
    """从扫码事件还原场景值（即小程序 openid）。

    未关注用户扫码关注：Event=subscribe，EventKey 形如 `qrscene_<场景值>`；
    已关注用户扫码：Event=SCAN，EventKey 直接就是场景值，无前缀。
    非扫码途径关注（搜索、名片分享等）时 EventKey 为空，返回空串。
    """
    raw = (event.get("EventKey") or "").strip()
    if not raw:
        return ""
    if raw.startswith(QRSCENE_PREFIX):
        raw = raw[len(QRSCENE_PREFIX):]
    return raw


def handle_callback_event(event: dict[str, str]) -> str:
    msg_type = event.get("MsgType", "")
    if msg_type != "event":
        return "success"

    event_name = event.get("Event", "")
    openid = event.get("FromUserName", "")
    union_id = event.get("UnionID", "")
    if not openid:
        return "success"

    # 扫码类事件携带场景值，据此直接建立两个 openid 的绑定，无需 unionid
    mini_openid = extract_scene_openid(event) if event_name in ("subscribe", "SCAN") else ""

    if event_name == "subscribe":
        upsert_follower(union_id, openid, active=True, mini_openid=mini_openid)
        logger.info("mp follower subscribed openid=%s unionid=%s mini=%s", openid, union_id, mini_openid)
    elif event_name == "unsubscribe":
        # 取关只置为不活跃，保留绑定关系，重新关注后无需再次扫码
        upsert_follower(union_id, openid, active=False)
        logger.info("mp follower unsubscribed openid=%s", openid)
    elif event_name == "SCAN":
        # 已关注用户扫带参二维码进入
        upsert_follower(union_id, openid, active=True, mini_openid=mini_openid)
        logger.info("mp follower scanned openid=%s mini=%s", openid, mini_openid)
    return "success"


def upsert_follower(union_id: str, mp_openid: str, active: bool, mini_openid: str = "") -> None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, union_id, mini_openid FROM mp_followers WHERE mp_openid = ?",
            (mp_openid,),
        ).fetchone()
        if row:
            # 事件未携带时保留已有值，避免被空值覆盖掉历史绑定
            effective_union = union_id or (row["union_id"] or "")
            effective_mini = mini_openid or (row["mini_openid"] or "")
            conn.execute(
                """
                UPDATE mp_followers
                SET union_id = ?, mini_openid = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (effective_union, effective_mini, 1 if active else 0, now_iso(), row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO mp_followers (union_id, mini_openid, mp_openid, is_active, subscribed_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (union_id, mini_openid, mp_openid, 1 if active else 0, now_iso(), now_iso()),
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


def _follower_openid_by_mini(mini_openid: str) -> str:
    """按小程序 openid 查服务号 openid（扫码绑定路径，不依赖 unionid）。"""
    if not mini_openid:
        return ""
    with db_session() as conn:
        row = conn.execute(
            "SELECT mp_openid FROM mp_followers WHERE mini_openid = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
            (mini_openid,),
        ).fetchone()
    return row["mp_openid"] if row else ""


def is_mini_bound(mini_openid: str) -> bool:
    """小程序用户是否已完成扫码关注绑定。"""
    return bool(_follower_openid_by_mini(mini_openid))


def _create_mp_qr_ticket(app_id: str, app_secret: str, scene_str: str) -> tuple[str, int]:
    token = _fetch_mp_access_token(app_id, app_secret)
    payload = {
        "expire_seconds": QRCODE_EXPIRE_SECONDS,
        "action_name": "QR_STR_SCENE",
        "action_info": {"scene": {"scene_str": scene_str}},
    }
    with httpx.Client(timeout=10) as client:
        resp = client.post(QRCODE_CREATE_URL.format(token=token), json=payload)
        resp.raise_for_status()
        data = resp.json()
    if "ticket" not in data:
        raise ValueError(f"MP_QRCODE_FAILED:{data.get('errcode')}:{data.get('errmsg')}")
    return data["ticket"], int(data.get("expire_seconds") or QRCODE_EXPIRE_SECONDS)


def get_mp_qrcode_data_url(mini_openid: str) -> str:
    """生成带场景值的服务号关注二维码，返回可直接用于 <image src> 的 data URL。

    场景值即该用户的小程序 openid。用户扫码关注后，回调事件的 EventKey 会把
    该值原样带回，后端据此直接建立 (小程序 openid, 服务号 openid) 绑定，
    从而绕开对微信开放平台 unionid（300 元/年）的依赖。

    返回图片流而非 ticket 拼 URL，是为了让小程序只请求自有域名，
    无需在小程序后台额外配置 mp.weixin.qq.com 为 downloadFile 合法域名。
    """
    config = get_mp_config()
    if not config["enabled"] or not mini_openid:
        return ""

    now_ts = time.time()
    with _mp_qr_lock:
        cached = _mp_qr_cache.get(mini_openid)
        if cached and now_ts < cached[1]:
            return cached[0]

    try:
        ticket, ttl = _create_mp_qr_ticket(config["app_id"], config["app_secret"], mini_openid)
        with httpx.Client(timeout=15) as client:
            resp = client.get(QRCODE_SHOW_URL, params={"ticket": ticket})
            resp.raise_for_status()
            content = resp.content
        if content[:2] != b"\xff\xd8":
            # ticket 无效时 showqrcode 返回纯文本错误而非图片（JPEG 以 FFD8 开头）
            raise ValueError(f"MP_QRCODE_IMAGE_INVALID:{content[:80]!r}")
        data_url = "data:image/jpeg;base64," + base64.b64encode(content).decode("ascii")
        with _mp_qr_lock:
            _mp_qr_cache[mini_openid] = (data_url, now_ts + max(ttl - QRCODE_CACHE_SAFETY, 3600))
        return data_url
    except Exception as exc:
        logger.warning("mp qrcode generate failed mini_openid=%s err=%s", mini_openid, exc)
        return ""


# 服务号「工单处理结果通知」类目模板（模板编号 53500）字段映射：
# const1=任务名称(枚举值只有"标书查重") time2=开始时间 time3=结束时间
# character_string6=工单编号 const8=当前状态(枚举值"查重完成"/"查重异常")
TASK_NAME_TEXT = "标书查重"
MP_STATUS_TEXT = {
    "completed": "查重完成",
    "awaiting_payment": "查重完成",
    "failed": "查重异常",
}


def _format_time(iso: str) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso[:16].replace("T", " ")


def send_mp_template_message(
    app_id: str,
    app_secret: str,
    template_id: str,
    mp_openid: str,
    task_no: str,
    start_time: str,
    end_time: str,
    status: str,
    mini_app_id: str = "",
    page: str = "pages/results/index",
) -> bool:
    token = _fetch_mp_access_token(app_id, app_secret)
    payload: dict[str, Any] = {
        "touser": mp_openid,
        "template_id": template_id,
        "data": {
            "const1": {"value": TASK_NAME_TEXT},
            "time2": {"value": start_time},
            "time3": {"value": end_time},
            "character_string6": {"value": task_no},
            "const8": {"value": status},
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
            task_no,
            result.get("errcode"),
            result.get("errmsg"),
        )
        return False
    return True


def mp_notify_task_finished(task_no: str, status_key: str) -> bool:
    """服务号模板消息推送（用户已关注且配置完整时生效，强通知无需逐次授权）。"""
    config = get_mp_config()
    if not config["enabled"]:
        return False
    with db_session() as conn:
        row = conn.execute(
            "SELECT notify_openid, notify_unionid, created_at, completed_at FROM tasks WHERE task_no = ?",
            (task_no,),
        ).fetchone()
    if not row:
        return False

    # 优先走扫码建立的直接映射（不依赖 unionid / 开放平台），取不到再回退 unionid
    mp_openid = _follower_openid_by_mini(row["notify_openid"] or "")
    source = "scene"
    if not mp_openid:
        mp_openid = _follower_openid_by_union(row["notify_unionid"] or "")
        source = "unionid"
    if not mp_openid:
        logger.info(
            "mp notify skipped task=%s: 未找到服务号 openid（mini=%s unionid=%s）",
            task_no,
            row["notify_openid"] or "",
            row["notify_unionid"] or "",
        )
        return False
    logger.info("mp notify resolved task=%s via %s", task_no, source)
    try:
        return send_mp_template_message(
            config["app_id"],
            config["app_secret"],
            config["template_id"],
            mp_openid,
            task_no,
            _format_time(row["created_at"]),
            _format_time(row["completed_at"]) or _format_time(now_iso()),
            MP_STATUS_TEXT.get(status_key, "查重完成"),
            mini_app_id=config["mini_app_id"],
            page=f"pages/results/index?taskNo={task_no}",
        )
    except Exception as exc:
        logger.warning("mp_notify_task_finished error task=%s err=%s", task_no, exc)
        return False
