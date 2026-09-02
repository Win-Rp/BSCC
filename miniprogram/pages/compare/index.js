const api = require("../../services/api");
const storage = require("../../utils/storage");
const { downloadAndOpenFile } = require("../../utils/file");
const {
  formatPercent,
  getMatchTypeText,
  ellipsis
} = require("../../utils/format");

function buildCompareOptions(summary) {
  return (summary.results || []).map((item) => ({
    compareResultId: item.compare_result_id,
    label: item.b_file_name
  }));
}

function buildPreviewList(payload) {
  return (payload && payload.segments ? payload.segments : []).map((item, index) => ({
    id: `preview-${index}`,
    typeText: getMatchTypeText(item.match_type),
    similarityText: typeof item.similarity === "number" ? formatPercent(item.similarity) : "-",
    aText: ellipsis(item.a_text, 88),
    bText: ellipsis(item.b_text, 88)
  }));
}

function buildMatchItems(detail) {
  const matches = (detail.matches || []).map((item, index) => ({
    id: `match-${index}`,
    matchType: item.match_type,
    typeText: getMatchTypeText(item.match_type),
    similarityText: formatPercent(item.similarity),
    title: `${getMatchTypeText(item.match_type)} · ${formatPercent(item.similarity)}`,
    aText: item.a_text || "",
    bText: item.b_text || "",
    aBlockId: item.a_position ? item.a_position.block_id : "",
    bBlockId: item.b_position ? item.b_position.block_id : "",
    positionText: `A 第${item.a_position ? item.a_position.page : "-"}页 / B 第${item.b_position ? item.b_position.page : "-"}页`
  }));

  const keywordItems = (detail.keyword_hits || []).map((item, index) => {
    const isAFile = item.file_id === detail.a_document.file_id;
    return {
      id: `keyword-${index}`,
      matchType: "keyword",
      typeText: "关键字命中",
      similarityText: "命中",
      title: `关键字 · ${item.keyword}`,
      aText: isAFile ? item.hit_text : "",
      bText: isAFile ? "" : item.hit_text,
      aBlockId: isAFile ? item.position.block_id : "",
      bBlockId: isAFile ? "" : item.position.block_id,
      positionText: `${isAFile ? "A" : "B"} 第${item.position.page}页`,
      keyword: item.keyword,
      contextBefore: item.context_before || "",
      contextAfter: item.context_after || ""
    };
  });

  return matches.concat(keywordItems);
}

function filterItems(items, filterKey) {
  if (!filterKey || filterKey === "all") {
    return items;
  }
  return items.filter((item) => item.matchType === filterKey);
}

function buildDocBlocks(blocks, filteredItems, activeItem, side) {
  const activeKey = side === "a" ? "aBlockId" : "bBlockId";
  const relatedIds = {};
  filteredItems.forEach((item) => {
    if (item[activeKey]) {
      relatedIds[item[activeKey]] = true;
    }
  });
  const activeId = activeItem && activeItem[activeKey] ? activeItem[activeKey] : "";

  return (blocks || []).map((item) => ({
    id: item.block_id,
    text: item.text,
    page: item.page,
    paragraph: item.paragraph,
    sentence: item.sentence,
    highlight: item.block_id === activeId ? "block--active" : (relatedIds[item.block_id] ? "block--hit" : "")
  }));
}

function buildHitSummary(filteredItems, activeMatch, activeFilter) {
  return {
    countText: String(filteredItems.length || 0),
    typeText: activeMatch ? activeMatch.typeText : (activeFilter === "all" ? "全部命中" : getMatchTypeText(activeFilter)),
    similarityText: activeMatch ? activeMatch.similarityText : "-"
  };
}

function getMetadataTypeText(type) {
  const map = {
    same: "相同",
    similar: "相似",
    different: "不同",
    missing: "缺失"
  };
  return map[type] || type || "-";
}

function buildFormatItems(detail) {
  return (detail.format_results || []).map((item, index) => ({
    id: `format-${index}`,
    itemName: item.item_name,
    aValue: item.a_value,
    bValue: item.b_value,
    similarityText: typeof item.similarity === "number" ? formatPercent(item.similarity) : "-",
    description: item.description || ""
  }));
}

function buildMetadataItems(detail) {
  return (detail.metadata_results || []).map((item, index) => ({
    id: `metadata-${index}`,
    fieldName: item.field_name,
    aValue: item.a_value || "—",
    bValue: item.b_value || "—",
    typeText: getMetadataTypeText(item.similarity_type),
    typeClass: {
      same: "meta-same",
      similar: "meta-similar",
      different: "meta-different",
      missing: "meta-missing"
    }[item.similarity_type] || "",
    isHighlighted: Boolean(item.is_highlighted)
  }));
}

Page({
  data: {
    taskNo: "",
    summary: null,
    compareOptions: [],
    compareIndex: 0,
    currentCompareLabel: "",
    currentResultId: 0,
    loading: true,
    errorText: "",
    locked: false,
    previewList: [],
    filterTabs: [
      { key: "all", label: "全部" },
      { key: "exact", label: "完全重复" },
      { key: "rewrite", label: "改写相似" },
      { key: "semantic", label: "语义相似" },
      { key: "keyword", label: "关键字" }
    ],
    activeFilter: "all",
    detailData: null,
    matchItems: [],
    filteredItems: [],
    activeMatchIndex: 0,
    activeMatch: null,
    hitSummary: null,
    aBlocks: [],
    bBlocks: [],
    formatItems: [],
    metadataItems: []
  },

  onLoad(options) {
    const taskNo = options.taskNo || storage.getTaskNo();
    const resultId = Number(options.resultId || 0);
    this.initialResultId = resultId;
    this.setData({
      taskNo: taskNo || ""
    });
  },

  onShow() {
    if (this.data.taskNo) {
      this.loadSummary();
    }
  },

  async loadSummary() {
    this.setData({
      loading: true,
      errorText: ""
    });

    const response = await api.getTaskSummary(this.data.taskNo);
    if (!response.success) {
      this.setData({
        loading: false,
        errorText: response.error ? response.error.message : "任务结果读取失败"
      });
      return;
    }

    const summary = response.data || {};
    const compareOptions = buildCompareOptions(summary);
    let compareIndex = 0;

    if (this.initialResultId) {
      const targetIndex = compareOptions.findIndex((item) => item.compareResultId === this.initialResultId);
      compareIndex = targetIndex >= 0 ? targetIndex : 0;
    }

    const currentResultId = compareOptions[compareIndex] ? compareOptions[compareIndex].compareResultId : 0;
    this.setData({
      loading: false,
      summary,
      compareOptions,
      compareIndex,
      currentCompareLabel: compareOptions[compareIndex] ? compareOptions[compareIndex].label : "",
      currentResultId
    });

    if (currentResultId) {
      this.loadDetail(currentResultId);
    }
  },

  async loadDetail(compareResultId) {
    this.setData({
      loading: true,
      locked: false,
      errorText: "",
      previewList: [],
      hitSummary: null
    });

    const response = await api.getDetail(this.data.taskNo, compareResultId);
    if (!response.success) {
      if (response.statusCode === 402 || (response.error && response.error.code === "ORDER_NOT_PAID")) {
        const previewRes = await api.getPreview(this.data.taskNo, compareResultId);
        this.setData({
          loading: false,
          locked: true,
          detailData: null,
          matchItems: [],
          filteredItems: [],
          activeMatch: null,
          activeMatchIndex: 0,
          hitSummary: null,
          aBlocks: [],
          bBlocks: [],
          formatItems: [],
          metadataItems: [],
          previewList: previewRes.success ? buildPreviewList(previewRes.data) : [],
          errorText: ""
        });
        return;
      }

      this.setData({
        loading: false,
        errorText: response.error ? response.error.message : "详情获取失败"
      });
      return;
    }

    const detailData = response.data || {};
    const matchItems = buildMatchItems(detailData);
    this.setData({
      loading: false,
      locked: false,
      detailData,
      matchItems,
      formatItems: buildFormatItems(detailData),
      metadataItems: buildMetadataItems(detailData)
    });
    this.applyFilter(this.data.activeFilter, 0);
  },

  handleCompareChange(event) {
    const compareIndex = Number(event.detail.value);
    const option = this.data.compareOptions[compareIndex];
    this.setData({
      compareIndex,
      currentCompareLabel: option ? option.label : "",
      currentResultId: option ? option.compareResultId : 0
    });
    if (option) {
      this.loadDetail(option.compareResultId);
    }
  },

  handleFilterChange(event) {
    const filterKey = event.currentTarget.dataset.key;
    this.applyFilter(filterKey, 0);
  },

  applyFilter(filterKey, activeMatchIndex) {
    const filteredItems = filterItems(this.data.matchItems, filterKey);
    const safeIndex = filteredItems.length ? Math.min(activeMatchIndex, filteredItems.length - 1) : 0;
    const activeMatch = filteredItems[safeIndex] || null;
    const detail = this.data.detailData || {};

    this.setData({
      activeFilter: filterKey,
      filteredItems,
      activeMatchIndex: safeIndex,
      activeMatch,
      hitSummary: buildHitSummary(filteredItems, activeMatch, filterKey),
      aBlocks: buildDocBlocks(detail.a_document ? detail.a_document.blocks : [], filteredItems, activeMatch, "a"),
      bBlocks: buildDocBlocks(detail.b_document ? detail.b_document.blocks : [], filteredItems, activeMatch, "b")
    });
  },

  selectMatch(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.applyFilter(this.data.activeFilter, index);
  },

  async handleOpenAFile() {
    if (!this.data.taskNo) {
      return;
    }

    await downloadAndOpenFile({
      url: api.getAFileURL(this.data.taskNo),
      fileName: this.data.summary && this.data.summary.a_file ? this.data.summary.a_file.name : "A文件",
      loadingText: "正在打开A原文"
    });
  },

  async handleOpenBFile() {
    if (!this.data.taskNo || !this.data.currentResultId) {
      wx.showToast({
        title: "当前暂无可打开的B原文",
        icon: "none"
      });
      return;
    }

    await downloadAndOpenFile({
      url: api.getBFileURL(this.data.taskNo, this.data.currentResultId),
      fileName: this.data.currentCompareLabel || "B文件",
      loadingText: "正在打开B原文"
    });
  },

  gotoOrder() {
    wx.navigateTo({
      url: `/pages/order/index?taskNo=${this.data.taskNo}`
    });
  },

  gotoResults() {
    wx.navigateBack({
      delta: 1
    });
  }
});
