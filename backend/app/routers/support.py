import json

from fastapi import APIRouter

from app.database import db_session
from app.services.pricing import build_public_pricing_payload
from app.utils.api import ok


router = APIRouter(tags=["support"])


@router.get("/support")
def support():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT key, value FROM settings WHERE key IN ('customer_service_wechat', 'customer_service_email')"
        ).fetchall()
        settings = {row["key"]: row["value"] for row in rows}
    return ok(
        {
            "wechat": settings.get("customer_service_wechat"),
            "email": settings.get("customer_service_email"),
        }
    )


@router.get("/public/site-config")
def public_site_config(locale: str | None = None):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT key, value FROM settings
            WHERE key IN (
                'site_title',
                'home_tags',
                'system_notice',
                'alipay_enabled',
                'wechat_enabled',
                'price_per_b_file_cents',
                'promo_enabled',
                'promo_price_per_b_file_cents',
                'promo_ends_at',
                'promo_note',
                'promo_badge',
                'promo_countdown_enabled',
                'promo_loss_aversion_text',
                'notify_template_id'
            )
            """
        ).fetchall()
        settings = {row["key"]: row["value"] for row in rows}
    return ok(
        {
            "site_title": settings.get("site_title", "标书查重系统"),
            "home_tags": _parse_json_list(settings.get("home_tags", "")),
            "system_notice": settings.get("system_notice", ""),
            "alipay_enabled": str(settings.get("alipay_enabled", "false")).lower() == "true",
            "wechat_enabled": str(settings.get("wechat_enabled", "false")).lower() == "true",
            "notify_template_id": settings.get("notify_template_id", ""),
            "promo": build_public_pricing_payload(settings, locale=locale),
        }
    )


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in str(value).split(",") if item.strip()]
