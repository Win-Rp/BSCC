const { request, upload, buildURL } = require("../utils/request");

function createTask(payload) {
  return upload("/api/tasks", {
    filePath: payload.aFile.path,
    name: "a_file",
    files: (payload.bFiles || []).map((item) => ({
      name: "b_files",
      uri: item.path
    })),
    formData: {
      keywords: payload.keywords || ""
    }
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
