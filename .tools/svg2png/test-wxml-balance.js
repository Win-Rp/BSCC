const fs = require("fs");
const path = require("path");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

console.log("=== upload WXML 残留引用检查 ===");
const uploadWxml = fs.readFileSync(path.join(cwd, "pages/upload/index.wxml"), "utf8");
const stale = uploadWxml.split("\n").filter((line) => /countdown|promo|priceText|预计/.test(line));
if (stale.length) {
  stale.forEach((line) => console.log("RESIDUE:", line.trim()));
  process.exitCode = 1;
} else {
  console.log("干净：无促销/价格残留");
}

console.log("\n=== WXML 标签平衡 ===");
const re = /<([a-zA-Z][\w-]*)((?:\s+[\w-:]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/)?>|<\/([a-zA-Z][\w-]*)\s*>/g;

for (const rel of ["pages/upload/index.wxml", "components/unlock-bar/index.wxml", "pages/results/index.wxml", "pages/progress/index.wxml", "pages/order/index.wxml", "pages/compare/index.wxml", "pages/docs/index.wxml", "pages/recovery/index.wxml", "components/nav-bar/index.wxml", "components/result-card/index.wxml"]) {
  const src = fs.readFileSync(path.join(cwd, rel), "utf8").replace(/<!--[\s\S]*?-->/g, "");
  const stack = [];
  let m;
  let ok = true;
  re.lastIndex = 0;
  while ((m = re.exec(src))) {
    if (m[4]) {
      const top = stack.pop();
      if (top !== m[4]) {
        console.log("MISMATCH", rel, "expect </" + top + "> got </" + m[4] + ">");
        ok = false;
        break;
      }
    } else if (!m[3]) {
      stack.push(m[1]);
    }
  }
  if (ok && stack.length === 0) {
    console.log("BALANCED", rel);
  } else if (ok) {
    console.log("UNCLOSED", rel, stack.join(","));
    process.exitCode = 1;
  } else {
    process.exitCode = 1;
  }
}
