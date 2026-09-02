const { formatMoney, formatCountdown, buildServerOffsetMs } = require("../../utils/format");

function buildOfferModel(summary, unlocked, promo) {
  if (!summary) {
    return null;
  }
  if (!summary.payment_required) {
    return null;
  }

  if (unlocked) {
    return {
      locked: false,
      title: "已解锁完整详情",
      desc: "本任务已完成解锁，可查看全部对比详情与后续回看。",
      badge: "",
      priceText: "",
      strikeText: "",
      savingsText: "",
      unitPriceText: "",
      note: "",
      lossAversion: "",
      showCountdown: false,
      promoEndsAt: "",
      serverNow: "",
      bFileCount: summary.b_file_count || 0
    };
  }

  const bFileCount = Math.max(Number(summary.b_file_count || 1), 1);
  const pricing = promo || {};
  const originalUnit = Number(pricing.original_unit_price_cents || 0);
  const effectiveUnit = Number(pricing.effective_unit_price_cents || pricing.promo_unit_price_cents || 0);
  const originalAmount = originalUnit * bFileCount;
  const effectiveAmount = effectiveUnit * bFileCount;
  const savings = Math.max(originalAmount - effectiveAmount, 0);
  const promoActive = Boolean(pricing.promo_active) && savings > 0;
  const showCountdown = Boolean(pricing.show_countdown) && Boolean(pricing.promo_ends_at);

  return {
    locked: true,
    title: "解锁查重",
    desc: "本次任务已超出免费对比文件额度，解锁后可查看全部重复片段、格式相似项、元数据对比与关键字命中。",
    badge: promoActive ? (pricing.promo_badge || "限时特惠") : "",
    priceText: effectiveUnit > 0 ? formatMoney(effectiveAmount) : "以下单页为准",
    strikeText: promoActive ? formatMoney(originalAmount) : "",
    savingsText: promoActive ? formatMoney(savings) : "",
    unitPriceText: effectiveUnit > 0 ? `${formatMoney(effectiveUnit)} / 份` : "",
    note: promoActive ? (pricing.promo_note || "") : "",
    lossAversion: promoActive ? (pricing.promo_loss_aversion_text || "") : "",
    showCountdown,
    promoEndsAt: showCountdown ? pricing.promo_ends_at : "",
    serverNow: pricing.server_now || "",
    bFileCount
  };
}

Component({
  properties: {
    summary: {
      type: Object,
      value: null
    },
    unlocked: {
      type: Boolean,
      value: false
    },
    orderNo: {
      type: String,
      value: ""
    },
    promo: {
      type: Object,
      value: null
    }
  },

  data: {
    viewModel: null,
    countdownText: ""
  },

  observers: {
    "summary, unlocked, promo"() {
      this.updateViewModel();
    }
  },

  lifetimes: {
    attached() {
      this.updateViewModel();
    },
    detached() {
      this.stopCountdown();
    }
  },

  methods: {
    updateViewModel() {
      const viewModel = buildOfferModel(this.data.summary, this.data.unlocked, this.data.promo);
      this.setData({ viewModel });
      this.syncCountdown();
    },

    syncCountdown() {
      const viewModel = this.data.viewModel;
      if (!viewModel || !viewModel.showCountdown || !viewModel.promoEndsAt) {
        this.stopCountdown();
        this.setData({ countdownText: "" });
        return;
      }

      this.stopCountdown();
      this.countdownEndTs = Date.parse(viewModel.promoEndsAt);
      this.countdownOffset = buildServerOffsetMs(viewModel.serverNow);
      this.tickCountdown();
      this.countdownTimer = setInterval(() => this.tickCountdown(), 1000);
    },

    tickCountdown() {
      const remainingMs = Math.max(this.countdownEndTs - (Date.now() + this.countdownOffset), 0);
      this.setData({
        countdownText: formatCountdown(remainingMs)
      });
      if (remainingMs <= 0) {
        this.stopCountdown();
      }
    },

    stopCountdown() {
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer);
        this.countdownTimer = null;
      }
    },

    handleUnlock() {
      this.triggerEvent("unlock");
    },

    handleView() {
      this.triggerEvent("view");
    }
  }
});
