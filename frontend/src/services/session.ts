const TASK_KEY = "bscc.currentTaskNo";
const ORDER_KEY = "bscc.currentOrderNo";

export function saveTaskNo(taskNo: string) {
  localStorage.setItem(TASK_KEY, taskNo);
}

export function getTaskNo() {
  return localStorage.getItem(TASK_KEY) ?? "";
}

export function saveOrderNo(orderNo: string) {
  localStorage.setItem(ORDER_KEY, orderNo);
}

export function getOrderNo() {
  return localStorage.getItem(ORDER_KEY) ?? "";
}
