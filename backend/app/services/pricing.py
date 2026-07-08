from __future__ import annotations

import json
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

SUPPORTED_LOCALES = ("zh-CN", "zh-TW", "en", "ja", "ko", "fr", "de")
PROMO_I18N_DEFAULTS: dict[str, dict[str, str]] = {
    "promo_note": {
        "zh-CN": "限时活动，仅限当前批次查重任务",
        "zh-TW": "限時活動，僅限當前批次查重任務",
        "en": "Limited-time offer for the current similarity-check batch only",
        "ja": "期間限定オファー。現在のチェックバッチのみ対象です",
        "ko": "현재 검사 배치에만 적용되는 기간 한정 혜택입니다",
        "fr": "Offre limitée valable uniquement pour ce lot de vérification",
        "de": "Zeitlich begrenztes Angebot nur für die aktuelle Prüfrunde",
    },
    "promo_badge": {
        "zh-CN": "限时特惠",
        "zh-TW": "限時特惠",
        "en": "Limited-time offer",
        "ja": "期間限定特価",
        "ko": "기간 한정 특가",
        "fr": "Offre limitée",
        "de": "Zeitlich begrenztes Angebot",
    },
    "promo_loss_aversion_text": {
        "zh-CN": "错过后将恢复原价",
        "zh-TW": "錯過後將恢復原價",
        "en": "Miss it and the price returns to normal",
        "ja": "この機会を逃すと通常価格に戻ります",
        "ko": "놓치면 정상가로 돌아갑니다",
        "fr": "Une fois l'offre passée, le tarif normal revient",
        "de": "Wenn Sie das Angebot verpassen, gilt wieder der Normalpreis",
    },
}


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


def build_public_pricing_payload(
    raw: dict[str, Any], current_time: datetime | None = None, *, locale: str | None = None
) -> dict[str, Any]:
    pricing = _normalize_pricing(raw, current_time=current_time, locale=locale)
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
    locale: str | None = None,
) -> dict[str, Any]:
    pricing = _normalize_pricing(raw, current_time=current_time, locale=locale)
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
        **build_public_pricing_payload(raw, current_time=current_time, locale=locale),
        "b_file_count": safe_b_file_count,
        "effective_unit_price_cents": actual_unit_price,
        "original_amount_cents": original_amount_cents,
        "effective_amount_cents": actual_amount_cents,
        "savings_cents": savings_cents,
        "discount_percent": discount_percent,
    }


def _normalize_pricing(
    raw: dict[str, Any], current_time: datetime | None = None, *, locale: str | None = None
) -> dict[str, Any]:
    current = current_time or now()
    normalized_locale = _normalize_locale(locale)
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
        "promo_note": _resolve_localized_setting("promo_note", raw.get("promo_note"), normalized_locale),
        "promo_badge": _resolve_localized_setting("promo_badge", raw.get("promo_badge"), normalized_locale),
        "promo_loss_aversion_text": _resolve_localized_setting(
            "promo_loss_aversion_text", raw.get("promo_loss_aversion_text"), normalized_locale
        ),
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


def _normalize_locale(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized.startswith(("zh-tw", "zh-hk", "zh-mo")):
        return "zh-TW"
    if normalized.startswith("zh"):
        return "zh-CN"
    if normalized.startswith("ja"):
        return "ja"
    if normalized.startswith("ko"):
        return "ko"
    if normalized.startswith("fr"):
        return "fr"
    if normalized.startswith("de"):
        return "de"
    return "en"


def _resolve_localized_setting(key: str, value: Any, locale: str) -> str:
    defaults = PROMO_I18N_DEFAULTS.get(key, {})
    raw_text = str(value or "").strip()
    if not raw_text:
        return defaults.get(locale) or defaults.get("en") or ""

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        localized = _pick_localized_text(parsed, locale)
        if localized:
            return localized

    if raw_text == defaults.get("zh-CN"):
        return defaults.get(locale) or defaults.get("en") or raw_text

    return raw_text


def _pick_localized_text(payload: dict[str, Any], locale: str) -> str:
    exact = str(payload.get(locale) or "").strip()
    if exact:
        return exact

    if locale == "zh-TW":
        for alias in ("zh-TW", "zh_HK", "zh-HK", "zh_Hant", "zh-Hant"):
            candidate = str(payload.get(alias) or "").strip()
            if candidate:
                return candidate

    for fallback in ("zh-CN", "en", "zh", "default"):
        candidate = str(payload.get(fallback) or "").strip()
        if candidate:
            return candidate

    for key in SUPPORTED_LOCALES:
        candidate = str(payload.get(key) or "").strip()
        if candidate:
            return candidate

    for candidate in payload.values():
        text = str(candidate or "").strip()
        if text:
            return text
    return ""
