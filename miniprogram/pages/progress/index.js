const api = require("../../services/api");
const storage = require("../../utils/storage");
const { startPolling, isTaskTerminal } = require("../../services/task");
const { getStatusText } = require("../../utils/format");

const STATUS_ORDER = ["uploaded", "queued", "parsing", "checking", "awaiting_payment", "completed"];

const STATUS_HINTS = {
  uploaded: "任务已提交，等待处理",
  queued: "已进入队列，通常数分钟内开始处理",
  parsing: "正在解析文档内容，速度与文件大小相关",
  checking: "正在逐份比对标书内容，请稍候",
  awaiting_payment: "查重完成，正在跳转结果页…",
  completed: "查重完成，正在跳转结果页…",
  failed: "任务处理失败，请返回重新上传"
};

// 失败时后端不记录失败阶段，从错误信息推断（默认视为比对阶段失败）
function inferFailedStepKey(errorMessage) {
  return /解析|parse/i.test(errorMessage || "") ? "parsing" : "checking";
}

function buildStepItems(status, errorMessage) {
  const steps = [
    { key: "queued", label: "排队" },
    { key: "parsing", label: "解析" },
    { key: "checking", label: "查重" },
    { key: "awaiting_payment", label: "待解锁" },
    { key: "completed", label: "完成" }
  ];
  const currentIndex = Math.max(STATUS_ORDER.indexOf(status), 0);
  const failedIndex = status === "failed" ? STATUS_ORDER.indexOf(inferFailedStepKey(errorMessage)) : -1;
  return steps.map((item, index) => {
    const stepIndex = STATUS_ORDER.indexOf(item.key);
    let state = "pending";
    if (status === "completed") {
      state = "done";
    } else if (status === "failed") {
      state = stepIndex < failedIndex ? "done" : stepIndex === failedIndex ? "error" : "pending";
    } else if (stepIndex < currentIndex) {
      state = "done";
    } else if (stepIndex === currentIndex) {
      state = "current";
    }
    return {
      key: item.key,
      label: item.label,
      state
    };
  });
}

function buildViewStatus(status, errorMessage) {
  const failed = status === "failed";
  const finished = status === "awaiting_payment" || status === "completed";
  return {
    isFailed: failed,
    isFinished: finished,
    statusHint: failed ? (errorMessage || STATUS_HINTS.failed) : (STATUS_HINTS[status] || "")
  };
}

Page({
  data: {
    taskNo: "",
    progress: 0,
    status: "",
    statusText: "任务初始化中",
    statusHint: "正在同步任务状态，请稍候…",
    isFailed: false,
    isFinished: false,
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
          const status = data.status || "";
          const errorMessage = data.error_message || "";
          const viewStatus = buildViewStatus(status, errorMessage);
          storage.setTaskContext({ taskNo: data.task_no || this.data.taskNo });
          this.setData(Object.assign({
            loading: false,
            progress: data.progress || 0,
            status,
            statusText: data.message || getStatusText(status),
            errorMessage,
            steps: buildStepItems(status, errorMessage)
          }, viewStatus));

          if (status === "awaiting_payment" || status === "completed") {
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
    if (!this.data.isFinished && !this.data.isFailed) {
      wx.showToast({
        title: `任务尚未完成（${this.data.progress}%），请稍候`,
        icon: "none"
      });
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
  },

  gotoRecovery() {
    wx.navigateTo({
      url: "/pages/recovery/index"
    });
  },

  copyTaskNo() {
    const taskNo = this.data.taskNo || "";
    if (!taskNo) {
      wx.showToast({
        title: "暂无任务号可复制",
        icon: "none"
      });
      return;
    }
    wx.setClipboardData({
      data: taskNo,
      success: () => {
        wx.showToast({
          title: "任务号已复制",
          icon: "success"
        });
      }
    });
  },

  onShareAppMessage() {
    const siteConfig = getApp().globalData.siteConfig || {};
    return {
      title: `${siteConfig.site_title || "标书查重"} · 智能查重与风险研判`,
      path: "/pages/upload/index",
      desc: "上传主标书与多份对比标书，自动完成重复检测与结果排行",
      imageUrl: "/assets/images/share.png"
    };
  }
});
