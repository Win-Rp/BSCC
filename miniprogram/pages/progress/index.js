const api = require("../../services/api");
const storage = require("../../utils/storage");
const { startPolling, isTaskTerminal } = require("../../services/task");
const { getStatusText } = require("../../utils/format");

function buildStepItems(status) {
  const steps = [
    { key: "queued", label: "排队" },
    { key: "parsing", label: "解析" },
    { key: "checking", label: "查重" },
    { key: "awaiting_payment", label: "待解锁" },
    { key: "completed", label: "完成" }
  ];
  const order = ["uploaded", "queued", "parsing", "checking", "awaiting_payment", "completed"];
  const currentIndex = Math.max(order.indexOf(status), 0);
  return steps.map((item) => ({
    key: item.key,
    label: item.label,
    active: order.indexOf(item.key) <= currentIndex || (status === "completed" && item.key === "awaiting_payment"),
    current: item.key === status
  }));
}

Page({
  data: {
    taskNo: "",
    progress: 0,
    status: "",
    statusText: "任务初始化中",
    errorMessage: "",
    loading: true,
    steps: buildStepItems("queued")
  },

  onLoad(options) {
    const taskNo = options.taskNo || storage.getTaskNo();
    this.setData({ taskNo: taskNo || "" });
  },

  onShow() {
    if (!this.data.taskNo) {
      return;
    }
    this.startStatusPolling();
  },

  onHide() {
    this.stopStatusPolling();
  },

  onUnload() {
    this.stopStatusPolling();
  },

  startStatusPolling() {
    this.stopStatusPolling();
    this.poller = startPolling(
      () => api.getTaskStatus(this.data.taskNo),
      {
        onSuccess: (response) => {
          if (!response.success) {
            this.setData({
              loading: false,
              errorMessage: response.error ? response.error.message : "状态获取失败"
            });
            return;
          }

          const data = response.data || {};
          storage.setTaskContext({ taskNo: data.task_no || this.data.taskNo });
          this.setData({
            loading: false,
            progress: data.progress || 0,
            status: data.status || "",
            statusText: data.message || getStatusText(data.status),
            errorMessage: data.error_message || "",
            steps: buildStepItems(data.status)
          });

          if (data.status === "awaiting_payment" || data.status === "completed") {
            setTimeout(() => {
              wx.redirectTo({
                url: `/pages/results/index?taskNo=${data.task_no}`
              });
            }, 800);
          }
        },
        shouldStop: (response) => {
          if (!response.success) {
            return false;
          }
          return isTaskTerminal(response.data && response.data.status);
        }
      }
    );
  },

  stopStatusPolling() {
    if (this.poller && this.poller.stop) {
      this.poller.stop();
    }
    this.poller = null;
  },

  gotoResults() {
    if (!this.data.taskNo) {
      return;
    }
    wx.redirectTo({
      url: `/pages/results/index?taskNo=${this.data.taskNo}`
    });
  },

  gotoUpload() {
    wx.reLaunch({
      url: "/pages/upload/index"
    });
  }
});
