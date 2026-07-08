const PREVIEW_ERROR_TEXT = "当前文件暂不能预览，请稍后重试";
const DOWNLOAD_ERROR_TEXT = "文件下载失败，请稍后重试";

const OPEN_FILE_TYPES = {
  doc: true,
  docx: true,
  xls: true,
  xlsx: true,
  ppt: true,
  pptx: true,
  pdf: true
};

function getFileType(fileName) {
  const value = String(fileName || "").split("?")[0];
  const matched = value.match(/\.([^.\\/]+)$/);
  if (!matched) {
    return "";
  }
  const extension = matched[1].toLowerCase();
  return OPEN_FILE_TYPES[extension] ? extension : "";
}

function showToast(title) {
  wx.showToast({
    title: title || PREVIEW_ERROR_TEXT,
    icon: "none",
    duration: 2200
  });
}

function downloadFile(url) {
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url,
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300 && response.tempFilePath) {
          resolve(response.tempFilePath);
          return;
        }
        reject({
          message: response.statusCode === 404 ? "当前文件暂未生成，请稍后重试" : DOWNLOAD_ERROR_TEXT
        });
      },
      fail(error) {
        reject({
          message: error && error.errMsg ? DOWNLOAD_ERROR_TEXT : PREVIEW_ERROR_TEXT
        });
      }
    });
  });
}

function openDocument(filePath, fileName) {
  return new Promise((resolve, reject) => {
    const fileType = getFileType(fileName);
    const options = {
      filePath,
      showMenu: true,
      success() {
        resolve(true);
      },
      fail() {
        reject({
          message: PREVIEW_ERROR_TEXT
        });
      }
    };

    if (fileType) {
      options.fileType = fileType;
    }

    wx.openDocument(options);
  });
}

async function downloadAndOpenFile(options) {
  const finalOptions = options || {};
  if (!finalOptions.url) {
    showToast(PREVIEW_ERROR_TEXT);
    return false;
  }

  wx.showLoading({
    title: finalOptions.loadingText || "正在打开文档",
    mask: true
  });

  try {
    const tempFilePath = await downloadFile(finalOptions.url);
    await openDocument(tempFilePath, finalOptions.fileName || "");
    return true;
  } catch (error) {
    showToast(error && error.message ? error.message : PREVIEW_ERROR_TEXT);
    return false;
  } finally {
    wx.hideLoading();
  }
}

module.exports = {
  downloadAndOpenFile
};
