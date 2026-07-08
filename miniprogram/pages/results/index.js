const api = require("../../services/api");
const storage = require("../../utils/storage");
const { downloadAndOpenFile } = require("../../utils/file");
const {
  formatPercent,
  formatDateTime,
  getUnlockStatusText,
  ellipsis
} = require("../../utils/format");

function buildOverview(summary, selectedResult) {
  if (!summary || !selectedResult) {
    return [];
  }
  return [
    { label: "总相似度", value: formatPercent(selectedResult.total_similarity) },
    { label: "完全重复", value: formatPercent(selectedResult.exact_similarity) },
    { label: "改写相似", value: formatPercent(selectedResult.rewrite_similarity) },
    { label: "语义相似", value: formatPercent(selectedResult.semantic_similarity) },
    { label: "格式相似", value: formatPercent(selectedResult.format_similarity) },
    { label: "元数据相似", value: formatPercent(selectedResult.metadata_similarity) }
  ];
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
    similarityText: typeof item.similarity === "number" ? formatPercent(item.similarity) : "-",
    aText: ellipsis(item.a_text, 90),
    bText: ellipsis(item.b_text, 90),
    positionText: `A P${item.a_position ? item.a_position.page : "-"} / B P${item.b_position ? item.b_position.page : "-"}`
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
    currentResultText: isUnlocked ? "已解锁，可查看完整详情" : "未解锁，当前以预览联调为主",
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
    loading: true,
    errorText: "",
    summary: null,
    summaryMeta: null,
    isUnlocked: false,
    selectedResultId: 0,
    selectedResult: null,
    overview: [],
    previewLoading: false,
    previewList: []
  },

  onLoad(options) {
    const recovery = storage.getRecoveryInfo();
    this.setData({
      taskNo: options.taskNo || recovery.taskNo || storage.getTaskNo(),
      orderNo: recovery.orderNo || storage.getOrderNo()
    });
  },

  onShow() {
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
      overview: buildOverview(summary, selectedResult),
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
      overview: buildOverview(this.data.summary, selectedResult),
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
  }
});
