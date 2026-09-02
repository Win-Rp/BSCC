const path = require("path");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

let assertCount = 0;
const assert = (cond, msg) => {
  console.log(cond ? "PASS" : "FAIL", msg);
  assertCount++;
  if (!cond) process.exitCode = 1;
};

// ---------- 1. unlock-bar 组件优惠卡逻辑 ----------
let componentInstance = null;
let triggered = [];
global.Component = (config) => {
  componentInstance = {
    data: JSON.parse(JSON.stringify(config.data || {})),
    properties: config.properties || {},
    setData(obj) { Object.assign(this.data, obj); },
    triggerEvent(name) { triggered.push(name); }
  };
  for (const key of Object.keys(config.methods || {})) {
    componentInstance[key] = config.methods[key];
  }
  for (const key of Object.keys(config.lifetimes || {})) {
    componentInstance["__lifetime_" + key] = config.lifetimes[key];
  }
  componentInstance.__observers = config.observers || {};
};

global.setInterval = () => 1;
global.clearInterval = () => {};
global.wx = {};

require(path.join(cwd, "components/unlock-bar/index.js"));

function setProps(summary, unlocked, promo) {
  componentInstance.data.summary = summary;
  componentInstance.data.unlocked = unlocked;
  componentInstance.data.promo = promo;
  componentInstance.__observers["summary, unlocked, promo"].call(componentInstance);
}

const PROMO_ACTIVE = {
  original_unit_price_cents: 1000,
  promo_unit_price_cents: 100,
  effective_unit_price_cents: 100,
  promo_enabled: true,
  promo_active: true,
  show_countdown: true,
  promo_note: "限时活动，仅限当前批次查重任务",
  promo_badge: "限时特惠",
  promo_loss_aversion_text: "错过后将恢复原价",
  promo_ends_at: new Date(Date.now() + 3600 * 1000).toISOString(),
  server_now: new Date().toISOString()
};

const PROMO_OFF = {
  original_unit_price_cents: 1000,
  promo_unit_price_cents: 100,
  effective_unit_price_cents: 1000,
  promo_enabled: false,
  promo_active: false,
  show_countdown: false,
  server_now: new Date().toISOString()
};

console.log("=== unlock-bar 组件 ===");

// 免费任务（未超免费额度）：不显示任何卡
setProps({ payment_required: false, b_file_count: 1, unlock_status: "free" }, false, PROMO_ACTIVE);
assert(componentInstance.data.viewModel === null, "免费任务不显示解锁卡（未触发免费额度上限）");

// 付费任务未解锁 + 促销：显示解锁卡与优惠价格
setProps({ payment_required: true, b_file_count: 3, unlock_status: "locked" }, false, PROMO_ACTIVE);
const vm = componentInstance.data.viewModel;
assert(vm && vm.locked === true, "付费未解锁任务显示锁定解锁卡");
assert(vm.priceText === "¥3.00", "促销总价 = 单价 ¥1.00 × 3 份（实际: " + vm.priceText + "）");
assert(vm.strikeText === "¥30.00", "原价划线 = ¥10.00 × 3 份");
assert(vm.savingsText === "¥27.00", "立省金额正确");
assert(vm.badge === "限时特惠", "促销徽标显示");
assert(vm.unitPriceText === "¥1.00 / 份", "单价文案正确");
assert(vm.showCountdown === true, "显示促销倒计时");
assert(componentInstance.data.countdownText.length > 0, "倒计时文本已生成");

// 已解锁（已支付）：显示已解锁状态，无价格
setProps({ payment_required: true, b_file_count: 3, unlock_status: "unlocked" }, true, PROMO_ACTIVE);
const vm2 = componentInstance.data.viewModel;
assert(vm2 && vm2.locked === false, "已解锁任务显示已解锁状态");
assert(vm2.priceText === "", "已解锁状态不显示价格");

// 付费任务 + 无促销：按原价显示，无立省/徽标/倒计时
setProps({ payment_required: true, b_file_count: 2, unlock_status: "locked" }, false, PROMO_OFF);
const vm3 = componentInstance.data.viewModel;
assert(vm3.locked === true, "无促销时仍显示解锁卡");
assert(vm3.priceText === "¥20.00", "无促销按原价总价显示（实际: " + vm3.priceText + "）");
assert(vm3.savingsText === "" && vm3.badge === "" && vm3.showCountdown === false, "无促销时不显示立省/徽标/倒计时");

// 促销配置缺失（siteConfig 未加载）：价格降级文案
setProps({ payment_required: true, b_file_count: 2, unlock_status: "locked" }, false, null);
const vm4 = componentInstance.data.viewModel;
assert(vm4.locked === true && vm4.priceText === "以下单页为准", "无定价配置时降级为引导文案");

// 按钮事件
setProps({ payment_required: true, b_file_count: 3, unlock_status: "locked" }, false, PROMO_ACTIVE);
triggered = [];
componentInstance.handleUnlock();
assert(triggered.indexOf("unlock") >= 0, "解锁按钮触发 unlock 事件");
triggered = [];
componentInstance.handleView();
assert(triggered.indexOf("view") >= 0, "查看按钮触发 view 事件");

// ---------- 2. 上传页无价格展示 ----------
console.log("\n=== 上传页 ===");
const fs = require("fs");
const uploadSource = fs.readFileSync(path.join(cwd, "pages/upload/index.js"), "utf8");
const uploadWxml = fs.readFileSync(path.join(cwd, "pages/upload/index.wxml"), "utf8");
const uploadWxss = fs.readFileSync(path.join(cwd, "pages/upload/index.wxss"), "utf8");

assert(!/promoCard/.test(uploadSource) && !/priceText/.test(uploadSource), "上传页 JS 无促销卡/价格逻辑");
assert(!/promoCard/.test(uploadWxml) && !/priceText/.test(uploadWxml), "上传页 WXML 无促销横幅/价格显示");
assert(!/promo-banner/.test(uploadWxml) && !/promo-banner/.test(uploadWxss), "上传页促销横幅结构与样式已移除");
assert(/首份 B 文件免费对比/.test(uploadSource), "规则文案提示免费额度与解锁路径");

// 上传页页面模块可正常加载
delete require.cache[path.join(cwd, "pages/upload/index.js")];
let uploadPage = null;
global.Page = (config) => { uploadPage = config; };
require(path.join(cwd, "pages/upload/index.js"));
assert(uploadPage && typeof uploadPage.submitTask === "function", "上传页模块加载正常");
assert(!("priceText" in uploadPage.data) && !("promoCard" in uploadPage.data), "上传页 data 无价格字段");

// ---------- 3. 结果页传参 ----------
console.log("\n=== 结果页 ===");
const resultsWxml = fs.readFileSync(path.join(cwd, "pages/results/index.wxml"), "utf8");
const resultsSource = fs.readFileSync(path.join(cwd, "pages/results/index.js"), "utf8");
assert(/promo="\{\{promoConfig\}\}"/.test(resultsWxml), "结果页向 unlock-bar 传入 promo 配置");
assert(/promoConfig/.test(resultsSource), "结果页 JS 注入 promoConfig");

console.log(`\n共 ${assertCount} 项断言完成`);
