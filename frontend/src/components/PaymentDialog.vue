<template>
  <el-dialog
    v-model="visible"
    :width="dialogWidth"
    class="payment-dialog"
    modal-class="payment-dialog-overlay"
    append-to-body
    destroy-on-close
    align-center
    :close-on-click-modal="!creating && !paying"
  >
    <template #header>
      <div class="payment-dialog__header">
        <div class="payment-dialog__eyebrow">{{ hasPromo ? promoBadgeText : "结果解锁窗口" }}</div>
        <h2>{{ hasPromo ? "现在锁定优惠更划算，完整详情一次看透" : "确认解锁完整详情" }}</h2>
        <p v-if="hasPromo">
          当前活动价 <strong>{{ displayUnitPrice }} / 每份对比文件</strong>，原价
          <span class="payment-dialog__origin">{{ displayOriginalUnitPrice }}</span>，
          现在解锁可立省 {{ promoDiscountText }}。
        </p>
        <p v-else>
          当前按 <strong>{{ displayUnitPrice }} / 每份对比文件</strong> 结算，支付后立即开放完整重复片段、格式相似项、元数据对比与关键字命中。
        </p>
      </div>
    </template>

    <div class="payment-layout" :class="{ 'payment-layout--checkout': !!order }">
      <div class="payment-layout__main">
        <section class="payment-hero">
          <div class="payment-hero__main">
            <div class="payment-hero__flag">{{ hasPromo ? promoBadgeText : "完整解锁" }}</div>
            <div class="payment-hero__price">
              <div class="payment-hero__price-stack">
                <div v-if="hasPromo" class="payment-hero__origin-price">{{ displayOriginalUnitPrice }}</div>
                <strong>{{ displayUnitPrice }}</strong>
              </div>
              <span>/ 每份 B 文件</span>
            </div>
            <p>
              {{ promoNoteText }}
            </p>
            <div v-if="hasPromo" class="payment-hero__promo-meta">
              <div class="payment-hero__save">本次可节省 {{ savingsAmountText }}</div>
              <div class="payment-hero__loss">{{ promoLossAversionText }}</div>
              <div v-if="promoSummary?.show_countdown" class="payment-hero__countdown">
                <span>距优惠结束仅剩</span>
                <strong>{{ countdownText }}</strong>
              </div>
            </div>
          </div>

          <div class="payment-summary-grid">
            <article class="payment-summary-card">
              <span>任务号</span>
              <strong>{{ taskNo || "-" }}</strong>
            </article>
            <article class="payment-summary-card">
              <span>当前状态</span>
              <strong>{{ statusText }}</strong>
            </article>
            <article class="payment-summary-card">
              <span>解锁范围</span>
              <strong>{{ order?.b_file_count ?? "全部" }} 份对比文件</strong>
            </article>
            <article class="payment-summary-card">
              <span>预计金额</span>
              <strong>{{ estimatedAmountText }}</strong>
            </article>
            <article v-if="hasPromo" class="payment-summary-card">
              <span>原价总额</span>
              <strong>{{ originalAmountText }}</strong>
            </article>
            <article v-if="hasPromo" class="payment-summary-card">
              <span>本次立省</span>
              <strong>{{ savingsAmountText }}</strong>
            </article>
          </div>
        </section>

        <section class="payment-benefits">
          <div class="payment-benefits__item">完整重复片段定位</div>
          <div class="payment-benefits__item">格式相似项明细</div>
          <div class="payment-benefits__item">元数据对比结果</div>
          <div class="payment-benefits__item">关键字命中详情</div>
        </section>

        <section class="payment-channel-panel">
          <div class="payment-channel-panel__head">
            <strong>支付方式</strong>
            <span>{{ channelHintText }}</span>
          </div>
          <div class="payment-channel-switch">
            <button
              type="button"
              class="payment-channel-option"
              :class="{ 'is-active': selectedChannel === 'alipay' }"
              :disabled="!paymentAvailability.alipay"
              @click="selectedChannel = 'alipay'"
            >
              支付宝
            </button>
            <button
              type="button"
              class="payment-channel-option"
              :class="{ 'is-active': selectedChannel === 'wechat' }"
              :disabled="!paymentAvailability.wechat"
              @click="selectedChannel = 'wechat'"
            >
              微信支付
            </button>
          </div>
        </section>

        <el-form label-position="top" class="payment-form">
          <el-form-item label="联系方式">
            <el-input
              v-model="contact"
              placeholder="邮箱 / 手机号 / 微信号"
              maxlength="64"
            />
          </el-form-item>
        </el-form>

        <section class="payment-order-panel">
          <div class="payment-order-panel__head">
            <strong>{{ order ? "待支付订单已生成" : "尚未生成支付订单" }}</strong>
            <el-tag :type="orderStatusTagType">{{ orderStatusLabel }}</el-tag>
          </div>

          <div v-if="order" class="payment-order-list">
            <div><span>订单号</span><strong>{{ order.order_no }}</strong></div>
            <div><span>文件份数</span><strong>{{ order.b_file_count }} 份</strong></div>
            <div><span>订单金额</span><strong>{{ formatMoney(order.amount_cents) }}</strong></div>
            <div v-if="hasPromo"><span>原价总额</span><strong>{{ originalAmountText }}</strong></div>
            <div v-if="hasPromo"><span>本次优惠</span><strong>立省 {{ savingsAmountText }}</strong></div>
            <div><span>联系方式</span><strong>{{ contact || "-" }}</strong></div>
          </div>
          <div v-else class="payment-empty-state">
            填写联系方式后即可锁定当前优惠价并生成支付订单。
          </div>
        </section>
      </div>

      <aside class="payment-layout__aside">
        <section class="payment-qr-panel">
          <div v-if="order?.payment_message" class="payment-status-banner payment-status-banner--error">
            <strong>当前失败原因</strong>
            <span>{{ order.payment_message }}</span>
          </div>

          <div v-if="qrCodeDataUrl" class="payment-qr-panel__content">
            <div class="payment-qr-panel__image-wrap">
              <div class="payment-qr-panel__brand" :class="`payment-qr-panel__brand--${currentPayChannel}`">
                <span class="payment-qr-panel__brand-dot" :class="`payment-qr-panel__brand-dot--${currentPayChannel}`"></span>
                {{ payChannelLabel }}扫码支付
              </div>
              <img :src="qrCodeDataUrl" :alt="`${payChannelLabel}支付二维码`" class="payment-qr-panel__image" />
              <div class="payment-qr-panel__scan-line"></div>
              <div class="payment-qr-panel__caption">请打开{{ scanAppText }}完成付款</div>
            </div>
            <div class="payment-qr-panel__tips">
              <strong>扫码完成支付后，系统会自动为你解锁完整详情</strong>
              <span>无需手动刷新页面，支付成功后会自动轮询订单状态，并立即开放全部对比结果。</span>
              <div class="payment-qr-panel__steps">
                <div>1. 打开{{ scanAppText }}</div>
                <div>2. 扫码并确认支付金额</div>
                <div>3. 等待当前窗口自动完成解锁</div>
              </div>
            </div>
          </div>
          <div v-else-if="order" class="payment-qr-panel__error-card">
            <div class="payment-qr-panel__error-icon">!</div>
            <div class="payment-qr-panel__error-body">
              <strong>{{ payChannelLabel }}二维码生成失败</strong>
              <span>{{ order.payment_message || "当前订单尚未返回可用二维码，请检查支付配置或重新生成订单。" }}</span>
              <div class="payment-qr-panel__error-hints">
                <div>{{ primaryErrorHint }}</div>
                <div>{{ secondaryErrorHint }}</div>
              </div>
            </div>
          </div>
          <div v-else class="payment-qr-panel__placeholder">
            <strong>等待生成支付二维码</strong>
            <span>先锁定优惠并创建订单，生成后这里会直接显示可扫码的{{ payChannelLabel }}二维码。</span>
          </div>
        </section>
      </aside>
    </div>

    <template #footer>
      <div class="payment-footer">
        <el-button class="payment-footer__ghost" @click="visible = false">我再想想</el-button>
        <el-button
          v-if="!order"
          type="danger"
          class="payment-footer__primary"
          :loading="creating"
          @click="handleCreateOrder"
        >
          {{ hasPromo ? `锁定优惠并生成${payChannelLabel}订单` : `生成${payChannelLabel}订单` }}
        </el-button>
        <template v-else>
          <el-button class="payment-footer__ghost" :loading="checking" @click="checkPaymentStatus">刷新支付状态</el-button>
          <el-button class="payment-footer__ghost" :loading="creating" @click="handleRegenerateOrder">
            重新生成新二维码
          </el-button>
          <el-button type="danger" class="payment-footer__primary" :loading="paying" @click="handlePaid">
            我已完成支付，立即校验
          </el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import QRCode from "qrcode";
import {
  createOrder,
  getOrderStatus,
  getPublicSiteConfig,
  type OrderInfo,
  type OrderStatus,
  type PromoPricingSummary,
  type PublicSiteConfig
} from "@/services/api";
import { saveOrderNo } from "@/services/session";
import { buildPromoSummary, buildServerOffsetMs, formatCountdown, formatMoney, getRemainingMs } from "@/utils/promo";

const props = defineProps<{ modelValue: boolean; taskNo: string; bFileCount?: number }>();
const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  paid: [];
}>();

const contact = ref("");
const creating = ref(false);
const checking = ref(false);
const paying = ref(false);
const order = ref<OrderInfo | null>(null);
const orderStatus = ref<OrderStatus | null>(null);
const siteConfig = ref<PublicSiteConfig | null>(null);
const qrCodeDataUrl = ref("");
const selectedChannel = ref<"alipay" | "wechat">("alipay");
const paymentAvailability = ref({ alipay: true, wechat: false });
let pollTimer: number | undefined;
let countdownTimer: number | undefined;
const countdownNow = ref(Date.now());

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit("update:modelValue", value)
});

const dialogWidth = computed(() => (order.value ? "980px" : "640px"));
const taskNo = computed(() => props.taskNo);
const currentPayChannel = computed(() => order.value?.pay_channel ?? selectedChannel.value);
const payChannelLabel = computed(() => currentPayChannel.value === "wechat" ? "微信支付" : "支付宝");
const scanAppText = computed(() => currentPayChannel.value === "wechat" ? "微信扫一扫" : "支付宝扫一扫");
const channelHintText = computed(() => {
  if (paymentAvailability.value.alipay && paymentAvailability.value.wechat) {
    return "支持支付宝与微信 Native 扫码";
  }
  if (paymentAvailability.value.wechat) return "当前仅启用微信 Native 扫码支付";
  return "当前仅启用支付宝扫码支付";
});
const primaryErrorHint = computed(() => {
  if (currentPayChannel.value === "wechat") {
    return "请优先检查：AppID、商户号、APIv2 Key、异步通知地址";
  }
  return "请优先检查：App ID、应用私钥、支付宝公钥、异步通知地址";
});
const secondaryErrorHint = computed(() => {
  if (currentPayChannel.value === "wechat") {
    return "如果刚修改过微信配置，建议重新生成订单获取新的 code_url";
  }
  return "如果刚修改过支付宝配置，建议重新生成订单以获取新的扫码串";
});
const statusText = computed(() => {
  if (!order.value) return "待创建";
  if (orderStatus.value?.status === "paid") return "已支付";
  return "待支付";
});
const orderStatusLabel = computed(() => {
  if (!order.value) return "未生成";
  return orderStatus.value?.status === "paid" ? "已支付" : "待支付";
});
const orderStatusTagType = computed(() => {
  if (!order.value) return "info";
  return orderStatus.value?.status === "paid" ? "success" : "warning";
});
const promoSummary = computed<PromoPricingSummary | null>(() => {
  if (order.value?.pricing) return order.value.pricing;
  return buildPromoSummary(siteConfig.value?.promo, props.bFileCount || 1);
});
const hasPromo = computed(() => Boolean(promoSummary.value && (promoSummary.value.promo_active || promoSummary.value.savings_cents > 0)));
const displayUnitPrice = computed(() => promoSummary.value ? formatMoney(promoSummary.value.effective_unit_price_cents) : "待计算");
const displayOriginalUnitPrice = computed(() => promoSummary.value ? formatMoney(promoSummary.value.original_unit_price_cents) : "待计算");
const estimatedAmountText = computed(() => {
  if (!promoSummary.value) return "生成订单后显示";
  return formatMoney(order.value?.amount_cents ?? promoSummary.value.effective_amount_cents);
});
const originalAmountText = computed(() => formatMoney(promoSummary.value?.original_amount_cents ?? 0));
const savingsAmountText = computed(() => formatMoney(promoSummary.value?.savings_cents ?? 0));
const promoDiscountText = computed(() => `${promoSummary.value?.discount_percent ?? 0}%`);
const promoLossAversionText = computed(() => hasPromo.value ? (promoSummary.value?.promo_loss_aversion_text || "错过后将恢复原价") : "支付后立即解锁完整详情与原文对比");
const promoNoteText = computed(() => hasPromo.value ? (promoSummary.value?.promo_note || "支付后立即解锁完整详情与原文对比") : "支付后立即解锁完整详情与原文对比");
const promoBadgeText = computed(() => promoSummary.value?.promo_badge || "限时特惠");
const serverOffsetMs = computed(() => buildServerOffsetMs(promoSummary.value?.server_now));
const countdownText = computed(() => formatCountdown(getRemainingMs(promoSummary.value, serverOffsetMs.value, countdownNow.value)));

async function handleCreateOrder() {
  if (!props.taskNo) {
    ElMessage.warning("缺少任务号，无法创建订单");
    return;
  }

  if (!paymentAvailability.value[selectedChannel.value]) {
    ElMessage.warning(`当前未启用${selectedChannel.value === "wechat" ? "微信支付" : "支付宝"}，请先在后台开启配置`);
    return;
  }

  if (!contact.value.trim()) {
    ElMessage.warning("请填写联系方式，便于根据订单排查问题");
    return;
  }

  creating.value = true;
  try {
    window.clearInterval(pollTimer);
    order.value = null;
    orderStatus.value = null;
    qrCodeDataUrl.value = "";
    order.value = await createOrder(props.taskNo, contact.value.trim(), selectedChannel.value);
    await syncQrCode(order.value?.qr_code_url ?? null);
    saveOrderNo(order.value.order_no);
    await checkPaymentStatus();
    startPolling();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "创建订单失败");
  } finally {
    creating.value = false;
  }
}

async function handlePaid() {
  if (!order.value) return;

  paying.value = true;
  try {
    await checkPaymentStatus();
    if (orderStatus.value?.status !== "paid") {
      ElMessage.warning("暂未确认支付成功，请完成付款后稍等片刻再点击校验");
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "支付状态更新失败");
  } finally {
    paying.value = false;
  }
}

function startPolling() {
  window.clearInterval(pollTimer);
  pollTimer = window.setInterval(() => {
    void checkPaymentStatus();
  }, 2500);
}

async function checkPaymentStatus() {
  if (!order.value) return;

  checking.value = true;
  try {
    orderStatus.value = await getOrderStatus(order.value.order_no);
    if (orderStatus.value.status === "paid") {
      window.clearInterval(pollTimer);
      ElMessage.success("支付成功，本次任务已解锁完整详情");
      visible.value = false;
      emit("paid");
    }
  } catch (error) {
    window.clearInterval(pollTimer);
    ElMessage.error(error instanceof Error ? error.message : "查询支付状态失败");
  } finally {
    checking.value = false;
  }
}

async function syncQrCode(payload: string | null) {
  if (!payload) {
    qrCodeDataUrl.value = "";
    return;
  }

  try {
    qrCodeDataUrl.value = await QRCode.toDataURL(payload, {
      margin: 1,
      width: 220,
      color: {
        dark: "#111111",
        light: "#FFFFFF"
      }
    });
  } catch (error) {
    qrCodeDataUrl.value = "";
    ElMessage.error(error instanceof Error ? error.message : "生成支付二维码失败");
  }
}

async function handleRegenerateOrder() {
  await handleCreateOrder();
  if (order.value?.order_no) {
    ElMessage.success("已重新生成支付二维码，旧订单已自动关闭");
  }
}

async function loadPaymentConfig() {
  try {
    siteConfig.value = await getPublicSiteConfig();
    paymentAvailability.value = {
      alipay: Boolean(siteConfig.value.alipay_enabled),
      wechat: Boolean(siteConfig.value.wechat_enabled)
    };
    if (!paymentAvailability.value[selectedChannel.value]) {
      selectedChannel.value = paymentAvailability.value.wechat ? "wechat" : "alipay";
    }
  } catch {
    siteConfig.value = null;
    paymentAvailability.value = { alipay: true, wechat: false };
  }
}

function startCountdown() {
  window.clearInterval(countdownTimer);
  countdownNow.value = Date.now();
  countdownTimer = window.setInterval(() => {
    countdownNow.value = Date.now();
  }, 1000);
}

watch(visible, (value) => {
  if (!value) {
    window.clearInterval(pollTimer);
    window.clearInterval(countdownTimer);
  } else {
    void loadPaymentConfig();
    startCountdown();
    if (order.value && orderStatus.value?.status !== "paid") {
      startPolling();
    }
  }
});

watch(() => props.taskNo, () => {
  window.clearInterval(pollTimer);
  order.value = null;
  orderStatus.value = null;
  qrCodeDataUrl.value = "";
});

watch(() => order.value?.qr_code_url, (value) => {
  void syncQrCode(value ?? null);
});

onBeforeUnmount(() => {
  window.clearInterval(pollTimer);
  window.clearInterval(countdownTimer);
});
</script>

<style scoped>
.payment-dialog__header {
  padding-right: 24px;
}

.payment-dialog__eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 122, 89, 0.12);
  color: #d94f2b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.payment-dialog__header h2 {
  margin: 10px 0 6px;
  font-size: 24px;
  line-height: 1.25;
  color: #111;
}

.payment-dialog__header p {
  margin: 0;
  color: #666;
  line-height: 1.65;
  font-size: 13px;
}

.payment-dialog__origin {
  text-decoration: line-through;
  color: #999;
}

.payment-layout {
  display: grid;
  gap: 14px;
}

.payment-layout--checkout {
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  align-items: start;
  gap: 16px;
}

.payment-layout__main,
.payment-layout__aside {
  display: grid;
  gap: 14px;
}

.payment-hero {
  position: relative;
  overflow: hidden;
  padding: 18px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(255, 122, 89, 0.2), transparent 32%),
    linear-gradient(135deg, #121212, #3b2417);
  color: #fff8ef;
}

.payment-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.08), transparent 36%);
  pointer-events: none;
}

.payment-hero__main {
  position: relative;
  z-index: 1;
}

.payment-hero__flag {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.payment-hero__price {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 10px;
}

.payment-hero__price-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.payment-hero__origin-price {
  font-size: 14px;
  text-decoration: line-through;
  color: rgba(255, 248, 239, 0.64);
}

.payment-hero__price strong {
  font-size: 34px;
  line-height: 1;
  color: #ffe08a;
}

.payment-hero__price span {
  font-size: 14px;
  color: rgba(255, 248, 239, 0.76);
}

.payment-hero p {
  max-width: 540px;
  margin: 8px 0 0;
  line-height: 1.6;
  font-size: 13px;
  color: rgba(255, 248, 239, 0.9);
}

.payment-hero__promo-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.payment-hero__save,
.payment-hero__loss,
.payment-hero__countdown {
  padding: 9px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
}

.payment-hero__save {
  color: #ffe08a;
  font-weight: 700;
}

.payment-hero__loss {
  color: rgba(255, 248, 239, 0.92);
}

.payment-hero__countdown {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 248, 239, 0.82);
}

.payment-hero__countdown strong {
  font-size: 16px;
  letter-spacing: 1px;
  color: #ffffff;
}

.payment-summary-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.payment-summary-card {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.payment-summary-card span {
  display: block;
  font-size: 12px;
  color: rgba(255, 248, 239, 0.72);
  margin-bottom: 6px;
}

.payment-summary-card strong {
  display: block;
  color: #fff;
  word-break: break-all;
}

.payment-benefits {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.payment-benefits__item {
  padding: 7px 10px;
  border-radius: 999px;
  background: #fff7f1;
  border: 1px solid #ffe0d3;
  color: #8a4c2f;
  font-size: 12px;
  font-weight: 600;
}

.payment-channel-panel {
  padding: 14px;
  border-radius: 18px;
  background: #fcfbfa;
  border: 1px solid #eee5de;
}

.payment-channel-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.payment-channel-panel__head strong {
  color: #111;
}

.payment-channel-panel__head span {
  color: #7a726b;
  font-size: 12px;
  line-height: 1.6;
  text-align: right;
}

.payment-channel-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.payment-channel-option {
  height: 42px;
  border-radius: 14px;
  border: 1px solid #e7ddd5;
  background: #fff;
  color: #554d46;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.payment-channel-option.is-active {
  border-color: #111;
  background: #111;
  color: #fff;
  box-shadow: 0 12px 24px rgba(17, 17, 17, 0.12);
}

.payment-channel-option:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.payment-order-panel,
.payment-qr-panel {
  padding: 14px;
  border-radius: 18px;
  background: #faf8f6;
  border: 1px solid #eee5de;
}

.payment-order-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.payment-status-banner {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.payment-status-banner--error {
  background: #fff1ee;
  border: 1px solid #ffd2c8;
}

.payment-status-banner strong {
  color: #9b3720;
  font-size: 12px;
}

.payment-status-banner span {
  color: #7f4a3b;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.payment-qr-panel__content {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.payment-qr-panel__image-wrap {
  position: relative;
  align-self: center;
  padding: 14px 14px 12px;
  border-radius: 24px;
  background: #fff;
  border: 1px solid #ece3dc;
  box-shadow: 0 18px 36px rgba(17, 17, 17, 0.08);
  overflow: hidden;
}

.payment-qr-panel__brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.payment-qr-panel__brand--alipay {
  background: #f5f8ff;
  color: #1677ff;
}

.payment-qr-panel__brand--wechat {
  background: #f1fbf5;
  color: #17a34a;
}

.payment-qr-panel__brand-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}

.payment-qr-panel__brand-dot--alipay {
  background: #1677ff;
  box-shadow: 0 0 0 4px rgba(22, 119, 255, 0.12);
}

.payment-qr-panel__brand-dot--wechat {
  background: #17a34a;
  box-shadow: 0 0 0 4px rgba(23, 163, 74, 0.12);
}

.payment-qr-panel__image {
  display: block;
  width: 200px;
  height: 200px;
  object-fit: contain;
}

.payment-qr-panel__scan-line {
  position: absolute;
  left: 18px;
  right: 18px;
  top: 54px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(22, 119, 255, 0.8), transparent);
  box-shadow: 0 0 12px rgba(22, 119, 255, 0.35);
  animation: qrScan 2.6s ease-in-out infinite;
}

.payment-qr-panel__caption {
  margin-top: 12px;
  text-align: center;
  font-size: 12px;
  color: #7a726b;
}

.payment-qr-panel__tips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.payment-qr-panel__steps {
  display: grid;
  gap: 10px;
  margin-top: 4px;
}

.payment-qr-panel__steps div {
  padding: 9px 11px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ece3dc;
  color: #554d46;
  font-size: 13px;
}

.payment-qr-panel__error-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff3f0, #fffaf7);
  border: 1px solid #ffd5cb;
}

.payment-qr-panel__error-icon {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: linear-gradient(135deg, #ff7a59, #ff3d54);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 800;
  box-shadow: 0 10px 20px rgba(255, 61, 84, 0.18);
}

.payment-qr-panel__error-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.payment-qr-panel__error-hints {
  display: grid;
  gap: 8px;
  margin-top: 4px;
}

.payment-qr-panel__error-hints div {
  padding: 9px 11px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 122, 89, 0.14);
  color: #7a5c4f;
  font-size: 12px;
  line-height: 1.6;
}

.payment-qr-panel__placeholder {
  padding: 12px 4px;
}

.payment-order-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.payment-order-list div {
  padding: 10px 12px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #ece3dc;
}

.payment-order-list span,
.payment-qr-panel__placeholder span,
.payment-qr-panel__tips span {
  display: block;
  font-size: 12px;
  color: #7a726b;
  margin-bottom: 6px;
}

.payment-order-list strong,
.payment-qr-panel__placeholder strong,
.payment-qr-panel__tips strong {
  color: #111;
  word-break: break-all;
}

.payment-empty-state {
  color: #7a726b;
  line-height: 1.7;
  font-size: 14px;
}

.payment-form :deep(.el-form-item__label) {
  font-weight: 600;
}

.payment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.payment-footer__ghost {
  min-width: 120px;
}

.payment-footer__primary {
  min-width: 220px;
  height: 42px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #ff7a59, #ff3d54);
  box-shadow: 0 14px 28px rgba(255, 61, 84, 0.24);
}

.payment-footer__primary:hover {
  background: linear-gradient(135deg, #ff6f4d, #ff304c);
}

:deep(.payment-dialog-overlay) {
  background: rgba(15, 15, 15, 0.58);
  backdrop-filter: blur(6px);
}

:deep(.payment-dialog .el-dialog) {
  margin-top: 6vh !important;
  max-height: 86vh;
  border-radius: 26px;
  overflow: hidden;
  box-shadow: 0 28px 80px rgba(17, 17, 17, 0.28);
}

:deep(.payment-dialog .el-dialog__header) {
  padding: 20px 22px 0;
}

:deep(.payment-dialog .el-dialog__body) {
  max-height: calc(86vh - 140px);
  overflow-y: auto;
  padding: 16px 22px 18px;
}

:deep(.payment-dialog .el-dialog__footer) {
  padding: 0 22px 20px;
}

@keyframes qrScan {
  0%,
  100% {
    transform: translateY(0);
    opacity: 0.72;
  }

  50% {
    transform: translateY(200px);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .payment-layout--checkout {
    grid-template-columns: 1fr;
  }

  .payment-channel-panel__head {
    flex-direction: column;
  }

  .payment-channel-panel__head span {
    text-align: left;
  }

  .payment-summary-grid,
  .payment-order-list,
  .payment-channel-switch {
    grid-template-columns: 1fr;
  }

  .payment-qr-panel__content {
    flex-direction: column;
    align-items: stretch;
  }

  .payment-qr-panel__image-wrap {
    align-self: center;
  }

  .payment-qr-panel__scan-line {
    display: none;
  }

  .payment-dialog__header h2 {
    font-size: 20px;
  }

  .payment-hero__price strong {
    font-size: 30px;
  }

  .payment-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .payment-footer__primary,
  .payment-footer__ghost {
    width: 100%;
  }
}
</style>
