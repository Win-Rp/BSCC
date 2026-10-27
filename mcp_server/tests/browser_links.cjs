const { chromium } = require(process.env.BSCC_TEST_PLAYWRIGHT);

async function main() {
  const [resultUrl, compareUrl, taskNo] = process.argv.slice(2);
  const browser = await chromium.launch({
    executablePath: process.env.BSCC_TEST_BROWSER,
    headless: true,
  });
  try {
    const page = await browser.newPage();
    await page.goto(resultUrl, { waitUntil: "domcontentloaded" });
    await page.locator(".task-id-tag").waitFor({ timeout: 30000 });
    const taskText = await page.locator(".task-id-tag").innerText();
    if (!taskText.includes(taskNo)) throw new Error("结果页没有显示 MCP 返回的任务号");

    await page.goto(compareUrl, { waitUntil: "domcontentloaded" });
    await page.locator(".txt-host").first().waitFor({ timeout: 30000 });
    await page.waitForFunction(() => document.querySelectorAll(".txt-host").length === 2);
    await page.locator(".txt-host mark.doc-hit").first().waitFor({ timeout: 30000 });
    const original = await page.locator(".txt-host").first().innerText();
    if (!original.includes("标书查重网页链接验证")) throw new Error("对比页没有显示 TXT 原文");
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
