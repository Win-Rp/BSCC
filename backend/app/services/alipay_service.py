import os
from alipay import AliPay
from alipay.utils import AliPayConfig
from dotenv import load_dotenv

from app.database import db_session
from app.utils.site_url import join_base_url, normalize_base_url

load_dotenv()


def get_alipay_config() -> dict[str, str | bool]:
    env_base_url = os.getenv("SITE_BASE_URL", "")
    env_notify_url = os.getenv("ALIPAY_NOTIFY_URL", "")
    env_gateway = os.getenv("ALIPAY_GATEWAY", "")

    settings = {
        "site_base_url": env_base_url,
        "alipay_enabled": os.getenv("ALIPAY_ENABLED", "false"),
        "alipay_gateway": env_gateway,
        "alipay_app_id": os.getenv("ALIPAY_APP_ID", ""),
        "alipay_notify_url": env_notify_url,
        "alipay_private_key": os.getenv("ALIPAY_PRIVATE_KEY", ""),
        "alipay_public_key": os.getenv("ALIPAY_PUBLIC_KEY", ""),
    }

    try:
        with db_session() as conn:
            rows = conn.execute(
                """
                SELECT key, value FROM settings
                WHERE key IN (
                    'site_base_url',
                    'alipay_enabled', 'alipay_gateway', 'alipay_app_id',
                    'alipay_notify_url', 'alipay_private_key', 'alipay_public_key'
                )
                """
            ).fetchall()
            for row in rows:
                settings[row["key"]] = row["value"]
    except Exception:
        # 数据库尚未初始化时回退到 .env 配置
        pass

    gateway = str(settings["alipay_gateway"] or env_gateway).strip()
    gateway_lower = gateway.lower()
    debug_enabled = "sandbox" in gateway_lower or "alipaydev.com" in gateway_lower
    base_url = normalize_base_url(str(settings.get("site_base_url", "") or env_base_url))
    notify_url = str(settings["alipay_notify_url"]).strip() or env_notify_url.strip() or join_base_url(base_url, "/api/payments/alipay/notify")

    return {
        "enabled": str(settings["alipay_enabled"]).lower() == "true",
        "debug": debug_enabled,
        "gateway": gateway,
        "app_id": str(settings["alipay_app_id"]),
        "notify_url": notify_url,
        "private_key": _normalize_key(str(settings["alipay_private_key"]), "private"),
        "public_key": _normalize_key(str(settings["alipay_public_key"]), "public"),
    }

def get_alipay_client() -> AliPay:
    """初始化并获取 Alipay 客户端"""
    config = get_alipay_config()
    if not config["enabled"]:
        raise ValueError("后台未启用支付宝支付配置")
    if not config["gateway"]:
        raise ValueError("缺少支付宝网关配置")
    if not config["app_id"] or not config["private_key"] or not config["public_key"]:
        raise ValueError("缺少支付宝配置项: app_id、应用私钥或支付宝公钥")

    alipay_client = AliPay(
        appid=config["app_id"],
        app_notify_url=None,
        app_private_key_string=config["private_key"],
        alipay_public_key_string=config["public_key"],
        debug=bool(config["debug"]),  # 仅用于兼容 SDK 的沙箱行为，实际请求网关以显式 gateway 为准
        sign_type="RSA2",
        config=AliPayConfig(timeout=15)
    )
    # 强制使用显式网关，避免再依赖“运行环境”开关做自动切换。
    alipay_client._gateway = str(config["gateway"])
    return alipay_client


def trade_precreate(out_trade_no: str, total_amount: float, subject: str, notify_url: str) -> dict:
    """
    扫码支付：生成二维码
    """
    alipay = get_alipay_client()
    result = alipay.api_alipay_trade_precreate(
        subject=subject,
        out_trade_no=out_trade_no,
        total_amount=f"{total_amount:.2f}",
        notify_url=notify_url
    )
    return result

def trade_query(out_trade_no: str) -> dict:
    """
    查询订单状态
    """
    alipay = get_alipay_client()
    result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
    return result

def trade_refund(out_trade_no: str, refund_amount: float, out_request_no: str) -> dict:
    """
    退款
    """
    alipay = get_alipay_client()
    result = alipay.api_alipay_trade_refund(
        out_trade_no=out_trade_no,
        refund_amount=f"{refund_amount:.2f}",
        out_request_no=out_request_no
    )
    return result

def trade_refund_query(out_trade_no: str, out_request_no: str) -> dict:
    """
    查询退款状态
    """
    alipay = get_alipay_client()
    result = alipay.api_alipay_trade_fastpay_refund_query(
        out_trade_no=out_trade_no,
        out_request_no=out_request_no
    )
    return result

def check_notify_sign(data: dict) -> bool:
    """
    校验异步通知的签名
    """
    alipay = get_alipay_client()
    signature = data.pop("sign")
    # sign_type 通常不需要参与验签，但在 python-alipay-sdk 中 pop 出 sign 即可
    sign_type = data.pop("sign_type", "RSA2")
    success = alipay.verify(data, signature)
    return success


def get_alipay_notify_url() -> str:
    return str(get_alipay_config()["notify_url"])


def _normalize_key(value: str, key_type: str) -> str:
    normalized = value.replace("\\n", "\n").strip()
    if not normalized:
        return normalized

    upper_value = normalized.upper()
    if "BEGIN " in upper_value and "END " in upper_value:
        return normalized

    if key_type == "private":
        begin_marker = "-----BEGIN PRIVATE KEY-----"
        end_marker = "-----END PRIVATE KEY-----"
    else:
        begin_marker = "-----BEGIN PUBLIC KEY-----"
        end_marker = "-----END PUBLIC KEY-----"

    body = "".join(line.strip() for line in normalized.splitlines() if line.strip())
    wrapped = "\n".join(body[index:index + 64] for index in range(0, len(body), 64))
    return f"{begin_marker}\n{wrapped}\n{end_marker}"
