const api = require("../../services/api");
const storage = require("../../utils/storage");
const { joinKeywords } = require("../../utils/format");

function normalizeFiles(list) {
  return (list || []).map((item) => ({
    name: item.name,
    path: item.path,
    size: item.size || 0
  }));
}

Page({
  data: {
    siteTitle: "BSCC 标书查重",
    homeTags: [],
    systemNotice: "",
    aFile: null,
    bFiles: [],
    keywords: "",
    loading: false,
    errorText: "",
    submitText: "开始查重",
    rules: [
      "支持 DOC、DOCX、PDF，扫描版 PDF 暂不支持。",
      "B 文件建议控制在 1 至 10 份。",
      "1 对多任务可先免费预览，再按订单解锁完整详情。"
    ]
  },

  onShow() {
    const app = getApp();
    const siteConfig = app.globalData.siteConfig || {};
    this.setData({
      siteTitle: siteConfig.site_title || "BSCC 标书查重",
      homeTags: siteConfig.home_tags || [],
      systemNotice: siteConfig.system_notice || ""
    });
  },

  chooseAFile() {
    wx.chooseMessageFile({
      count: 1,
      type: "file",
      extension: ["doc", "docx", "pdf"],
      success: (res) => {
        const file = normalizeFiles(res.tempFiles)[0] || null;
        this.setData({
          aFile: file,
          errorText: ""
        });
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
      extension: ["doc", "docx", "pdf"],
      success: (res) => {
        const picked = normalizeFiles(res.tempFiles);
        const merged = this.data.bFiles.concat(picked).slice(0, 10);
        this.setData({
          bFiles: merged,
          errorText: ""
        });
      }
    });
  },

  removeBFile(event) {
    const index = Number(event.currentTarget.dataset.index);
    const nextFiles = this.data.bFiles.filter((_, itemIndex) => itemIndex !== index);
    this.setData({
      bFiles: nextFiles
    });
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

  async submitTask() {
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
      submitText: "任务提交中..."
    });

    const response = await api.createTask({
      aFile: this.data.aFile,
      bFiles: this.data.bFiles,
      keywords: joinKeywords(this.data.keywords)
    });

    if (!response.success) {
      this.setData({
        loading: false,
        submitText: "开始查重",
        errorText: response.error ? response.error.message : "提交失败，请稍后重试"
      });
      return;
    }

    const taskNo = response.data.task_no;
    storage.setTaskContext({
      taskNo,
      orderNo: "",
      contact: storage.getRecoveryInfo().contact || ""
    });

    this.setData({
      loading: false,
      submitText: "开始查重"
    });

    wx.navigateTo({
      url: `/pages/progress/index?taskNo=${taskNo}`
    });
  }
});
