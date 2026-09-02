const env = require("../config/env");

function buildURL(path) {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  return `${env.baseURL}${path}`;
}

function friendlyNetworkError(rawMsg, fallback) {
  const msg = String(rawMsg || "");
  if (/domain list/i.test(msg)) {
    return "接口域名不在白名单：请在开发者工具「详情-本地设置」勾选「不校验合法域名」，或在小程序后台配置合法域名";
  }
  if (/tls|ssl|socket/i.test(msg)) {
    return "网络连接异常，请检查网络或代理设置后重试";
  }
  if (/timeout|timed?\s*out/i.test(msg)) {
    return "网络请求超时，请稍后重试";
  }
  return fallback;
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
            message: friendlyNetworkError(error.errMsg, "网络异常，请稍后重试")
          },
          statusCode: 0
        });
      }
    });
  });
}

function upload(path, options) {
  const finalOptions = options || {};
  const boundary = `----bsccform${Date.now()}${Math.floor(Math.random() * 1000000)}`;
  const files = finalOptions.files || [];
  const formData = finalOptions.formData || {};

  return buildMultipartBody(formData, files, boundary)
    .then((body) => new Promise((resolve) => {
      wx.request({
        url: buildURL(path),
        method: "POST",
        header: {
          "Content-Type": `multipart/form-data; boundary=${boundary}`
        },
        data: body,
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
              message: friendlyNetworkError(error.errMsg, "上传失败，请稍后重试")
            },
            statusCode: 0
          });
        }
      });
    }))
    .catch((error) => ({
      success: false,
      data: null,
      error: {
        code: "UPLOAD_FAILED",
        message: (error && error.message) || "读取文件失败，请重新选择文件"
      },
      statusCode: 0
    }));
}

const MIME_BY_EXT = {
  doc: "application/msword",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  pdf: "application/pdf"
};

function utf8Encode(str) {
  const text = String(str == null ? "" : str);
  const bytes = [];
  for (let i = 0; i < text.length; i++) {
    let code = text.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff && i + 1 < text.length) {
      const next = text.charCodeAt(i + 1);
      if (next >= 0xdc00 && next <= 0xdfff) {
        code = 0x10000 + ((code - 0xd800) << 10) + (next - 0xdc00);
        i++;
      }
    }
    if (code < 0x80) {
      bytes.push(code);
    } else if (code < 0x800) {
      bytes.push(0xc0 | (code >> 6), 0x80 | (code & 0x3f));
    } else if (code < 0x10000) {
      bytes.push(0xe0 | (code >> 12), 0x80 | ((code >> 6) & 0x3f), 0x80 | (code & 0x3f));
    } else {
      bytes.push(0xf0 | (code >> 18), 0x80 | ((code >> 12) & 0x3f), 0x80 | ((code >> 6) & 0x3f), 0x80 | (code & 0x3f));
    }
  }
  return new Uint8Array(bytes);
}

function concatBytes(chunks) {
  let total = 0;
  for (const chunk of chunks) total += chunk.length;
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.length;
  }
  return out;
}

function readFileAsync(filePath) {
  return new Promise((resolve, reject) => {
    wx.getFileSystemManager().readFile({
      filePath,
      success(res) {
        resolve(res.data);
      },
      fail(err) {
        reject(new Error(err.errMsg || `读取文件失败：${filePath}`));
      }
    });
  });
}

function escapeFilename(name) {
  return String(name || "file").replace(/"/g, "'");
}

async function buildMultipartBody(formData, files, boundary) {
  const chunks = [];

  for (const key of Object.keys(formData)) {
    const value = formData[key];
    if (value === undefined || value === null) continue;
    chunks.push(utf8Encode(`--${boundary}\r\nContent-Disposition: form-data; name="${key}"\r\n\r\n`));
    chunks.push(utf8Encode(value));
    chunks.push(utf8Encode("\r\n"));
  }

  for (const file of files) {
    const filename = escapeFilename(file.filename || file.filePath);
    const dot = filename.lastIndexOf(".");
    const ext = dot >= 0 ? filename.slice(dot + 1).toLowerCase() : "";
    const mime = MIME_BY_EXT[ext] || "application/octet-stream";
    chunks.push(
      utf8Encode(
        `--${boundary}\r\nContent-Disposition: form-data; name="${file.name}"; filename="${filename}"\r\nContent-Type: ${mime}\r\n\r\n`
      )
    );
    const content = await readFileAsync(file.filePath);
    chunks.push(new Uint8Array(content));
    chunks.push(utf8Encode("\r\n"));
  }

  chunks.push(utf8Encode(`--${boundary}--\r\n`));
  return concatBytes(chunks).buffer;
}

module.exports = {
  buildURL,
  request,
  upload
};
