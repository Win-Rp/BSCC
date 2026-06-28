import hashlib
import hmac
import os
import secrets
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from dotenv import load_dotenv

from app.database import db_session
from app.utils.site_url import join_base_url, normalize_base_url

load_dotenv()

UNIFIEDORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"
ORDERQUERY_URL = "https://api.mch.weixin.qq.com/pay/orderquery"
CLOSEORDER_URL = "https://api.mch.weixin.qq.com/pay/closeorder"


def get_wechatpay_config() -> dict[str, str | bool]:
    env_base_url = os.getenv("SITE_BASE_URL", "")
    env_enabled = os.getenv("WECHATPAY_ENABLED", "False")
    env_notify_url = os.getenv("WECHATPAY_NOTIFY_URL", "")
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT key, value FROM settings
            WHERE key IN ('site_base_url', 'wechat_enabled', 'wechat_app_id', 'wechat_mch_id', 'wechat_api_v2_key', 'wechat_notify_url')
            """
        ).fetchall()
        settings = {row["key"]: row["value"] for row in rows}

    base_url = normalize_base_url(str(settings.get("site_base_url", "")).strip() or env_base_url)
    notify_url = str(settings.get("wechat_notify_url", "")).strip() or env_notify_url.strip() or join_base_url(base_url, "/api/payments/wechat/notify")

    return {
        "enabled": str(settings.get("wechat_enabled", env_enabled)).lower() == "true",
        "app_id": str(settings.get("wechat_app_id", "")).strip() or str(os.getenv("WECHATPAY_APP_ID", "")).strip(),
        "mch_id": str(settings.get("wechat_mch_id", "")).strip() or str(os.getenv("WECHATPAY_MCH_ID", "")).strip(),
        "api_v2_key": str(settings.get("wechat_api_v2_key", "")).strip() or str(os.getenv("WECHATPAY_API_V2_KEY", "")).strip(),
        "notify_url": notify_url,
    }


def get_wechat_notify_url() -> str:
    config = get_wechatpay_config()
    notify_url = str(config["notify_url"]).strip()
    if not notify_url:
        raise ValueError("缺少微信支付异步通知地址配置")
    return notify_url


def trade_native_precreate(
    out_trade_no: str,
    total_fee: int,
    body: str,
    notify_url: str,
    client_ip: str = "127.0.0.1",
) -> dict[str, Any]:
    config = _require_config()
    payload = {
        "appid": str(config["app_id"]),
        "mch_id": str(config["mch_id"]),
        "nonce_str": _nonce_str(),
        "sign_type": "HMAC-SHA256",
        "body": body[:127],
        "out_trade_no": out_trade_no,
        "total_fee": str(total_fee),
        "spbill_create_ip": client_ip or "127.0.0.1",
        "notify_url": notify_url,
        "trade_type": "NATIVE",
        "product_id": out_trade_no,
    }
    return _call_wechat_api(UNIFIEDORDER_URL, payload)


def trade_query(out_trade_no: str) -> dict[str, Any]:
    config = _require_config()
    payload = {
        "appid": str(config["app_id"]),
        "mch_id": str(config["mch_id"]),
        "nonce_str": _nonce_str(),
        "sign_type": "HMAC-SHA256",
        "out_trade_no": out_trade_no,
    }
    return _call_wechat_api(ORDERQUERY_URL, payload)


def close_order(out_trade_no: str) -> dict[str, Any]:
    config = _require_config()
    payload = {
        "appid": str(config["app_id"]),
        "mch_id": str(config["mch_id"]),
        "nonce_str": _nonce_str(),
        "sign_type": "HMAC-SHA256",
        "out_trade_no": out_trade_no,
    }
    return _call_wechat_api(CLOSEORDER_URL, payload)


def parse_xml(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
    data: dict[str, str] = {}
    for child in root:
        data[child.tag] = (child.text or "").strip()
    return data


def check_notify_sign(data: dict[str, str]) -> bool:
    config = get_wechatpay_config()
    api_v2_key = str(config["api_v2_key"]).strip()
    if not api_v2_key:
        return False
    sign = data.get("sign", "")
    if not sign:
        return False
    sign_type = data.get("sign_type", "HMAC-SHA256")
    expected = generate_sign(data, api_v2_key, sign_type)
    return sign.upper() == expected.upper()


def notify_success_xml() -> str:
    return "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"


def notify_fail_xml(message: str = "FAIL") -> str:
    return f"<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[{message}]]></return_msg></xml>"


def generate_sign(data: dict[str, Any], api_v2_key: str, sign_type: str = "HMAC-SHA256") -> str:
    pairs = []
    for key in sorted(data.keys()):
        value = data[key]
        if key == "sign" or value is None:
            continue
        normalized = str(value).strip()
        if normalized == "":
            continue
        pairs.append(f"{key}={normalized}")
    sign_payload = "&".join(pairs) + f"&key={api_v2_key}"
    if sign_type.upper() == "MD5":
        return hashlib.md5(sign_payload.encode("utf-8")).hexdigest().upper()
    return hmac.new(api_v2_key.encode("utf-8"), sign_payload.encode("utf-8"), hashlib.sha256).hexdigest().upper()


def _require_config() -> dict[str, str | bool]:
    config = get_wechatpay_config()
    if not config["enabled"]:
        raise ValueError("后台未启用微信支付配置")
    if not config["app_id"] or not config["mch_id"] or not config["api_v2_key"]:
        raise ValueError("缺少微信支付配置项: AppID、商户号或 APIv2 Key")
    return config


def _call_wechat_api(url: str, payload: dict[str, str]) -> dict[str, Any]:
    config = _require_config()
    sign_type = payload.get("sign_type", "HMAC-SHA256")
    payload["sign"] = generate_sign(payload, str(config["api_v2_key"]), sign_type)
    xml_payload = _dict_to_xml(payload)

    with httpx.Client(timeout=15.0) as client:
        response = client.post(url, content=xml_payload.encode("utf-8"), headers={"Content-Type": "text/xml; charset=utf-8"})
        response.raise_for_status()

    parsed = parse_xml(response.text)
    if parsed.get("return_code") != "SUCCESS":
        raise ValueError(parsed.get("return_msg") or "微信支付通信失败")
    if parsed.get("sign") and not check_notify_sign(parsed):
        raise ValueError("微信支付返回签名校验失败")
    if parsed.get("result_code") != "SUCCESS":
        raise ValueError(parsed.get("err_code_des") or parsed.get("err_code") or "微信支付业务处理失败")
    return parsed


def _dict_to_xml(data: dict[str, Any]) -> str:
    items = ["<xml>"]
    for key, value in data.items():
        items.append(f"<{key}><![CDATA[{value}]]></{key}>")
    items.append("</xml>")
    return "".join(items)


def _nonce_str() -> str:
    return secrets.token_hex(16).upper()
