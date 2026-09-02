const path = require("path");
const fs = require("fs");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

let assertCount = 0;
const assert = (cond, msg) => {
  console.log(cond ? "PASS" : "FAIL", msg);
  assertCount++;
  if (!cond) process.exitCode = 1;
};

// ---------- 提取页面逻辑做隔离测试 ----------
// buildStepItems / buildViewStatus 是模块内函数，通过加载 Page 配置无法直接拿到，
// 用源码提取 + new Function 方式测试，同时验证完整模块可加载。
const source = fs.readFileSync(path.join(cwd, "pages/progress/index.js"), "utf8");

const fnStep = source.match(/function buildStepItems[\s\S]*?\n  };\n}/)[0];
const fnView = source.match(/function buildViewStatus[\s\S]*?\n}/)[0];
const fnInfer = source.match(/function inferFailedStepKey[\s\S]*?\n}/)[0];
const STATUS_ORDER = ["uploaded", "queued", "parsing", "checking", "awaiting_payment", "completed"];
const STATUS_HINTS = {
  uploaded: "", queued: "已进入队列，通常数分钟内开始处理", parsing: "正在解析文档内容，速度与文件大小相关",
  checking: "正在逐份比对标书内容，请稍候", awaiting_payment: "查重完成，正在跳转结果页…",
  completed: "查重完成，正在跳转结果页…", failed: "任务处理失败，请返回重新上传"
};
const inferFailedStepKey = new Function("return " + fnInfer)();
const buildStepItems = new Function("STATUS_ORDER", "inferFailedStepKey", "return " + fnStep)(STATUS_ORDER, inferFailedStepKey);
const buildViewStatus = new Function("STATUS_HINTS", "return " + fnView)(STATUS_HINTS);

function stateOf(status) {
  return buildStepItems(status).map((s) => `${s.label}:${s.state}`).join(" ");
}

console.log("=== 时间线状态机 ===");
console.log("  queued     →", stateOf("queued"));
console.log("  parsing    →", stateOf("parsing"));
console.log("  checking   →", stateOf("checking"));
console.log("  awaiting   →", stateOf("awaiting_payment"));
console.log("  completed  →", stateOf("completed"));
console.log("  failed@checking →", stateOf("failed"));

// queued：排队=当前，其余 pending
let steps = buildStepItems("queued");
assert(steps[0].state === "current" && steps.slice(1).every((s) => s.state === "pending"), "排队态：仅第一节点为 current");

// parsing：排队 done，解析 current
steps = buildStepItems("parsing");
assert(steps[0].state === "done" && steps[1].state === "current" && steps[2].state === "pending", "解析态：排队 done、解析 current");

// checking
steps = buildStepItems("checking");
assert(steps[0].state === "done" && steps[1].state === "done" && steps[2].state === "current", "查重态：前两步 done、查重 current");

// awaiting_payment
steps = buildStepItems("awaiting_payment");
assert(steps.slice(0, 3).every((s) => s.state === "done") && steps[3].state === "current" && steps[4].state === "pending", "待解锁态：前三步 done、待解锁 current");

// completed：全部 done
steps = buildStepItems("completed");
assert(steps.every((s) => s.state === "done"), "完成态：全部 done");

// failed（默认视为比对阶段失败）：排队/解析 done，查重 error
steps = buildStepItems("failed", "比对超时");
assert(steps[0].state === "done" && steps[1].state === "done" && steps[2].state === "error" && steps[3].state === "pending", "失败态（默认）：查重节点 error、后续 pending");

// failed（解析失败，从错误信息推断）：排队 done，解析 error
steps = buildStepItems("failed", "文档解析失败：文件损坏");
assert(steps[0].state === "done" && steps[1].state === "error" && steps[2].state === "pending", "失败态（解析失败推断）：解析节点 error");
steps = buildStepItems("failed", "PDF parse error");
assert(steps[1].state === "error", "失败态（英文 parse 关键字推断）：解析节点 error");

console.log("\n=== 视图状态 ===");
let view = buildViewStatus("checking", "");
assert(view.isFailed === false && view.isFinished === false, "checking：非失败非完成");
assert(/正在逐份比对/.test(view.statusHint), "checking：提示文案正确");

view = buildViewStatus("queued", "");
assert(/通常数分钟内开始/.test(view.statusHint), "queued：预期管理文案");

view = buildViewStatus("failed", "文档解析失败");
assert(view.isFailed === true && view.isFinished === false, "failed：失败态标记");
assert(view.statusHint === "文档解析失败", "failed：展示后端错误信息");

view = buildViewStatus("completed", "");
assert(view.isFinished === true && /正在跳转结果页/.test(view.statusHint), "completed：完成态标记");

view = buildViewStatus("awaiting_payment", "");
assert(view.isFinished === true, "awaiting_payment：完成态标记");

// ---------- 页面模块加载 + 按钮守卫 ----------
console.log("\n=== 页面模块与按钮守卫 ===");
let pageConfig = null;
let toastMessages = [];
let redirectUrls = [];
global.Page = (config) => { pageConfig = config; };
global.getApp = () => ({ globalData: { siteConfig: {} } });
global.wx = {
  showToast(o) { toastMessages.push(o.title); },
  redirectTo(o) { redirectUrls.push(o.url); },
  reLaunch() {},
  navigateTo() {},
  setClipboardData() {}
};
require(path.join(cwd, "pages/progress/index.js"));
assert(pageConfig && typeof pageConfig.gotoResults === "function", "页面模块加载正常");

// 未完成时点击"查看结果页"：拦截 + toast
toastMessages = [];
redirectUrls = [];
pageConfig.data.taskNo = "T123";
pageConfig.data.isFinished = false;
pageConfig.data.isFailed = false;
pageConfig.data.progress = 60;
pageConfig.gotoResults();
assert(toastMessages.length === 1 && /尚未完成/.test(toastMessages[0]), "未完成点击主按钮：toast 拦截");
assert(redirectUrls.length === 0, "未完成点击主按钮：不跳转");

// 完成后点击：正常跳转
pageConfig.data.isFinished = true;
pageConfig.gotoResults();
assert(redirectUrls.length === 1 && redirectUrls[0].indexOf("pages/results") >= 0, "完成后点击：跳转结果页");

// 失败态点击：允许查看任务详情
pageConfig.data.isFinished = false;
pageConfig.data.isFailed = true;
pageConfig.gotoResults();
assert(redirectUrls.length === 2, "失败态点击：允许进入结果页查看");

// 初始 data 包含新增字段
assert("statusHint" in pageConfig.data && "isFailed" in pageConfig.data && "isFinished" in pageConfig.data, "data 含新增状态字段");

console.log(`\n共 ${assertCount} 项断言完成`);
