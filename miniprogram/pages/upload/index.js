const storage = require("../../utils/storage");
const { joinKeywords } = require("../../utils/format");
const { ensureNotifyReady } = require("../../utils/notify");

function normalizeFiles(list) {
  return (list || []).map((item) => ({
    name: item.name,
    path: item.path,
    size: item.size || 0
  }));
}

const SUPPORTED_EXTENSIONS = ["docx", "pdf"];

function splitBySupported(files) {
  const accepted = [];
  const rejected = [];
  for (const file of files) {
    const ext = (file.name.split(".").pop() || "").toLowerCase();
    if (SUPPORTED_EXTENSIONS.indexOf(ext) >= 0) {
      accepted.push(file);
    } else {
      rejected.push(file);
    }
  }
  return { accepted, rejected };
}

Page({
  data: {
    siteTitle: "标书查重",
    homeTags: [],
    systemNotice: "",
    aFile: null,
    bFiles: [],
    keywords: "",
    loading: false,
    errorText: "",
    fileSummary: "尚未选择文件",
    submitText: "开始查重",
    showOfficialAccount: true,
    rules: [
      "支持 DOCX、PDF，扫描版 PDF 暂不支持。",
      "B 文件建议控制在 1 至 10 份。",
      "首份 B 文件免费对比，超出后可在结果页解锁完整详情。"
    ]
  },

  onLoad() {
    // 配置异步返回可能晚于首次 onShow，就绪后再补一次渲染，避免公告延迟出现
    const app = getApp();
    if (app.configReady) {
      app.configReady.then(() => this.applySiteConfig());
    }
  },

  onOfficialAccountError() {
    this.setData({ showOfficialAccount: false });
  },

  onShow() {
    this.applySiteConfig();
    this.refreshBarSummary();
  },

  applySiteConfig() {
    const app = getApp();
    const siteConfig = app.globalData.siteConfig || {};
    this.setData({
      siteTitle: siteConfig.site_title || "标书查重",
      homeTags: siteConfig.home_tags || [],
      systemNotice: siteConfig.system_notice || ""
    });
  },

  refreshBarSummary() {
    const parts = [];
    if (this.data.aFile) parts.push("A×1");
    if (this.data.bFiles.length) parts.push(`B×${this.data.bFiles.length}`);
    const fileSummary = parts.length ? `已选 ${parts.join(" · ")}` : "尚未选择文件";
    this.setData({ fileSummary });
  },

  chooseAFile() {
    wx.chooseMessageFile({
      count: 1,
      type: "file",
      extension: SUPPORTED_EXTENSIONS,
      success: (res) => {
        const files = normalizeFiles(res.tempFiles);
        const { accepted, rejected } = splitBySupported(files);
        if (!accepted.length) {
          this.setData({
            errorText: "仅支持 DOCX、PDF 格式，请重新选择"
          });
          return;
        }
        this.setData({
          aFile: accepted[0],
          errorText: ""
        });
        this.refreshBarSummary();
      }
    });
  },

  chooseBFiles() {
    const remain = 10 - this.data.bFiles.length;
    if (remain <= 0) {
      wx.showToast({
        title: "B 文件最多 10 份",
        icon: "none"
      });
      return;
    }

    wx.chooseMessageFile({
      count: remain,
      type: "file",
      extension: SUPPORTED_EXTENSIONS,
      success: (res) => {
        const picked = normalizeFiles(res.tempFiles);
        const { accepted, rejected } = splitBySupported(picked);
        if (!accepted.length) {
          this.setData({
            errorText: "仅支持 DOCX、PDF 格式，请重新选择"
          });
          return;
        }
        if (rejected.length) {
          wx.showToast({
            title: `已跳过不支持的文件：${rejected.map((f) => f.name).join("、")}`,
            icon: "none"
          });
        }
        this.setData({
          bFiles: this.data.bFiles.concat(accepted).slice(0, 10),
          errorText: ""
        });
        this.refreshBarSummary();
      }
    });
  },

  removeBFile(event) {
    const index = Number(event.currentTarget.dataset.index);
    const nextFiles = this.data.bFiles.filter((_, itemIndex) => itemIndex !== index);
    this.setData({
      bFiles: nextFiles
    });
    this.refreshBarSummary();
  },

  handleKeywordsInput(event) {
    this.setData({
      keywords: event.detail.value
    });
  },

  gotoRecovery() {
    wx.navigateTo({
      url: "/pages/recovery/index"
    });
  },

  gotoDocs() {
    wx.navigateTo({
      url: "/pages/docs/index"
    });
  },

  onShareAppMessage() {
    const siteConfig = getApp().globalData.siteConfig || {};
    return {
      title: `${siteConfig.site_title || "标书查重"} · 1对多智能查重`,
      path: "/pages/upload/index",
      desc: "上传主标书与多份对比标书，自动完成重复检测与风险研判",
      imageUrl: "/assets/images/share.png"
    };
  },

  async submitTask() {
    if (this.data.loading) {
      return;
    }
    if (!this.data.aFile) {
      this.setData({ errorText: "请先选择主标书 A 文件" });
      return;
    }
    if (!this.data.bFiles.length) {
      this.setData({ errorText: "请至少选择 1 份对比标书 B 文件" });
      return;
    }

    this.setData({
      loading: true,
      errorText: "",
      submitText: "准备提交..."
    });

    // 订阅授权必须在用户点击链路内完成（requestSubscribeMessage 依赖点击事件）
    const notify = await ensureNotifyReady();

    this.setData({
      loading: false,
      submitText: "开始查重"
    });

    // 清空上一任务的本地任务号，避免进度页轮询到旧任务
    storage.setTaskNo("");

    // 立即进入等待页，文件上传在进度页内展示，避免原地转圈的“假死”感
    wx.navigateTo({
      url: "/pages/progress/index?from=upload",
      success: (res) => {
        res.eventChannel.emit("pendingUpload", {
          aFile: this.data.aFile,
          bFiles: this.data.bFiles,
          keywords: joinKeywords(this.data.keywords),
          notifyOpenid: notify.openid,
          notifyUnionid: notify.unionid,
          contact: storage.getRecoveryInfo().contact || ""
        });
      },
      fail: () => {
        this.setData({ errorText: "页面跳转失败，请重试" });
      }
    });
  }
});
