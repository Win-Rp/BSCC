const api = require("../services/api");

const OPENID_CACHE_KEY = "bscc_openid";
const UNIONID_CACHE_KEY = "bscc_unionid";

function resolveTemplateId() {
  // 模板 ID 只认后台 siteConfig 下发：为空则不弹授权窗，
  // 避免前端授权模板与后端发送模板不一致导致 43101（额度恒为 0）
  try {
    const app = getApp();
    const id = app && app.globalData && app.globalData.siteConfig && app.globalData.siteConfig.notify_template_id;
    return id || "";
  } catch (e) {
    return "";
  }
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
      console.warn("[notify] siteConfig 未下发 notify_template_id，跳过授权弹窗");
      resolve(false);
      return;
    }
    wx.requestSubscribeMessage({
      tmplIds: [templateId],
      success: (res) => {
        const accepted = res[templateId] === "accept";
        console.log("[notify] 授权弹窗结果:", accepted ? "accept" : "reject", JSON.stringify(res));
        resolve(accepted);
      },
      fail: (err) => {
        console.warn("[notify] requestSubscribeMessage 调用失败:", err && err.errMsg);
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
    console.log("[notify] openid 命中本地缓存");
    return { openid, unionid: getCachedUnionid(), subscribed: true };
  }

  const code = await login();
  if (!code) {
    console.warn("[notify] wx.login 获取 code 失败");
    return { openid: "", unionid: "", subscribed: false };
  }

  const response = await api.wxLogin(code);
  if (!response.success || !response.data || !response.data.openid) {
    console.warn("[notify] wxLogin 未换到 openid:", JSON.stringify(response));
    return { openid: "", unionid: "", subscribed: false };
  }
  console.log("[notify] openid 获取成功");

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
