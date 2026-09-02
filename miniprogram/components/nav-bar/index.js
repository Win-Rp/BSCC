Component({
  properties: {
    title: { type: String, value: "" },
    showBack: { type: Boolean, value: false },
    bg: { type: String, value: "#f5f7f8" }
  },

  data: {
    statusBarHeight: 20,
    navBodyHeight: 44
  },

  lifetimes: {
    attached() {
      const windowInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
      const statusBarHeight = windowInfo.statusBarHeight || 20;
      let navBodyHeight = 44;
      try {
        const menu = wx.getMenuButtonBoundingClientRect();
        if (menu && menu.height) {
          navBodyHeight = (menu.top - statusBarHeight) * 2 + menu.height;
        }
      } catch (e) {
        // 使用默认高度
      }
      this.setData({ statusBarHeight, navBodyHeight });
    }
  },

  methods: {
    handleBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        wx.navigateBack({ delta: 1 });
      } else {
        wx.reLaunch({ url: "/pages/upload/index" });
      }
    }
  }
});
