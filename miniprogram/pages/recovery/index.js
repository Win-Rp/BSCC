const api = require("../../services/api");
const storage = require("../../utils/storage");
const { formatDateTime, getUnlockStatusText, getStatusText } = require("../../utils/format");

Page({
  data: {
    taskNo: "",
    orderNo: "",
    contact: "",
    loading: false,
    errorText: "",
    result: null
  },

  onLoad() {
    const recovery = storage.getRecoveryInfo();
    this.setData({
      taskNo: recovery.taskNo || storage.getTaskNo(),
      orderNo: recovery.orderNo || storage.getOrderNo(),
      contact: recovery.contact || ""
    });
  },

  handleInput(event) {
    const field = event.currentTarget.dataset.field;
    this.setData({
      [field]: event.detail.value
    });
  },

  async submitRecovery() {
    if (!this.data.taskNo && !this.data.orderNo) {
      this.setData({ errorText: "请至少输入任务号或订单号" });
      return;
    }

    this.setData({
      loading: true,
      errorText: "",
      result: null
    });

    const response = await api.recoverTask({
      task_no: this.data.taskNo || undefined,
      order_no: this.data.orderNo || undefined,
      contact: this.data.contact || undefined
    });

    if (!response.success) {
      this.setData({
        loading: false,
        errorText: response.error ? response.error.message : "恢复失败"
      });
      return;
    }

    const result = response.data || {};
    storage.setTaskContext({
      taskNo: result.task_no,
      orderNo: result.order_no || "",
      contact: this.data.contact || ""
    });

    this.setData({
      loading: false,
      result: {
        taskNo: result.task_no,
        orderNo: result.order_no || "-",
        taskStatusText: getStatusText(result.task_status),
        unlockStatusText: getUnlockStatusText(result.unlock_status),
        orderStatusText: result.order_status || "-",
        canViewDetail: result.can_view_detail,
        expiresAt: formatDateTime(result.expires_at)
      }
    });
  },

  openRecoveredTask() {
    if (!this.data.result) {
      return;
    }
    if (this.data.result.canViewDetail) {
      wx.navigateTo({
        url: `/pages/results/index?taskNo=${this.data.result.taskNo}`
      });
      return;
    }
    wx.navigateTo({
      url: `/pages/order/index?taskNo=${this.data.result.taskNo}`
    });
  }
});
