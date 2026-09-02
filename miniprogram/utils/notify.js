const api = require("../services/api");

const DEFAULT_TEMPLATE_ID = "0EWR6EdE5PZwTy3op4CIwxMH950vcLvBdPT5tBD1jkA";
const OPENID_CACHE_KEY = "bscc_openid";
const UNIONID_CACHE_KEY = "bscc_unionid";

function resolveTemplateId() {
  try {
    const app = getApp();
    const id = app && app.globalData && app.globalData.siteConfig && app.globalData.siteConfig.notify_template_id;
    if (id) {
      return id;
    }
  } catch (e) {
    // getApp 不可用时使用默认模板
  }
  return DEFAULT_TEMPLATE_ID;
}

function getCachedOpenid() {
  try {
    return wx.getStorageSync(OPENID_CACHE_KEY) || "";
  } catch (e) {
    return "";
  }
}

function getCachedUnionid() {
  try {
    return wx.getStorageSync(UNIONID_CACHE_KEY) || "";
  } catch (e) {
    return "";
  }
}

function cacheUser(openid, unionid) {
  try {
    wx.setStorageSync(OPENID_CACHE_KEY, openid || "");
    if (unionid) {
      wx.setStorageSync(UNIONID_CACHE_KEY, unionid);
    }
  } catch (e) {
    // 存储失败不影响主流程
  }
}

function requestSubscribe() {
  return new Promise((resolve) => {
    const templateId = resolveTemplateId();
    if (!templateId) {
      resolve(false);
      return;
    }
    wx.requestSubscribeMessage({
      tmplIds: [templateId],
      success: (res) => {
        resolve(res[templateId] === "accept");
      },
      fail: () => {
        resolve(false);
      }
    });
  });
}

function login() {
  return new Promise((resolve) => {
    wx.login({
      success: (res) => {
        resolve(res.code || "");
      },
      fail: () => {
        resolve("");
      }
    });
  });
}

async function ensureNotifyReady() {
  // 一次性订阅消息：每次授权只能推送一条，因此每次提交都要请求授权累积额度
  const accepted = await requestSubscribe();
  if (!accepted) {
    return { openid: "", unionid: "", subscribed: false };
  }

  let openid = getCachedOpenid();
  if (openid) {
    return { openid, unionid: getCachedUnionid(), subscribed: true };
  }

  const code = await login();
  if (!code) {
    return { openid: "", unionid: "", subscribed: false };
  }

  const response = await api.wxLogin(code);
  if (!response.success || !response.data || !response.data.openid) {
    return { openid: "", unionid: "", subscribed: false };
  }

  openid = response.data.openid;
  cacheUser(openid, response.data.unionid);
  return { openid, unionid: response.data.unionid || "", subscribed: true };
}

module.exports = {
  ensureNotifyReady,
  getCachedOpenid,
  getCachedUnionid,
  requestSubscribe,
  resolveTemplateId
};
