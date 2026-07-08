const { formatPercent, getRiskLevel } = require("../../utils/format");

Component({
  properties: {
    result: {
      type: Object,
      value: null
    },
    selected: {
      type: Boolean,
      value: false
    },
    locked: {
      type: Boolean,
      value: false
    },
    unlocked: {
      type: Boolean,
      value: false
    }
  },

  data: {
    viewModel: null
  },

  observers: {
    result(value) {
      if (!value) {
        this.setData({ viewModel: null });
        return;
      }
      const risk = getRiskLevel(value.total_similarity);
      this.setData({
        viewModel: {
          compareResultId: value.compare_result_id,
          bFileName: value.b_file_name,
          totalSimilarity: formatPercent(value.total_similarity),
          exactSimilarity: formatPercent(value.exact_similarity),
          rewriteSimilarity: formatPercent(value.rewrite_similarity),
          semanticSimilarity: formatPercent(value.semantic_similarity),
          keywordHitCount: value.keyword_hit_count || 0,
          matchedSentenceCount: value.matched_sentence_count || 0,
          matchedParagraphCount: value.matched_paragraph_count || 0,
          riskText: risk.text,
          riskType: risk.type
        }
      });
    }
  },

  methods: {
    handlePreview() {
      this.triggerEvent("preview", {
        compareResultId: this.data.viewModel && this.data.viewModel.compareResultId
      });
    },

    handleDetail() {
      this.triggerEvent("detail", {
        compareResultId: this.data.viewModel && this.data.viewModel.compareResultId
      });
    },

    handleUnlock() {
      this.triggerEvent("unlock");
    }
  }
});
