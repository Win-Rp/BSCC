const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");

const SRC = "d:/Office/Rp/Dev/BSCC/assets/logo";
const OUT = "d:/Office/Rp/Dev/BSCC/miniprogram/assets/images";

fs.mkdirSync(OUT, { recursive: true });

function render(srcName, outName, width) {
  const svg = fs.readFileSync(path.join(SRC, srcName));
  const resvg = new Resvg(svg, { fitTo: { mode: "width", value: width }, background: "rgba(0,0,0,0)" });
  const png = resvg.render().asPng();
  const out = path.join(OUT, outName);
  fs.writeFileSync(out, png);
  console.log(`OK ${out} (${width}px, ${png.length} bytes)`);
}

render("logo.svg", "logo.png", 600);      // 横向组合标（60px 高基准 x2 缩放 = 600 宽）
render("logo.svg", "logo@2x.png", 1200);   // 高清
render("logo-white.svg", "logo-white.png", 600);   // 反白版（深色背景用）
render("logo-white.svg", "logo-white@2x.png", 1200);
render("logo-icon.svg", "logo-icon.png", 240);  // 方形图标 240
render("logo-icon.svg", "logo-icon@2x.png", 480); // 方形图标高清
