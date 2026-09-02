const path = require("path");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

let pageInstance = null;
let chooseHandler = null;

global.Page = (config) => {
  pageInstance = {
    data: JSON.parse(JSON.stringify(config.data)),
    setData(obj) { Object.assign(this.data, obj); }
  };
  for (const key of Object.keys(config)) {
    if (key !== "data") pageInstance[key] = config[key];
  }
};
global.getApp = () => ({ globalData: { siteConfig: {} } });
global.wx = {
  chooseMessageFile(opts) {
    chooseHandler = opts;
    // 记录调用参数供断言
    chooseHandler.lastOptions = opts;
  },
  showToast(o) { chooseHandler.toast = o; },
  navigateTo() {}
};

require(path.join(cwd, "pages/upload/index.js"));

const assert = (cond, msg) => {
  console.log(cond ? "PASS" : "FAIL", msg);
  if (!cond) process.exitCode = 1;
};

function pickA(fileName) {
  pageInstance.chooseAFile();
  chooseHandler.success({ tempFiles: [{ name: fileName, path: "wxfile://tmp/x", size: 100 }] });
}

function pickB(fileNames) {
  pageInstance.chooseBFiles();
  chooseHandler.success({ tempFiles: fileNames.map((n) => ({ name: n, path: "wxfile://tmp/" + n, size: 100 })) });
}

// 1. A 文件：合法扩展名
pickA("主标书.docx");
assert(pageInstance.data.aFile && pageInstance.data.aFile.name === "主标书.docx", "A 选择 .docx 被接受");

// 2. A 文件：非法扩展名（应保留原选择，不被覆盖）
pickA("旧格式标书.doc");
assert(pageInstance.data.aFile && pageInstance.data.aFile.name === "主标书.docx", "A 选择 .doc 被拒绝（保留原有文件）");
assert(/仅支持 DOCX、PDF/.test(pageInstance.data.errorText), "A 拒绝时给出格式错误提示");

// 3. A 文件：大写扩展名
pickA("标书.PDF");
assert(pageInstance.data.aFile && pageInstance.data.aFile.name === "标书.PDF", "A 选择 .PDF（大写）被接受");

// 4. B 文件：混合合法与非法
pageInstance.setData({ bFiles: [], errorText: "" });
pickB(["合法一.docx", "非法.doc", "合法二.pdf", "无扩展名"]);
assert(pageInstance.data.bFiles.length === 2, "B 混合选择时仅保留 2 个合法文件");
assert(pageInstance.data.bFiles.map((f) => f.name).join(",") === "合法一.docx,合法二.pdf", "B 保留的文件正确");
assert(chooseHandler.toast && /已跳过不支持的文件/.test(chooseHandler.toast.title), "B 跳过非法文件时有 toast 提示");

// 5. B 文件：全部非法
pageInstance.setData({ bFiles: [], errorText: "" });
chooseHandler.toast = null;
pickB(["a.doc", "b.txt"]);
assert(pageInstance.data.bFiles.length === 0, "B 全部非法时不添加任何文件");
assert(/仅支持 DOCX、PDF/.test(pageInstance.data.errorText), "B 全部非法时给出错误提示");

// 6. 选择器 extension 参数收紧
pickA("重新触发.js");
const ext = chooseHandler.lastOptions.extension;
assert(Array.isArray(ext) && ext.length === 2 && ext.includes("docx") && ext.includes("pdf") && !ext.includes("doc"), "chooseMessageFile extension 参数 = [docx, pdf]");
assert(pageInstance.data.errorText === "仅支持 DOCX、PDF 格式，请重新选择", "扩展名校验兜底生效");

// 7. 底部摘要随过滤结果更新
assert(pageInstance.data.fileSummary === "尚未选择文件" || pageInstance.data.fileSummary.indexOf("B×") >= 0, "底部摘要已刷新");
