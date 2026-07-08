const storage = require("./utils/storage");
const api = require("./services/api");

App({
  globalData: {
    siteConfig: null,
    supportInfo: null
  },

  onLaunch() {
    this.bootstrap();
  },

  bootstrap() {
    Promise.all([api.getSiteConfig(), api.getSupport()])
      .then(([siteConfigRes, supportRes]) => {
        if (siteConfigRes.success) {
          this.globalData.siteConfig = siteConfigRes.data;
        }
        if (supportRes.success) {
          this.globalData.supportInfo = supportRes.data;
        }
      })
      .catch(() => {});
  },

  setTaskContext(payload) {
    storage.setTaskContext(payload);
  }
});
