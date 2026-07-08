const KEYS = {
  TASK_NO: "bscc_task_no",
  ORDER_NO: "bscc_order_no",
  RECOVERY_INFO: "bscc_recovery_info"
};

function safeSet(key, value) {
  try {
    wx.setStorageSync(key, value);
  } catch (error) {
    console.warn("storage set failed", key, error);
  }
}

function safeGet(key, defaultValue) {
  try {
    const value = wx.getStorageSync(key);
    return value === "" || typeof value === "undefined" ? defaultValue : value;
  } catch (error) {
    console.warn("storage get failed", key, error);
    return defaultValue;
  }
}

function safeRemove(key) {
  try {
    wx.removeStorageSync(key);
  } catch (error) {
    console.warn("storage remove failed", key, error);
  }
}

function setTaskNo(taskNo) {
  safeSet(KEYS.TASK_NO, taskNo || "");
}

function getTaskNo() {
  return safeGet(KEYS.TASK_NO, "");
}

function setOrderNo(orderNo) {
  safeSet(KEYS.ORDER_NO, orderNo || "");
}

function getOrderNo() {
  return safeGet(KEYS.ORDER_NO, "");
}

function setRecoveryInfo(payload) {
  const current = getRecoveryInfo();
  safeSet(KEYS.RECOVERY_INFO, Object.assign({}, current, payload || {}));
}

function getRecoveryInfo() {
  return safeGet(KEYS.RECOVERY_INFO, {
    taskNo: "",
    orderNo: "",
    contact: ""
  });
}

function clearRecoveryInfo() {
  safeRemove(KEYS.RECOVERY_INFO);
}

function setTaskContext(payload) {
  const nextValue = Object.assign({}, getRecoveryInfo(), payload || {});
  if (nextValue.taskNo) {
    setTaskNo(nextValue.taskNo);
  }
  if (nextValue.orderNo) {
    setOrderNo(nextValue.orderNo);
  }
  setRecoveryInfo(nextValue);
}

module.exports = {
  KEYS,
  setTaskNo,
  getTaskNo,
  setOrderNo,
  getOrderNo,
  setRecoveryInfo,
  getRecoveryInfo,
  clearRecoveryInfo,
  setTaskContext
};
