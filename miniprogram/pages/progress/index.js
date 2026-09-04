const api = require("../../services/api");
const storage = require("../../utils/storage");
const { startPolling, isTaskTerminal } = require("../../services/task");
const { getStatusText } = require("../../utils/format");

// 服务号二维码兜底直链：site-config 未下发 mp_qrcode_url 时使用
const MP_QR_FALLBACK_URL = "https://mic.mxitx.com/qrcode_srv.jpg";
const MP_QR_LOCAL = "/assets/images/mp-qr.jpg";

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

// uploadState: null-不展示上传节点（任务号直达场景）；current/done/error-上传阶段状态
function buildStepItems(status, errorMessage, uploadState) {
  const steps = [
    { key: "queued", label: "排队" },
    { key: "parsing", label: "解析" },
    { key: "checking", label: "查重" },
    { key: "awaiting_payment", label: "待解锁" },
    { key: "completed", label: "完成" }
  ];
  const hasStatus = Boolean(status);
  const currentIndex = hasStatus ? Math.max(STATUS_ORDER.indexOf(status), 0) : -1;
  const failedIndex = status === "failed" ? STATUS_ORDER.indexOf(inferFailedStepKey(errorMessage)) : -1;
  const mapped = steps.map((item) => {
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
  if (uploadState) {
    mapped.unshift({ key: "upload", label: "上传", state: uploadState });
  }
  return mapped;
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
    copied: false,
    showQr: false,
    mpQrSrc: MP_QR_FALLBACK_URL,
    uploading: false,
    uploadFailed: false,
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
    // scene 为小程序码场景值（BS 端跨端接力码），内容即任务号
    const sceneTaskNo = options.scene ? decodeURIComponent(options.scene) : "";
    const taskNo = options.taskNo || sceneTaskNo || storage.getTaskNo();
    this.setData({ taskNo: taskNo || "" });
    this.resolveMpQrSrc();

    // 上传页直达：预置上传态，避免任务号生成前闪现“未找到任务”
    if (options.from === "upload") {
      this.setData({
        uploading: true,
        statusText: "准备上传文件",
        statusHint: "正在接收文件列表，请稍候…",
        steps: buildStepItems("", "", "current")
      });
    }

    // 由上传页 navigateTo 直达时接收待上传文件，进入「上传阶段」
    const channel = this.getOpenerEventChannel && this.getOpenerEventChannel();
    if (channel && typeof channel.on === "function") {
      channel.on("pendingUpload", (payload) => this.beginUpload(payload || {}));
    }
  },

  onShow() {
    if (!this.data.taskNo || this.data.uploading) {
      return;
    }
    this.startStatusPolling();
  },

  onHide() {
    this.stopStatusPolling();
  },

  onUnload() {
    this._destroyed = true;
    this._stopUploadTimer();
    this.stopStatusPolling();
    if (this._copyResetTimer) {
      clearTimeout(this._copyResetTimer);
      this._copyResetTimer = null;
    }
  },

  showMpQr() {
    this.setData({ showQr: true });
  },

  // 二维码源优先级：后台 site-config 下发 > 兜底直链
  resolveMpQrSrc() {
    const app = getApp();
    const apply = () => {
      const configured = app.globalData.siteConfig && app.globalData.siteConfig.mp_qrcode_url;
      if (configured) {
        this.setData({ mpQrSrc: configured });
      }
    };
    if (app.globalData.siteConfig) {
      apply();
      return;
    }
    if (app.configReady) {
      app.configReady.then(apply).catch(() => {});
    }
  },

  // 远程图加载失败时退回本地静态二维码，保证弹层始终有码可扫
  onMpQrError() {
    if (this.data.mpQrSrc !== MP_QR_LOCAL) {
      this.setData({ mpQrSrc: MP_QR_LOCAL });
    }
  },

  hideMpQr() {
    this.setData({ showQr: false });
  },

  noop() {
    // 阻止冒泡占位：弹层内容点击不关闭
  },

  beginUpload(payload) {
    this._enteredViaUpload = true;
    this.stopStatusPolling();
    const fileCount = 1 + (payload.bFiles || []).length;
    this.setData({
      uploading: true,
      uploadFailed: false,
      isFailed: false,
      progress: 4,
      statusText: "正在上传文件",
      statusHint: `共 ${fileCount} 个文件，上传完成后自动开始查重`,
      steps: buildStepItems("", "", "current")
    });
    this._startUploadTimer();

    api.createTask({
      aFile: payload.aFile,
      bFiles: payload.bFiles || [],
      keywords: payload.keywords || "",
      notifyOpenid: payload.notifyOpenid || "",
      notifyUnionid: payload.notifyUnionid || ""
    }).then((response) => {
      this._stopUploadTimer();
      if (!response.success) {
        if (this._destroyed) {
          return;
        }
        this.setData({
          uploading: false,
          uploadFailed: true,
          isFailed: true,
          statusText: "文件上传失败",
          statusHint: "",
          errorMessage: (response.error && response.error.message) || "上传失败，请返回重试",
          steps: buildStepItems("", "", "error")
        });
        return;
      }

      const taskNo = (response.data && response.data.task_no) || "";
      // 页面已退出也要保存任务号：任务实际已创建，可通过恢复功能找回
      storage.setTaskContext({
        taskNo,
        orderNo: "",
        contact: payload.contact || storage.getRecoveryInfo().contact || ""
      });
      if (this._destroyed) {
        return;
      }
      this.setData({
        uploading: false,
        uploadFailed: false,
        taskNo,
        progress: 100,
        statusText: "文件上传完成",
        statusHint: "已进入处理队列，正在同步任务状态…",
        isFailed: false,
        steps: buildStepItems("queued", "", "done")
      });
      this.startStatusPolling();
    });
  },

  // wx.request 无传输进度回调，用渐进逼近 90% 的平滑动画表达上传进行中
  _startUploadTimer() {
    this._stopUploadTimer();
    this._uploadTimer = setInterval(() => {
      const shown = Math.floor(this.data.progress);
      if (shown >= 90) {
        return;
      }
      const next = Math.min(90, shown + Math.max(1, Math.round((90 - shown) * 0.08)));
      this.setData({ progress: next });
    }, 600);
  },

  _stopUploadTimer() {
    if (this._uploadTimer) {
      clearInterval(this._uploadTimer);
      this._uploadTimer = null;
    }
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
            steps: buildStepItems(status, errorMessage, this._enteredViaUpload ? "done" : null)
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
    if (this.data.uploading) {
      wx.showToast({
        title: "文件上传中，请稍候",
        icon: "none"
      });
      return;
    }
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
    // 优先返回：上传页仍在栈中，已选文件可保留直接重试
    const pages = getCurrentPages();
    if (pages.length > 1) {
      wx.navigateBack();
      return;
    }
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
        // 按钮文案切换为“已复制”作为即时反馈，短暂保留后自动复位
        this.setData({ copied: true });
        if (this._copyResetTimer) {
          clearTimeout(this._copyResetTimer);
        }
        this._copyResetTimer = setTimeout(() => {
          this.setData({ copied: false });
          this._copyResetTimer = null;
        }, 1600);
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
