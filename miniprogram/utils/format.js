function padNumber(value) {
  return String(value).padStart(2, "0");
}

function formatPercent(value) {
  const number = Number(value || 0);
  return `${(number * 100).toFixed(2)}%`;
}

// 后端与数据库统一以「分」存储价格，前端展示统一换算为「元」
const centsToYuan = (amountCents) => Number(((Number(amountCents) || 0) / 100).toFixed(2));

function formatMoney(cents) {
  return `¥${centsToYuan(cents).toFixed(2)}`;
}

function formatDateTime(input) {
  if (!input) {
    return "-";
  }
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) {
    return input;
  }
  return `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())} ${padNumber(date.getHours())}:${padNumber(date.getMinutes())}`;
}

function formatCountdown(remainingMs) {
  const totalSeconds = Math.max(Math.floor(remainingMs / 1000), 0);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${padNumber(hours)}:${padNumber(minutes)}:${padNumber(seconds)}`;
}

function buildServerOffsetMs(serverNow) {
  const serverTimestamp = Date.parse(serverNow || "");
  return Number.isNaN(serverTimestamp) ? 0 : serverTimestamp - Date.now();
}

function splitKeywords(value) {
  return String(value || "")
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinKeywords(value) {
  return splitKeywords(value).join(",");
}

function getStatusText(status) {
  const map = {
    uploaded: "文件已上传",
    queued: "任务排队中",
    parsing: "正在解析文档",
    checking: "正在查重",
    awaiting_payment: "查重完成，等待支付解锁",
    completed: "查重完成",
    failed: "任务失败",
    deleted: "任务数据已删除"
  };
  return map[status] || status || "-";
}

function getUnlockStatusText(status) {
  const map = {
    free: "免费可看",
    locked: "待解锁",
    unlocked: "已解锁"
  };
  return map[status] || status || "-";
}

function getMatchTypeText(type) {
  const map = {
    exact: "完全重复",
    rewrite: "改写相似",
    semantic: "语义相似",
    keyword: "关键字命中"
  };
  return map[type] || type || "-";
}

function getRiskLevel(score) {
  const value = Number(score || 0);
  if (value >= 0.8) {
    return { text: "高风险", type: "danger" };
  }
  if (value >= 0.5) {
    return { text: "中风险", type: "warning" };
  }
  return { text: "低风险", type: "safe" };
}

function ellipsis(text, maxLength) {
  const value = String(text || "");
  if (!maxLength || value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength)}...`;
}

module.exports = {
  formatPercent,
  formatMoney,
  centsToYuan,
  formatDateTime,
  formatCountdown,
  buildServerOffsetMs,
  splitKeywords,
  joinKeywords,
  getStatusText,
  getUnlockStatusText,
  getMatchTypeText,
  getRiskLevel,
  ellipsis
};
