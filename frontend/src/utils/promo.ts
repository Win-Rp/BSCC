import type { PromoPricingConfig, PromoPricingSummary } from "@/services/api";

export function formatMoney(cents: number) {
  return `¥${(Number(cents || 0) / 100).toFixed(2)}`;
}

export function buildPromoSummary(
  promo: PromoPricingConfig | null | undefined,
  bFileCount: number
): PromoPricingSummary | null {
  if (!promo) return null;
  const safeCount = Math.max(Number(bFileCount || 0), 1);
  const originalAmountCents = Number(promo.original_unit_price_cents || 0) * safeCount;
  const effectiveAmountCents = Number(promo.effective_unit_price_cents || 0) * safeCount;
  const savingsCents = Math.max(originalAmountCents - effectiveAmountCents, 0);
  const discountPercent = originalAmountCents ? Math.round((savingsCents / originalAmountCents) * 100) : 0;
  return {
    ...promo,
    b_file_count: safeCount,
    original_amount_cents: originalAmountCents,
    effective_amount_cents: effectiveAmountCents,
    savings_cents: savingsCents,
    discount_percent: discountPercent
  };
}

export function buildServerOffsetMs(serverNow: string | null | undefined) {
  const serverTimestamp = Date.parse(serverNow || "");
  return Number.isNaN(serverTimestamp) ? 0 : serverTimestamp - Date.now();
}

export function getRemainingMs(
  promo: Pick<PromoPricingConfig, "promo_ends_at" | "show_countdown"> | null | undefined,
  serverOffsetMs = 0,
  currentClientMs = Date.now()
) {
  if (!promo?.show_countdown || !promo.promo_ends_at) return 0;
  const endTimestamp = Date.parse(promo.promo_ends_at);
  if (Number.isNaN(endTimestamp)) return 0;
  return Math.max(endTimestamp - (currentClientMs + serverOffsetMs), 0);
}

export function formatCountdown(remainingMs: number) {
  const totalSeconds = Math.max(Math.floor(remainingMs / 1000), 0);
  const hours = Math.floor(totalSeconds / 3600).toString().padStart(2, "0");
  const minutes = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}
