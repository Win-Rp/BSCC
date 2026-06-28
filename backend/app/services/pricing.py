from __future__ import annotations

from datetime import datetime
from typing import Any

from app.utils.time import now, TZ


PRICING_SETTING_KEYS = (
    "price_per_b_file_cents",
    "promo_enabled",
    "promo_price_per_b_file_cents",
    "promo_ends_at",
    "promo_note",
    "promo_badge",
    "promo_countdown_enabled",
    "promo_loss_aversion_text",
)


def load_pricing_settings(conn) -> dict[str, str]:
    rows = conn.execute(
        f"""
        SELECT key, value
        FROM settings
        WHERE key IN ({",".join("?" for _ in PRICING_SETTING_KEYS)})
        """,
        PRICING_SETTING_KEYS,
    ).fetchall()
    return {row["key"]: row["value"] for row in rows}


def build_public_pricing_payload(raw: dict[str, Any], current_time: datetime | None = None) -> dict[str, Any]:
    pricing = _normalize_pricing(raw, current_time=current_time)
    return {
        "original_unit_price_cents": pricing["original_unit_price_cents"],
        "promo_unit_price_cents": pricing["promo_unit_price_cents"],
        "effective_unit_price_cents": pricing["effective_unit_price_cents"],
        "promo_enabled": pricing["promo_enabled"],
        "promo_active": pricing["promo_active"],
        "show_countdown": pricing["show_countdown"],
        "promo_note": pricing["promo_note"],
        "promo_badge": pricing["promo_badge"],
        "promo_loss_aversion_text": pricing["promo_loss_aversion_text"],
        "promo_ends_at": pricing["promo_ends_at"],
        "server_now": pricing["server_now"],
    }


def build_order_pricing_payload(
    raw: dict[str, Any],
    b_file_count: int,
    *,
    effective_unit_price_cents: int | None = None,
    effective_amount_cents: int | None = None,
    current_time: datetime | None = None,
) -> dict[str, Any]:
    pricing = _normalize_pricing(raw, current_time=current_time)
    safe_b_file_count = max(int(b_file_count or 1), 1)
    original_amount_cents = pricing["original_unit_price_cents"] * safe_b_file_count
    actual_unit_price = (
        max(int(effective_unit_price_cents), 1)
        if effective_unit_price_cents is not None
        else pricing["effective_unit_price_cents"]
    )
    actual_amount_cents = (
        max(int(effective_amount_cents), 0)
        if effective_amount_cents is not None
        else actual_unit_price * safe_b_file_count
    )
    savings_cents = max(original_amount_cents - actual_amount_cents, 0)
    discount_percent = round((savings_cents / original_amount_cents) * 100) if original_amount_cents else 0
    return {
        **build_public_pricing_payload(raw, current_time=current_time),
        "b_file_count": safe_b_file_count,
        "effective_unit_price_cents": actual_unit_price,
        "original_amount_cents": original_amount_cents,
        "effective_amount_cents": actual_amount_cents,
        "savings_cents": savings_cents,
        "discount_percent": discount_percent,
    }


def _normalize_pricing(raw: dict[str, Any], current_time: datetime | None = None) -> dict[str, Any]:
    current = current_time or now()
    original_unit_price_cents = max(_to_int(raw.get("price_per_b_file_cents"), 1000), 1)
    promo_unit_price_cents = max(_to_int(raw.get("promo_price_per_b_file_cents"), 100), 1)
    promo_enabled = _to_bool(raw.get("promo_enabled"), False)
    promo_ends_at = str(raw.get("promo_ends_at") or "").strip()
    parsed_promo_end = _parse_datetime(promo_ends_at)
    promo_in_time = not parsed_promo_end or parsed_promo_end > current
    promo_active = (
        promo_enabled
        and promo_unit_price_cents < original_unit_price_cents
        and promo_in_time
    )
    return {
        "original_unit_price_cents": original_unit_price_cents,
        "promo_unit_price_cents": promo_unit_price_cents,
        "effective_unit_price_cents": promo_unit_price_cents if promo_active else original_unit_price_cents,
        "promo_enabled": promo_enabled,
        "promo_active": promo_active,
        "show_countdown": promo_active and _to_bool(raw.get("promo_countdown_enabled"), True) and bool(parsed_promo_end),
        "promo_note": str(raw.get("promo_note") or "").strip(),
        "promo_badge": str(raw.get("promo_badge") or "限时特惠").strip() or "限时特惠",
        "promo_loss_aversion_text": str(raw.get("promo_loss_aversion_text") or "错过后将恢复原价").strip() or "错过后将恢复原价",
        "promo_ends_at": parsed_promo_end.isoformat(timespec="seconds") if parsed_promo_end else "",
        "server_now": current.isoformat(timespec="seconds"),
    }


def _to_int(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return default


def _parse_datetime(value: str) -> datetime | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed
