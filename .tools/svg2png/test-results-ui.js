const path = require("path");
const fs = require("fs");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

let assertCount = 0;
const assert = (cond, msg) => {
  console.log(cond ? "PASS" : "FAIL", msg);
  assertCount++;
  if (!cond) process.exitCode = 1;
};

const source = fs.readFileSync(path.join(cwd, "pages/results/index.js"), "utf8");

// 提取页面级纯函数
const fnOverview = source.match(/function buildOverview[\s\S]*?\n}/)[0];
const fnPreview = source.match(/function buildPreviewList[\s\S]*?\n}/)[0];
const fnMeta = source.match(/function buildSummaryMeta[\s\S]*?\n}/)[0];

// 依赖注入：format 工具
const { formatPercent, formatDateTime, getRiskLevel, ellipsis } = require(path.join(cwd, "utils/format.js"));
const buildOverview = new Function("getFillClass_placeholder", "formatPercent", "getRiskLevel", `
  ${source.match(/function getFillClass[\s\S]*?\n}/)[0]}
  ${fnOverview}
  return buildOverview;
`)(null, formatPercent, getRiskLevel);
const buildPreviewList = new Function("formatPercent", "ellipsis", `${fnPreview}; return buildPreviewList;`)(formatPercent, ellipsis);
const buildSummaryMeta = new Function("formatDateTime", "getUnlockStatusText", `${fnMeta}; return buildSummaryMeta;`)(formatDateTime, () => "免费可看");

console.log("=== buildOverview：总相似度 hero 与细分 ===");
const selected = {
  total_similarity: 0.2254,
  exact_similarity: 0.1148,
  rewrite_similarity: 0.0318,
  semantic_similarity: 0.0788,
  format_similarity: 0.5636,
  metadata_similarity: 0.1667
};
const ov = buildOverview({ task_no: "T1" }, selected);
assert(ov.totalMetric.valueText === "22.54%", "总相似度 hero 文案（实际: " + ov.totalMetric.valueText + "）");
assert(ov.totalMetric.riskType === "safe" && ov.totalMetric.riskText === "低风险", "总相似度风险判定为低风险");
assert(ov.details.length === 5, "细分指标为 5 项（总相似度已分离）");
assert(ov.details.every((d) => d.label !== "总相似度"), "细分项中不再包含总相似度");
const fmt = ov.details.find((d) => d.label === "格式相似");
assert(fmt.value === "56.36%" && fmt.percent === 56 && fmt.fillClass === "bar-row__fill--warning", "格式相似 56.36% 高亮 warning（解释橙色）");

const ovHigh = buildOverview({}, { total_similarity: 0.9, exact_similarity: 0.8, rewrite_similarity: 0.1, semantic_similarity: 0.2, format_similarity: 0.3, metadata_similarity: 0.4 });
assert(ovHigh.totalMetric.riskType === "danger", "90% 总相似度 → danger");
const ovMid = buildOverview({}, { total_similarity: 0.6, exact_similarity: 0.2, rewrite_similarity: 0.1, semantic_similarity: 0.1, format_similarity: 0.3, metadata_similarity: 0.2 });
assert(ovMid.totalMetric.riskType === "warning", "60% 总相似度 → warning");

assert(buildOverview(null, null).totalMetric === null && buildOverview(null, null).details.length === 0, "无选中结果时返回空结构");

console.log("\n=== buildPreviewList：A/B 标识与页码 ===");
const previews = buildPreviewList({
  segments: [
    { match_type: "exact", similarity: 1.0, a_text: "A文本", b_text: "B文本", a_position: { page: 4 }, b_position: { page: 17 } },
    { match_type: "rewrite", similarity: 0.8, a_text: "x", b_text: "y", a_position: null, b_position: { page: 2 } },
    { match_type: "semantic", similarity: 0.7, a_text: "x", b_text: "y" }
  ]
});
assert(previews[0].typeText === "完全重复" && previews[0].typeClass === "tag-danger", "完全重复 → 红色标签");
assert(previews[1].typeClass === "tag-warning", "改写相似 → 橙色标签");
assert(previews[2].typeClass === "", "语义相似 → 默认青色标签");
assert(previews[0].aPage === 4 && previews[0].bPage === 17, "A/B 页码拆分字段");
assert(previews[1].aPage === "-" && previews[1].bPage === 2, "缺失位置回退 -");
assert(!("positionText" in previews[0]), "旧的拼接位置字段已移除");

console.log("\n=== buildSummaryMeta：去除冗余行 ===");
const meta = buildSummaryMeta({
  task_no: "T20260902102534B281",
  mode: "single",
  unlock_status: "free",
  expires_at: "2026-09-09T10:25:00",
  a_file: { name: "A文件.pdf" },
  results: [{ b_file_name: "B1.pdf" }]
}, { b_file_name: "B1.pdf" }, true);
assert(meta.taskNo === "T20260902102534B281", "任务号保留");
assert(!("currentResultText" in meta), "「当前结果」冗余行已移除（与解锁 chips 重复）");
assert(meta.modeText === "单份对比" && meta.bFileCount === 1 && meta.selectedBFileName === "B1.pdf", "chips 与文件行字段齐备");
assert(buildSummaryMeta(null, null, false) === null, "无 summary 返回 null");

console.log("\n=== 页面模块加载与 data 结构 ===");
let pageConfig = null;
global.Page = (config) => { pageConfig = config; };
global.getApp = () => ({ globalData: { siteConfig: {} } });
global.wx = { showToast() {}, navigateTo() {}, redirectTo() {}, setClipboardData() {} };
require(path.join(cwd, "pages/results/index.js"));
assert(pageConfig && typeof pageConfig.loadSummary === "function", "结果页模块加载正常");
assert("overviewData" in pageConfig.data && pageConfig.data.overviewData.details.length === 0, "data 含 overviewData 空结构");

console.log("\n=== WXML 关键结构 ===");
const wxml = fs.readFileSync(path.join(cwd, "pages/results/index.wxml"), "utf8");
assert(/metric-hero__score--\{\{overviewData\.totalMetric\.riskType\}\}/.test(wxml), "总相似度 hero 按风险着色");
assert(/preview-item__block--a/.test(wxml) && /preview-item__block--b/.test(wxml), "预览 A/B 块视觉区分");
assert(/meta-chip/.test(wxml) && /file-badge--a/.test(wxml), "任务卡 chips + A/B 文件徽标");
assert(!/操作区/.test(wxml), "「操作区」系统文案已移除");
assert(!/recovery-btn/.test(wxml), "恢复任务按钮移出操作区");
assert(/footer-link/.test(wxml), "底部提供找回历史任务小链接");
assert(/compare-cta/.test(wxml) && /result-actions-row/.test(wxml), "主按钮全宽 + 次要按钮横排");
assert(/overview-note/.test(wxml), "格式/元数据相似度解释文案");
assert(!/currentResultText/.test(wxml) && !/summary-head/.test(wxml), "旧结构残留已清除");

// result-card 风险着色
const cardWxml = fs.readFileSync(path.join(cwd, "components/result-card/index.wxml"), "utf8");
assert(/result-card__score--\{\{viewModel\.riskType\}\}/.test(cardWxml), "result-card 总相似度按风险着色");

console.log(`\n共 ${assertCount} 项断言完成`);
