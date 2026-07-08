Component({
  properties: {
    summary: {
      type: Object,
      value: null
    },
    unlocked: {
      type: Boolean,
      value: false
    },
    orderNo: {
      type: String,
      value: ""
    }
  },

  data: {
    viewModel: null
  },

  observers: {
    summary(value) {
      if (!value) {
        this.setData({ viewModel: null });
        return;
      }
      this.setData({
        viewModel: {
          bFileCount: value.b_file_count || 0,
          note: value.payment_required ? "当前为 1 对多任务，支付后解锁全部对比详情。"
            : "当前任务已具备完整查看能力。"
        }
      });
    }
  },

  methods: {
    handleUnlock() {
      this.triggerEvent("unlock");
    },

    handleView() {
      this.triggerEvent("view");
    }
  }
});
