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

async function ensureOpenid() {
  let openid = getCachedOpenid();
  if (openid) {
    return openid;
  }
  const code = await login();
  if (!code) {
    console.warn("[notify] wx.login 获取 code 失败");
    return "";
  }
  const response = await api.wxLogin(code);
  if (!response.success || !response.data || !response.data.openid) {
    console.warn("[notify] wxLogin 未换到 openid:", JSON.stringify(response));
    return "";
  }
  cacheUser(response.data.openid, response.data.unionid);
  return response.data.openid;
}

async function ensureNotifyReady() {
  // 一次性订阅消息：每次授权只能推送一条，因此每次提交都要请求授权累积额度。
  // 注意：requestSubscribeMessage 必须在用户点击链路内最先调用，
  // 之后的 wx.login 网络请求不能插在弹窗之前。
  const accepted = await requestSubscribe();

  // openid 与订阅授权解耦：用户拒绝弹窗时仍要获取 openid，
  // 服务号扫码绑定（二维码场景值）依赖它，不授权订阅也不影响关注通知
  const openid = await ensureOpenid();
  if (!openid) {
    return { openid: "", unionid: "", subscribed: accepted };
  }
  return { openid, unionid: getCachedUnionid(), subscribed: accepted };
}

module.exports = {
  ensureNotifyReady,
  getCachedOpenid,
  getCachedUnionid,
  requestSubscribe,
  resolveTemplateId
};
