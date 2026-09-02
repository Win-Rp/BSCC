const path = require("path");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

let assertCount = 0;
const assert = (cond, msg) => {
  console.log(cond ? "PASS" : "FAIL", msg);
  assertCount++;
  if (!cond) process.exitCode = 1;
};

const { centsToYuan, formatMoney } = require(path.join(cwd, "utils/format.js"));

console.log("=== centsToYuan 单元测试（对齐 BS 端逻辑） ===");
assert(centsToYuan(1000) === 10, "1000 分 → 10 元");
assert(centsToYuan(100) === 1, "100 分 → 1 元");
assert(centsToYuan(255) === 2.55, "255 分 → 2.55 元");
assert(centsToYuan(256) === 2.56, "256 分 → 2.56 元");
assert(centsToYuan(1) === 0.01, "1 分 → 0.01 元");
assert(centsToYuan(0) === 0, "0 分 → 0 元");
assert(centsToYuan(null) === 0, "null → 0 元");
assert(centsToYuan(undefined) === 0, "undefined → 0 元");
assert(centsToYuan("990") === 9.9, "字符串 990 分 → 9.9 元（后台促销价）");

console.log("\n=== formatMoney 展示格式 ===");
assert(formatMoney(1000) === "¥10.00", "1000 分 → ¥10.00");
assert(formatMoney(100) === "¥1.00", "100 分 → ¥1.00");
assert(formatMoney(990) === "¥9.90", "990 分 → ¥9.90");
assert(formatMoney(0) === "¥0.00", "0 分 → ¥0.00");
assert(formatMoney(null) === "¥0.00", "null → ¥0.00");
assert(formatMoney(333.33) === "¥3.33", "非整数分（总价/份数回退场景）→ ¥3.33");
assert(formatMoney(3000) === "¥30.00", "3000 分 → ¥30.00");

console.log("\n=== unlock-bar 端到端（真实分值配置） ===");
let componentInstance = null;
let triggered = [];
global.Component = (config) => {
  componentInstance = {
    data: JSON.parse(JSON.stringify(config.data || {})),
    setData(obj) { Object.assign(this.data, obj); },
    triggerEvent(name) { triggered.push(name); }
  };
  for (const key of Object.keys(config.methods || {})) componentInstance[key] = config.methods[key];
  componentInstance.__observers = config.observers || {};
};
global.setInterval = () => 1;
global.clearInterval = () => {};
global.wx = {};

delete require.cache[path.join(cwd, "components/unlock-bar/index.js")];
require(path.join(cwd, "components/unlock-bar/index.js"));

function setProps(summary, unlocked, promo) {
  componentInstance.data.summary = summary;
  componentInstance.data.unlocked = unlocked;
  componentInstance.data.promo = promo;
  componentInstance.__observers["summary, unlocked, promo"].call(componentInstance);
}

// 线上真实配置：原价 1000 分/份，促销 990 分/份（当前线上促销已过期，再测一个生效场景）
const PROMO = {
  original_unit_price_cents: 1000,
  promo_unit_price_cents: 100,
  effective_unit_price_cents: 100,
  promo_enabled: true,
  promo_active: true,
  show_countdown: false,
  server_now: new Date().toISOString()
};
setProps({ payment_required: true, b_file_count: 5, unlock_status: "locked" }, false, PROMO);
let vm = componentInstance.data.viewModel;
assert(vm.priceText === "¥5.00", "促销 ¥1/份 × 5 份 = ¥5.00（实际: " + vm.priceText + "）");
assert(vm.strikeText === "¥50.00", "原价划线 ¥10 × 5 = ¥50.00");
assert(vm.savingsText === "¥45.00", "立省 ¥45.00");
assert(vm.unitPriceText === "¥1.00 / 份", "单价 ¥1.00 / 份");

// 原价场景（促销过期）：¥10 × 2 份
const NO_PROMO = {
  original_unit_price_cents: 1000,
  promo_unit_price_cents: 100,
  effective_unit_price_cents: 1000,
  promo_enabled: false,
  promo_active: false,
  show_countdown: false,
  server_now: new Date().toISOString()
};
setProps({ payment_required: true, b_file_count: 2, unlock_status: "locked" }, false, NO_PROMO);
vm = componentInstance.data.viewModel;
assert(vm.priceText === "¥20.00", "原价 ¥10/份 × 2 份 = ¥20.00（实际: " + vm.priceText + "）");

console.log(`\n共 ${assertCount} 项断言完成`);
