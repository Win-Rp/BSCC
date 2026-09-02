const path = require("path");
const envCfg = require(path.join("d:/Office/Rp/Dev/BSCC/miniprogram/config/env.js"));
const https = require(envCfg.baseURL.startsWith("https") ? "https" : "http");
const cwd = "d:/Office/Rp/Dev/BSCC/miniprogram";

global.wx = {
  request(options) {
    const url = new URL(options.url);
    const req = https.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname + url.search,
        method: options.method || "GET",
        headers: Object.assign({ "Content-Type": "application/json" }, options.header || {}),
        timeout: options.timeout || 15000
      },
      (res) => {
        let raw = "";
        res.on("data", (chunk) => (raw += chunk));
        res.on("end", () => options.success({ data: raw, statusCode: res.statusCode }));
      }
    );
    req.on("error", (err) => options.fail({ errMsg: err.message }));
    req.on("timeout", () => { req.destroy(); options.fail({ errMsg: "timeout" }); });
    if (options.data) req.write(typeof options.data === "string" ? options.data : JSON.stringify(options.data));
    req.end();
  }
};

const api = require(path.join(cwd, "services/api.js"));
const env = require(path.join(cwd, "config/env.js"));

console.log("baseURL =", env.baseURL);

(async () => {
  const site = await api.getSiteConfig();
  console.log("[site-config] success =", site.success, "| site_title =", site.data && site.data.site_title, "| tags =", site.data && site.data.home_tags.length, "| promo_active =", site.data && site.data.promo.promo_active);

  const support = await api.getSupport();
  console.log("[support] success =", support.success, "| email =", support.data && support.data.email);

  const status = await api.getTaskStatus("INVALID123");
  console.log("[task-status 404] success =", status.success, "| code =", status.error && status.error.code, "| message =", status.error && status.error.message);

  const recover = await api.recoverTask({});
  console.log("[recover 400] success =", recover.success, "| code =", recover.error && recover.error.code);

  const aUrl = api.getAFileURL("TASK123");
  console.log("[file-url]", aUrl);
  console.log("ALL END-TO-END CHECKS DONE");
  process.exit(0);
})();
