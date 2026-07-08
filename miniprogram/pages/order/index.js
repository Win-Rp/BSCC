const api = require("../../services/api");
const storage = require("../../utils/storage");
const { startPolling, isOrderTerminal } = require("../../services/task");
const { formatMoney, formatDateTime } = require("../../utils/format");

function buildChannels(siteConfig) {
  const config = siteConfig || {};
  const channels = [];
  if (config.alipay_enabled !== false) {
    channels.push({ value: "alipay", label: "支付宝" });
  }
  if (config.wechat_enabled) {
    channels.push({ value: "wechat", label: "微信支付" });
  }
  if (!channels.length) {
    channels.push({ value: "alipay", label: "支付宝" });
  }
  return channels;
}

function getPayChannelText(channel) {
  return channel === "wechat" ? "微信支付" : "支付宝";
}

function getOrderStatusText(status) {
  const map = {
    created: "待支付",
    pending: "待支付",
    unpaid: "待支付",
    paying: "支付处理中",
    processing: "支付处理中",
    paid: "已支付",
    failed: "支付失败",
    closed: "已关闭",
    canceled: "已取消",
    cancelled: "已取消",
    refunded: "已退款"
  };
  return map[status] || status || "-";
}

function getUnlockStatusText(status) {
  const map = {
    locked: "待解锁",
    unlocked: "已解锁",
    free: "免费可看"
  };
  return map[status] || status || "-";
}

function buildOrderCard(data, fallbackChannel) {
  if (!data || !data.order_no) {
    return null;
  }

  return {
    orderNo: data.order_no,
    amountText: typeof data.amount_cents === "number" ? formatMoney(data.amount_cents) : "以服务端返回为准",
    bFileCount: data.b_file_count || 0,
    qrCodeURL: data.qr_code_url || "",
    paymentMessage: data.payment_message || "订单已创建，请按系统提示完成支付后自动刷新状态。",
    status: data.status || "",
    statusText: getOrderStatusText(data.status),
    payChannelText: getPayChannelText(data.pay_channel || fallbackChannel),
    pricing: data.pricing || null
  };
}

function buildStatusCard(data, fallbackOrderNo) {
  if (!data && !fallbackOrderNo) {
    return null;
  }

  const payload = data || {};
  return {
    orderNo: payload.order_no || fallbackOrderNo || "",
    status: payload.status || "",
    statusText: getOrderStatusText(payload.status),
    unlockStatus: payload.unlock_status || "",
    unlockStatusText: getUnlockStatusText(payload.unlock_status),
    paidAt: payload.paid_at ? formatDateTime(payload.paid_at) : "待支付",
    payChannelText: getPayChannelText(payload.pay_channel),
    taskNo: payload.task_no || ""
  };
}

Page({
  data: {
    taskNo: "",
    orderNo: "",
    contact: "",
    payChannel: "alipay",
    channels: [{ value: "alipay", label: "支付宝" }],
    loading: false,
    refreshing: false,
    polling: false,
    errorText: "",
    orderCard: null,
    statusCard: null,
    supportInfo: null
  },

  onLoad(options) {
    const app = getApp();
    const siteConfig = app.globalData.siteConfig || {};
    const supportInfo = app.globalData.supportInfo || {};
    const recovery = storage.getRecoveryInfo();
    const channels = buildChannels(siteConfig);
    this.hasRedirectedAfterPaid = false;
    this.setData({
      taskNo: options.taskNo || recovery.taskNo || storage.getTaskNo(),
      orderNo: options.orderNo || recovery.orderNo || storage.getOrderNo(),
      contact: recovery.contact || "",
      channels,
      payChannel: channels[0].value,
      supportInfo
    });
  },

  onShow() {
    if (this.data.orderNo) {
      this.queryOrderStatus({ silent: true });
      this.startOrderPolling();
    }
  },

  onHide() {
    this.stopOrderPolling();
  },

  onUnload() {
    this.stopOrderPolling();
  },

  handleInput(event) {
    const field = event.currentTarget.dataset.field;
    this.setData({
      [field]: event.detail.value
    });
  },

  handleChannelChange(event) {
    this.setData({
      payChannel: event.detail.value
    });
  },

  async createOrder() {
    if (!this.data.taskNo) {
      this.setData({ errorText: "缺少任务号，请先返回结果页或恢复页" });
      return;
    }
    if (!this.data.contact) {
      this.setData({ errorText: "请填写联系方式，便于恢复订单" });
      return;
    }

    this.setData({
      loading: true,
      errorText: ""
    });

    const response = await api.createOrder({
      task_no: this.data.taskNo,
      contact: this.data.contact,
      pay_channel: this.data.payChannel
    });

    if (!response.success) {
      this.setData({
        loading: false,
        errorText: response.error ? response.error.message : "订单创建失败"
      });
      return;
    }

    const data = response.data || {};
    this.hasRedirectedAfterPaid = false;
    storage.setTaskContext({
      taskNo: data.task_no,
      orderNo: data.order_no,
      contact: this.data.contact
    });

    this.setData({
      loading: false,
      orderNo: data.order_no,
      orderCard: buildOrderCard(data, this.data.payChannel),
      statusCard: buildStatusCard(data, data.order_no)
    });

    this.queryOrderStatus({ silent: true });
    this.startOrderPolling();
  },

  async queryOrderStatus(options) {
    const finalOptions = options || {};
    if (!this.data.orderNo) {
      if (!finalOptions.silent) {
        wx.showToast({
          title: "暂无订单号可查询",
          icon: "none"
        });
      }
      return;
    }

    this.setData({
      refreshing: true,
      errorText: ""
    });

    const response = await api.getOrderStatus(this.data.orderNo);
    if (!response.success) {
      this.setData({
        refreshing: false,
        errorText: response.error ? response.error.message : "订单状态获取失败"
      });
      if (!finalOptions.silent) {
        wx.showToast({
          title: "刷新失败，请稍后重试",
          icon: "none"
        });
      }
      return;
    }

    const data = response.data || {};
    storage.setTaskContext({
      taskNo: data.task_no || this.data.taskNo,
      orderNo: data.order_no || this.data.orderNo,
      contact: this.data.contact
    });

    this.setData({
      refreshing: false,
      taskNo: data.task_no || this.data.taskNo,
      orderNo: data.order_no || this.data.orderNo,
      statusCard: buildStatusCard(data, this.data.orderNo)
    });

    if (!this.data.orderCard && data.order_no) {
      this.setData({
        orderCard: buildOrderCard(data, this.data.payChannel)
      });
    }

    if (finalOptions.manual) {
      wx.showToast({
        title: "状态已更新",
        icon: "success"
      });
    }

    if (data.status === "paid" || data.unlock_status === "unlocked") {
      this.handlePaidSuccess(data);
    }
  },

  handlePaidSuccess(data) {
    if (this.hasRedirectedAfterPaid) {
      return;
    }

    this.hasRedirectedAfterPaid = true;
    this.stopOrderPolling();
    wx.showToast({
      title: "支付完成，已解锁",
      icon: "success"
    });
    setTimeout(() => {
      wx.redirectTo({
        url: `/pages/results/index?taskNo=${data.task_no || this.data.taskNo}`
      });
    }, 1000);
  },

  handleRefreshStatus() {
    this.queryOrderStatus({ manual: true });
  },

  copyOrderNo() {
    const orderNo = this.data.orderNo || (this.data.statusCard && this.data.statusCard.orderNo) || "";
    if (!orderNo) {
      wx.showToast({
        title: "暂无订单号可复制",
        icon: "none"
      });
      return;
    }

    wx.setClipboardData({
      data: orderNo,
      success: () => {
        wx.showToast({
          title: "订单号已复制",
          icon: "success"
        });
      }
    });
  },

  startOrderPolling() {
    if (!this.data.orderNo) {
      return;
    }
    this.stopOrderPolling();
    this.setData({ polling: true });
    this.poller = startPolling(
      () => api.getOrderStatus(this.data.orderNo),
      {
        onSuccess: (response) => {
          if (!response.success) {
            return;
          }

          const data = response.data || {};
          storage.setTaskContext({
            taskNo: data.task_no || this.data.taskNo,
            orderNo: data.order_no || this.data.orderNo,
            contact: this.data.contact
          });

          this.setData({
            taskNo: data.task_no || this.data.taskNo,
            orderNo: data.order_no || this.data.orderNo,
            statusCard: buildStatusCard(data, this.data.orderNo)
          });

          if (!this.data.orderCard && data.order_no) {
            this.setData({
              orderCard: buildOrderCard(data, this.data.payChannel)
            });
          }

          if (data.status === "paid" || data.unlock_status === "unlocked") {
            this.handlePaidSuccess(data);
          }
        },
        shouldStop: (response) => {
          if (!response.success) {
            return false;
          }
          return isOrderTerminal(response.data && response.data.status) || (response.data && response.data.unlock_status === "unlocked");
        }
      }
    );
  },

  stopOrderPolling() {
    if (this.poller && this.poller.stop) {
      this.poller.stop();
    }
    this.poller = null;
    this.setData({ polling: false });
  },

  gotoResults() {
    wx.navigateTo({
      url: `/pages/results/index?taskNo=${this.data.taskNo}`
    });
  }
});
