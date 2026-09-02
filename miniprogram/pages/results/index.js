const api = require("../../services/api");
const storage = require("../../utils/storage");
const { downloadAndOpenFile } = require("../../utils/file");
const {
  formatPercent,
  formatDateTime,
  getUnlockStatusText,
  getRiskLevel,
  ellipsis
} = require("../../utils/format");

function getFillClass(value) {
  const number = Number(value || 0);
  if (number >= 0.8) {
    return "bar-row__fill--danger";
  }
  if (number >= 0.5) {
    return "bar-row__fill--warning";
  }
  return "";
}

function buildOverview(summary, selectedResult) {
  if (!summary || !selectedResult) {
    return { totalMetric: null, contentDetails: [], structDetails: [] };
  }
  const totalRisk = getRiskLevel(selectedResult.total_similarity);
  const totalMetric = {
    valueText: formatPercent(selectedResult.total_similarity),
    riskType: totalRisk.type,
    riskText: totalRisk.text
  };
  const toDetail = (label, value) => {
    const number = Number(value || 0);
    return {
      label,
      value: formatPercent(number),
      percent: Math.min(Math.max(Math.round(number * 100), 0), 100),
      fillClass: getFillClass(number)
    };
  };
  return {
    totalMetric,
    contentDetails: [
      toDetail("完全重复", selectedResult.exact_similarity),
      toDetail("改写相似", selectedResult.rewrite_similarity),
      toDetail("语义相似", selectedResult.semantic_similarity)
    ],
    structDetails: [
      toDetail("格式相似", selectedResult.format_similarity),
      toDetail("元数据相似", selectedResult.metadata_similarity)
    ]
  };
}

function buildPreviewList(payload) {
  return (payload && payload.segments ? payload.segments : []).map((item, index) => ({
    id: `${item.match_type}-${index}`,
    typeText: {
      exact: "完全重复",
      rewrite: "改写相似",
      semantic: "语义相似",
      keyword: "关键字命中"
    }[item.match_type] || item.match_type,
    typeClass: {
      exact: "tag-danger",
      rewrite: "tag-warning"
    }[item.match_type] || "",
    similarityText: typeof item.similarity === "number" ? formatPercent(item.similarity) : "-",
    aText: ellipsis(item.a_text, 90),
    bText: ellipsis(item.b_text, 90),
    aPage: item.a_position ? item.a_position.page : "-",
    bPage: item.b_position ? item.b_position.page : "-"
  }));
}

function buildSummaryMeta(summary, selectedResult, isUnlocked) {
  if (!summary) {
    return null;
  }
  return {
    taskNo: summary.task_no,
    modeText: summary.mode === "multi" ? "1 对多查重" : "单份对比",
    unlockText: getUnlockStatusText(summary.unlock_status),
    expiresAt: formatDateTime(summary.expires_at),
    aFileName: summary.a_file ? summary.a_file.name : "-",
    bFileCount: (summary.results || []).length,
    selectedBFileName: selectedResult ? selectedResult.b_file_name : "-"
  };
}

Page({
  data: {
    taskNo: "",
    orderNo: "",
    promoConfig: null,
    loading: true,
    errorText: "",
    summary: null,
    summaryMeta: null,
    isUnlocked: false,
    selectedResultId: 0,
    selectedResult: null,
    overviewData: { totalMetric: null, contentDetails: [], structDetails: [] },
    previewLoading: false,
    previewList: []
  },

  onLoad(options) {
    const recovery = storage.getRecoveryInfo();
    const siteConfig = getApp().globalData.siteConfig || {};
    this.setData({
      taskNo: options.taskNo || recovery.taskNo || storage.getTaskNo(),
      orderNo: recovery.orderNo || storage.getOrderNo(),
      promoConfig: siteConfig.promo || null
    });
  },

  onShow() {
    const siteConfig = getApp().globalData.siteConfig || {};
    this.setData({
      promoConfig: siteConfig.promo || null
    });
    if (this.data.taskNo) {
      this.loadSummary();
    }
  },

  async loadSummary(preferResultId) {
    this.setData({
      loading: true,
      errorText: ""
    });

    const response = await api.getTaskSummary(this.data.taskNo);
    if (!response.success) {
      this.setData({
        loading: false,
        errorText: response.error ? response.error.message : "结果获取失败"
      });
      return;
    }

    const summary = response.data || {};
    const selectedResultId = Number(preferResultId || this.data.selectedResultId || (summary.results && summary.results[0] && summary.results[0].compare_result_id) || 0);
    const selectedResult = (summary.results || []).find((item) => item.compare_result_id === selectedResultId) || (summary.results || [])[0] || null;
    const isUnlocked = summary.unlock_status === "unlocked" || !summary.payment_required;

    storage.setTaskContext({
      taskNo: summary.task_no,
      orderNo: this.data.orderNo || storage.getOrderNo()
    });

    this.setData({
      loading: false,
      summary,
      isUnlocked,
      selectedResultId: selectedResult ? selectedResult.compare_result_id : 0,
      selectedResult,
      overviewData: buildOverview(summary, selectedResult),
      summaryMeta: buildSummaryMeta(summary, selectedResult, isUnlocked)
    });

    if (selectedResult) {
      this.loadPreview(selectedResult.compare_result_id);
    } else {
      this.setData({ previewList: [] });
    }
  },

  async loadPreview(compareResultId) {
    this.setData({
      selectedResultId: compareResultId,
      previewLoading: true
    });

    const selectedResult = (this.data.summary && this.data.summary.results || []).find((item) => item.compare_result_id === compareResultId) || null;
    this.setData({
      selectedResult,
      overviewData: buildOverview(this.data.summary, selectedResult),
      summaryMeta: buildSummaryMeta(this.data.summary, selectedResult, this.data.isUnlocked)
    });

    const response = await api.getPreview(this.data.taskNo, compareResultId);
    this.setData({
      previewLoading: false,
      previewList: response.success ? buildPreviewList(response.data) : [],
      errorText: response.success ? "" : (response.error ? response.error.message : "预览加载失败")
    });
  },

  handlePreview(event) {
    const compareResultId = Number(event.detail.compareResultId);
    this.loadPreview(compareResultId);
  },

  handleDetail(event) {
    const compareResultId = Number(event.detail.compareResultId);
    wx.navigateTo({
      url: `/pages/compare/index?taskNo=${this.data.taskNo}&resultId=${compareResultId}`
    });
  },

  async handleOpenAFile() {
    if (!this.data.taskNo || !this.data.summaryMeta) {
      return;
    }
    await downloadAndOpenFile({
      url: api.getAFileURL(this.data.taskNo),
      fileName: this.data.summaryMeta.aFileName,
      loadingText: "正在打开A标书"
    });
  },

  async handleOpenBFile() {
    if (!this.data.taskNo || !this.data.selectedResultId || !this.data.selectedResult) {
      wx.showToast({
        title: "当前暂无可打开的B标书",
        icon: "none"
      });
      return;
    }

    await downloadAndOpenFile({
      url: api.getBFileURL(this.data.taskNo, this.data.selectedResultId),
      fileName: this.data.selectedResult.b_file_name,
      loadingText: "正在打开B标书"
    });
  },

  gotoOrder() {
    wx.navigateTo({
      url: `/pages/order/index?taskNo=${this.data.taskNo}`
    });
  },

  gotoCompare() {
    if (!this.data.selectedResultId) {
      return;
    }
    wx.navigateTo({
      url: `/pages/compare/index?taskNo=${this.data.taskNo}&resultId=${this.data.selectedResultId}`
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

  buildShareInfo() {
    const siteConfig = getApp().globalData.siteConfig || {};
    const taskNo = this.data.taskNo || "";
    const siteTitle = siteConfig.site_title || "标书查重";
    const results = (this.data.summary && this.data.summary.results) || [];

    if (!taskNo || !results.length) {
      return {
        title: `${siteTitle} · 智能查重与风险研判`,
        desc: "上传标书即可完成重复检测与风险研判",
        taskNo: ""
      };
    }

    const top = results[0];
    const risk = getRiskLevel(top.total_similarity);
    return {
      title: `${siteTitle} · 最高相似度 ${formatPercent(top.total_similarity)}（${risk.text}）`,
      desc: `共 ${this.data.summary.b_file_count} 份对比标书，点击查看完整查重结果`,
      taskNo
    };
  },

  onShareAppMessage() {
    const info = this.buildShareInfo();
    return {
      title: info.title,
      path: info.taskNo ? `/pages/results/index?taskNo=${info.taskNo}` : "/pages/upload/index",
      desc: info.desc,
      imageUrl: "/assets/images/share.png"
    };
  },

  onShareTimeline() {
    const info = this.buildShareInfo();
    return {
      title: info.title,
      query: info.taskNo ? `taskNo=${info.taskNo}` : "",
      imageUrl: "/assets/images/share.png"
    };
  }
});
