const { request, upload, buildURL } = require("../utils/request");

function createTask(payload) {
  const files = [
    {
      name: "a_file",
      filePath: payload.aFile.path,
      filename: payload.aFile.name
    }
  ].concat(
    (payload.bFiles || []).map((item) => ({
      name: "b_files",
      filePath: item.path,
      filename: item.name
    }))
  );

  return upload("/api/tasks", {
    files,
    formData: {
      keywords: payload.keywords || "",
      notify_openid: payload.notifyOpenid || ""
    }
  });
}

function wxLogin(code) {
  return request("/api/wx/login", {
    method: "POST",
    data: { code }
  });
}

function getTaskStatus(taskNo) {
  return request(`/api/tasks/${encodeURIComponent(taskNo)}/status`);
}

function getTaskSummary(taskNo) {
  return request(`/api/tasks/${encodeURIComponent(taskNo)}/summary`);
}

function getPreview(taskNo, compareResultId) {
  return request(`/api/tasks/${encodeURIComponent(taskNo)}/results/${compareResultId}/preview`);
}

function getDetail(taskNo, compareResultId) {
  return request(`/api/tasks/${encodeURIComponent(taskNo)}/results/${compareResultId}/detail`);
}

function createOrder(payload) {
  return request("/api/orders", {
    method: "POST",
    data: payload
  });
}

function getOrderStatus(orderNo) {
  return request(`/api/orders/${encodeURIComponent(orderNo)}/status`);
}

function recoverTask(payload) {
  return request("/api/recover", {
    method: "POST",
    data: payload
  });
}

function getSupport() {
  return request("/api/support");
}

function getSiteConfig() {
  return request("/api/public/site-config");
}

function getAFileURL(taskNo) {
  return buildURL(`/api/tasks/${encodeURIComponent(taskNo)}/file/a`);
}

function getBFileURL(taskNo, resultId) {
  return buildURL(`/api/tasks/${encodeURIComponent(taskNo)}/file/b/${resultId}`);
}

module.exports = {
  createTask,
  wxLogin,
  getTaskStatus,
  getTaskSummary,
  getPreview,
  getDetail,
  createOrder,
  getOrderStatus,
  recoverTask,
  getSupport,
  getSiteConfig,
  getAFileURL,
  getBFileURL
};
