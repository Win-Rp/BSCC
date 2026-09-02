const path = require("path");
const https = require("https");

const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

// 生成最小合法 PDF（pypdf 可解析提取文本）
function makePdf(lines) {
  const text = lines.map((s) => s.replace(/([()\\])/g, "\\$1")).join(") Tj\n0 -16 TD (");
  const objects = [];
  objects[1] = "<< /Type /Catalog /Pages 2 0 R >>";
  objects[2] = "<< /Type /Pages /Kids [3 0 R] /Count 1 >>";
  objects[3] = "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>";
  const stream = `BT /F1 12 Tf 72 720 Td (${text}) Tj\nET`;
  objects[4] = `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`;
  objects[5] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>";

  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  for (let i = 1; i <= 5; i++) {
    offsets[i] = Buffer.byteLength(pdf, "latin1");
    pdf += `${i} 0 obj\n${objects[i]}\nendobj\n`;
  }
  const xrefPos = Buffer.byteLength(pdf, "latin1");
  pdf += "xref\n0 6\n0000000000 65535 f \n";
  for (let i = 1; i <= 5; i++) {
    pdf += String(offsets[i]).padStart(10, "0") + " 00000 n \n";
  }
  pdf += `trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xrefPos}\n%%EOF\n`;
  return Buffer.from(pdf, "latin1");
}

const A_TEXT = [
  "This is the main bid document for testing purposes.",
  "The project duration is thirty six months in total.",
  "Performance bond shall be five percent of contract value.",
  "Our company provides comprehensive maintenance services."
];
const B1_TEXT = [
  "This is the first comparison bid document for testing.",
  "The project duration is thirty six months in total.",
  "Performance bond shall be five percent of contract value.",
  "Different content to keep similarity partial."
];
const B2_TEXT = [
  "Totally unrelated text for second comparison file.",
  "Nothing matches the main document here at all.",
  "Unique paragraphs number two of second file.",
  "Unique paragraphs number three of second file."
];

const FILE_MAP = {
  "wxfile://tmp/a.docx.pdf": makePdf(A_TEXT),
  "wxfile://tmp/b1.pdf": makePdf(B1_TEXT),
  "wxfile://tmp/b2.pdf": makePdf(B2_TEXT)
};

// 模拟 wx 环境：readFile 读内存文件，request 走真实 HTTPS
global.wx = {
  getFileSystemManager() {
    return {
      readFile(opts) {
        const content = FILE_MAP[opts.filePath];
        if (!content) {
          opts.fail({ errMsg: `readFile:fail no such file ${opts.filePath}` });
          return;
        }
        opts.success({ data: content.buffer.slice(content.byteOffset, content.byteOffset + content.byteLength) });
      }
    };
  },
  request(opts) {
    const url = new URL(opts.url);
    const body = opts.data ? Buffer.from(opts.data) : null;
    const headers = Object.assign({}, opts.header);
    if (body) headers["Content-Length"] = body.length;
    const req = https.request(
      {
        hostname: url.hostname,
        path: url.pathname,
        method: opts.method || "GET",
        headers,
        timeout: opts.timeout || 30000
      },
      (res) => {
        let raw = "";
        res.on("data", (c) => (raw += c));
        res.on("end", () => opts.success({ data: raw, statusCode: res.statusCode }));
      }
    );
    req.on("error", (e) => opts.fail({ errMsg: e.message }));
    req.on("timeout", () => { req.destroy(); opts.fail({ errMsg: "timeout" }); });
    if (body) req.write(body);
    req.end();
  }
};

const api = require(path.join(cwd, "services/api.js"));

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

(async () => {
  console.log("=== 1. 创建任务（A + 2 个 B，走小程序上传层） ===");
  const res = await api.createTask({
    aFile: { name: "测试主标书.pdf", path: "wxfile://tmp/a.docx.pdf" },
    bFiles: [
      { name: "测试对比标书一.pdf", path: "wxfile://tmp/b1.pdf" },
      { name: "测试对比标书二.pdf", path: "wxfile://tmp/b2.pdf" }
    ],
    keywords: "duration,maintenance"
  });
  console.log("结果:", JSON.stringify(res, null, 2));
  if (!res.success) {
    console.error("创建失败");
    process.exit(1);
  }

  const taskNo = res.data.task_no;
  console.log("task_no =", taskNo);

  console.log("\n=== 2. 轮询任务状态 ===");
  let status = "";
  for (let i = 0; i < 30; i++) {
    await sleep(3000);
    const st = await api.getTaskStatus(taskNo);
    if (!st.success) { console.error("状态查询失败:", JSON.stringify(st)); process.exit(1); }
    status = st.data.status;
    console.log(`  [${i}] status=${status} progress=${st.data.progress}%`);
    if (["completed", "failed"].includes(status)) break;
  }

  if (status !== "completed") {
    console.error("任务未完成，status =", status);
    process.exit(1);
  }

  console.log("\n=== 3. 获取结果摘要 ===");
  const summary = await api.getTaskSummary(taskNo);
  if (!summary.success) { console.error("摘要失败:", JSON.stringify(summary)); process.exit(1); }
  console.log("mode =", summary.data.mode, "| b_file_count =", summary.data.b_file_count, "| unlock =", summary.data.unlock_status);
  console.log("A 文件:", JSON.stringify(summary.data.a_file));
  for (const r of summary.data.results) {
    console.log(`  ${r.b_file_name}: 总相似度 ${r.total_similarity}% (精确 ${r.exact_similarity}% / 改写 ${r.rewrite_similarity}%) 关键字命中 ${r.keyword_hit_count}`);
  }

  console.log("\nALL INTEGRATION ASSERTIONS PASSED");
  process.exit(0);
})().catch((e) => { console.error("FATAL:", e); process.exit(1); });
