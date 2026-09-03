import logging
import re
import threading
import time
from typing import Any

import httpx

from app.database import db_session

logger = logging.getLogger("bscc.wechat_notify")

CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SUBSCRIBE_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"
TEMPLATE_LIST_URL = "https://api.weixin.qq.com/wxaapi/newtmpl/gettemplate?access_token={token}"

# 探测失败时的兜底字段（服务编号=character_string1，服务结果=phrase2）
DEFAULT_TEMPLATE_FIELDS = ("character_string1", "phrase2")
_FIELDS_NEGATIVE_TTL = 600.0

# 微信订阅消息各类型关键词的字数上限
_FIELD_LIMITS = (
    ("character_string", 32),
    ("thing", 20),
    ("phrase", 5),
    ("phone_number", 17),
    ("letter", 20),
    ("symbol", 5),
)

_token_cache: dict[str, Any] = {"access_token": "", "expires_at": 0.0}
_token_lock = threading.Lock()
_fields_cache: dict[str, dict[str, Any]] = {}
_fields_lock = threading.Lock()


def get_notify_config() -> dict[str, Any]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT key, value FROM settings
            WHERE key IN ('notify_enabled', 'wechat_app_id', 'wechat_mini_app_id',
                          'wechat_app_secret', 'notify_template_id')
            """
        ).fetchall()
    settings = {row["key"]: (row["value"] or "") for row in rows}
    # code2session 与订阅消息必须使用小程序自身的 AppID；留空则回退到支付配置的 AppID
    app_id = settings.get("wechat_mini_app_id") or settings.get("wechat_app_id", "")
    app_secret = settings.get("wechat_app_secret", "")
    template_id = settings.get("notify_template_id", "")
    enabled = settings.get("notify_enabled", "false").lower() == "true"
    return {
        "enabled": enabled and bool(app_id and app_secret and template_id),
        "app_id": app_id,
        "app_secret": app_secret,
        "template_id": template_id,
    }


def code2session(app_id: str, app_secret: str, js_code: str) -> dict[str, Any]:
    params = {
        "appid": app_id,
        "secret": app_secret,
        "js_code": js_code,
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=10) as client:
        resp = client.get(CODE2SESSION_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    if data.get("errcode") not in (None, 0):
        raise ValueError(f"WX_CODE2SESSION_FAILED:{data.get('errcode')}:{data.get('errmsg')}")
    if not data.get("openid"):
        raise ValueError("WX_CODE2SESSION_FAILED:no openid returned")
    # unionid 仅在小程序绑定微信开放平台后返回，用于关联服务号粉丝
    return {"openid": data["openid"], "session_key": data.get("session_key", ""), "unionid": data.get("unionid", "")}


def _fetch_access_token(app_id: str, app_secret: str) -> str:
    with _token_lock:
        now_ts = time.time()
        if _token_cache["access_token"] and now_ts < _token_cache["expires_at"] - 120:
            return _token_cache["access_token"]
        params = {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
        with httpx.Client(timeout=10) as client:
            resp = client.get(ACCESS_TOKEN_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        if "access_token" not in data:
            raise ValueError(f"WX_TOKEN_FAILED:{data.get('errcode')}:{data.get('errmsg')}")
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now_ts + int(data.get("expires_in", 7200))
        return _token_cache["access_token"]


def _field_limit(field: str) -> int:
    for prefix, limit in _FIELD_LIMITS:
        if field.startswith(prefix):
            return limit
    return 20


def _resolve_template_fields(token: str, template_id: str) -> tuple[str, ...]:
    """通过 gettemplate 接口探测模板真实字段名，避免 character_string1/phrase2 猜错导致 47003。"""
    now_ts = time.time()
    with _fields_lock:
        cached = _fields_cache.get(template_id)
        if cached and (cached["permanent"] or now_ts < cached["expires_at"]):
            return tuple(cached["fields"])

    fields: tuple[str, ...] | None = None
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(TEMPLATE_LIST_URL.format(token=token))
            resp.raise_for_status()
            data = resp.json()
        if data.get("errcode") not in (None, 0):
            raise ValueError(f"{data.get('errcode')}:{data.get('errmsg')}")
        for item in data.get("data") or []:
            if item.get("priTmplId") != template_id:
                continue
            parsed = tuple(re.findall(r"\{\{(\w+)\.DATA\}\}", item.get("content") or ""))
            if parsed:
                fields = parsed
            break
    except Exception as exc:
        logger.warning("resolve template fields failed tmpl=%s err=%s", template_id, exc)

    if fields is None:
        # 探测失败（模板未添加/接口异常）使用兜底映射，短期内不再重复探测
        with _fields_lock:
            _fields_cache[template_id] = {
                "fields": DEFAULT_TEMPLATE_FIELDS,
                "permanent": False,
                "expires_at": time.time() + _FIELDS_NEGATIVE_TTL,
            }
        return DEFAULT_TEMPLATE_FIELDS

    with _fields_lock:
        _fields_cache[template_id] = {"fields": fields, "permanent": True, "expires_at": 0.0}
    logger.info("template fields resolved tmpl=%s fields=%s", template_id, fields)
    return fields


def send_subscribe_message(
    app_id: str,
    app_secret: str,
    template_id: str,
    openid: str,
    service_no: str,
    service_result: str,
    page: str = "pages/results/index",
) -> bool:
    token = _fetch_access_token(app_id, app_secret)
    fields = _resolve_template_fields(token, template_id)
    data: dict[str, Any] = {}
    for field, value in zip(fields, (service_no, service_result)):
        data[field] = {"value": _clip(value, _field_limit(field))}
    payload = {
        "touser": openid,
        "template_id": template_id,
        "page": page,
        "miniprogram_state": "formal",
        "data": data,
    }
    url = SUBSCRIBE_SEND_URL.format(token=token)
    with httpx.Client(timeout=10) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        result = resp.json()
    if result.get("errcode") not in (None, 0):
        logger.warning("subscribe send failed task=%s errcode=%s errmsg=%s", service_no, result.get("errcode"), result.get("errmsg"))
        return False
    return True


def _clip(text: str, limit: int) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    clipped = value[:limit].rstrip("，。！？、,.;；:： ")
    return clipped or value[:limit]


# 小程序订阅消息兜底文案（phrase 服务结果关键词限 5 字）
_RESULT_TEXT = {
    "completed": "查重完成",
    "awaiting_payment": "完成待解锁",
    "failed": "查重异常",
}


def notify_task_finished(task_no: str, status_key: str) -> bool:
    """status_key: completed / awaiting_payment / failed。
    优先服务号模板消息（已关注用户强触达），失败回退小程序订阅消息。"""
    from app.services import wechat_mp

    try:
        if wechat_mp.mp_notify_task_finished(task_no, status_key):
            return True
    except Exception as exc:
        logger.warning("mp notify fallback to subscribe task=%s err=%s", task_no, exc)

    config = get_notify_config()
    if not config["enabled"]:
        logger.warning(
            "notify skipped: config disabled task=%s "
            "(check notify_enabled / wechat_mini_app_id / wechat_app_secret / notify_template_id)",
            task_no,
        )
        return False
    with db_session() as conn:
        row = conn.execute(
            "SELECT notify_openid, notify_authorized_at FROM tasks WHERE task_no = ?",
            (task_no,),
        ).fetchone()
    if not row or not row["notify_openid"]:
        logger.warning("notify skipped: task has no notify_openid task=%s", task_no)
        return False
    try:
        return send_subscribe_message(
            config["app_id"],
            config["app_secret"],
            config["template_id"],
            row["notify_openid"],
            task_no,
            _RESULT_TEXT.get(status_key, "查重完成"),
            page=f"pages/results/index?taskNo={task_no}",
        )
    except Exception as exc:
        logger.warning("notify_task_finished error task=%s err=%s", task_no, exc)
        return False
