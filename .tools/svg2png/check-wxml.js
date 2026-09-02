const fs = require("fs");
const path = require("path");

const files = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith(".wxml")) files.push(p);
  }
})(".");

const voidTags = new Set(["image", "input", "import", "include"]);
let allOk = true;

for (const f of files) {
  const src = fs.readFileSync(f, "utf8").replace(/<!--[\s\S]*?-->/g, "");
  const stack = [];
  const re = /<\/?([a-zA-Z][\w-]*)(?:"[^"]*"|'[^']*'|[^"'>])*>/g;
  let m, ok = true;
  while ((m = re.exec(src))) {
    const full = m[0];
    const tag = m[1];
    const selfClose = /\/\s*>$/.test(full);
    const isClose = /^<\//.test(full);
    if (isClose) {
      const top = stack.pop();
      if (top !== tag) {
        ok = false;
        console.log("MISMATCH in", f, "expect </" + top + "> got </" + tag + ">");
        break;
      }
    } else if (!selfClose && !voidTags.has(tag)) {
      stack.push(tag);
    }
  }
  if (stack.length) {
    ok = false;
    console.log("UNCLOSED in", f, ":", stack.join(","));
  }
  if (ok) console.log("OK", f);
  else allOk = false;
}
console.log(allOk ? "ALL WXML BALANCED" : "WXML ISSUES FOUND");
