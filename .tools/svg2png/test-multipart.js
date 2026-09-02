const path = require("path");
const fs = require("fs");

const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

// 构造假文件内容（含中文二进制不可打印字节）
const A_CONTENT = Buffer.from([0x50, 0x4b, 0x03, 0x04, 0x00, 0x11, 0x22, 0x33]);
const B1_CONTENT = Buffer.from([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x37, 0x0a]);
const B2_CONTENT = Buffer.from([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]);

const FILE_MAP = {
  "wxfile://tmp/a-标书.docx": A_CONTENT,
  "wxfile://tmp/b-对比文件1.pdf": B1_CONTENT,
  "wxfile://tmp/b-对比文件2.pdf": B2_CONTENT
};

let capturedRequest = null;

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
    capturedRequest = opts;
    opts.success({ data: '{"success":true}', statusCode: 200 });
  }
};

const req = require(path.join(cwd, "utils/request.js"));
const api = require(path.join(cwd, "services/api.js"));

// 解析 multipart 报文
function parseMultipart(buffer, contentType) {
  const m = /boundary=(.+)$/.exec(contentType);
  if (!m) throw new Error("no boundary in content-type");
  const boundary = m[1];
  const body = Buffer.from(buffer);
  const delim = Buffer.from(`--${boundary}`);
  const parts = [];
  let pos = body.indexOf(delim);
  while (pos !== -1) {
    const next = body.indexOf(delim, pos + delim.length);
    if (next === -1) break;
    let seg = body.slice(pos + delim.length, next);
    if (seg[0] === 0x0d && seg[1] === 0x0a) seg = seg.slice(2);
    const headerEnd = seg.indexOf("\r\n\r\n");
    if (headerEnd !== -1) {
      const headerStr = seg.slice(0, headerEnd).toString("utf8");
      const content = seg.slice(headerEnd + 4);
      if (content.length >= 2 && content[content.length - 2] === 0x0d && content[content.length - 1] === 0x0a) {
        parts.push({ header: headerStr, content: content.slice(0, -2) });
      } else {
        parts.push({ header: headerStr, content });
      }
    }
    pos = next;
  }
  return parts;
}

(async () => {
  const res = await api.createTask({
    aFile: { name: "主标书-投标文件.docx", path: "wxfile://tmp/a-标书.docx" },
    bFiles: [
      { name: "对比标书一.pdf", path: "wxfile://tmp/b-对比文件1.pdf" },
      { name: "对比标书二.pdf", path: "wxfile://tmp/b-对比文件2.pdf" }
    ],
    keywords: "工期,履约保证金"
  });

  console.log("API 返回:", JSON.stringify(res));
  if (!capturedRequest) throw new Error("wx.request 未被调用");
  if (!(capturedRequest.data instanceof ArrayBuffer)) throw new Error("请求体不是 ArrayBuffer");
  console.log("method =", capturedRequest.method);
  console.log("Content-Type =", capturedRequest.header["Content-Type"]);
  console.log("body bytes =", capturedRequest.data.byteLength);

  const parts = parseMultipart(capturedRequest.data, capturedRequest.header["Content-Type"]);
  console.log("parts =", parts.length);
  for (const p of parts) {
    console.log("---");
    console.log("header:", p.header.replace(/\r\n/g, " | "));
    console.log("content:", p.content.length, "bytes");
  }

  // 断言
  const byDisposition = (name) => parts.filter((p) => p.header.includes(`name="${name}"`));
  const kw = parts.filter((p) => p.header.includes('name="keywords"'));
  const a = byDisposition("a_file");
  const b = byDisposition("b_files");

  const assert = (cond, msg) => { if (!cond) { console.error("ASSERT FAIL:", msg); process.exit(1); } console.log("PASS:", msg); };

  assert(kw.length === 1 && kw[0].content.toString("utf8") === "工期,履约保证金", "keywords 字段 UTF-8 正确");
  assert(a.length === 1, "a_file 恰好 1 个");
  assert(a[0].header.includes('filename="主标书-投标文件.docx"'), "A 文件中文文件名正确");
  assert(a[0].header.includes("wordprocessingml.document"), "A 文件 MIME 正确");
  assert(a[0].content.equals(A_CONTENT), "A 文件内容字节一致");
  assert(b.length === 2, "b_files 恰好 2 个");
  assert(b[0].header.includes('filename="对比标书一.pdf"'), "B1 中文文件名正确");
  assert(b[0].header.includes("application/pdf"), "B MIME 正确");
  assert(b[0].content.equals(B1_CONTENT) && b[1].content.equals(B2_CONTENT), "B 文件内容字节一致");
  console.log("\nALL MULTIPART ASSERTIONS PASSED");
})();
