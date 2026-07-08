const env = require("../config/env");

function buildURL(path) {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  return `${env.baseURL}${path}`;
}

function parsePayload(data) {
  if (typeof data === "string") {
    try {
      return JSON.parse(data);
    } catch (error) {
      return data;
    }
  }
  return data;
}

function normalizeResponse(raw, statusCode) {
  const payload = parsePayload(raw);

  if (payload && typeof payload === "object" && typeof payload.success === "boolean") {
    return {
      success: Boolean(payload.success),
      data: payload.data || null,
      error: payload.error || null,
      statusCode
    };
  }

  if (statusCode >= 200 && statusCode < 300) {
    return {
      success: true,
      data: payload,
      error: null,
      statusCode
    };
  }

  return {
    success: false,
    data: null,
    error: {
      code: `HTTP_${statusCode}`,
      message: `请求失败：${statusCode}`
    },
    statusCode
  };
}

function request(path, options) {
  const finalOptions = options || {};

  return new Promise((resolve) => {
    wx.request({
      url: buildURL(path),
      method: finalOptions.method || "GET",
      data: finalOptions.data || null,
      header: Object.assign(
        {
          "Content-Type": "application/json"
        },
        finalOptions.header || {}
      ),
      timeout: finalOptions.timeout || env.requestTimeout,
      success(response) {
        resolve(normalizeResponse(response.data, response.statusCode));
      },
      fail(error) {
        resolve({
          success: false,
          data: null,
          error: {
            code: "NETWORK_ERROR",
            message: error.errMsg || "网络异常，请稍后重试"
          },
          statusCode: 0
        });
      }
    });
  });
}

function upload(path, options) {
  const finalOptions = options || {};

  return new Promise((resolve) => {
    wx.uploadFile({
      url: buildURL(path),
      filePath: finalOptions.filePath,
      name: finalOptions.name || "file",
      files: finalOptions.files || [],
      formData: finalOptions.formData || {},
      header: finalOptions.header || {},
      timeout: finalOptions.timeout || env.uploadTimeout,
      success(response) {
        resolve(normalizeResponse(response.data, response.statusCode));
      },
      fail(error) {
        resolve({
          success: false,
          data: null,
          error: {
            code: "UPLOAD_FAILED",
            message: error.errMsg || "上传失败，请稍后重试"
          },
          statusCode: 0
        });
      }
    });
  });
}

module.exports = {
  buildURL,
  request,
  upload
};
