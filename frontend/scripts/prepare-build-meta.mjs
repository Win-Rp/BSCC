import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = fileURLToPath(new URL("../", import.meta.url));
const packageJsonPath = path.join(projectRoot, "package.json");
const generatedDir = path.join(projectRoot, "src", "generated");
const generatedFilePath = path.join(generatedDir, "buildMeta.ts");

// Docker 构建是一次性环境，自增 buildNumber 的状态文件无法写回仓库，
// 导致每次部署都从同一基数 +1（版本号永远不变）。
// 因此 patch 段改为构建日期 + 时间（东八区），任何环境每次构建必然变化且单调递增。
function shanghaiParts(date) {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23"
  });
  const parts = {};
  for (const part of formatter.formatToParts(date)) {
    parts[part.type] = part.value;
  }
  return parts;
}

async function readJson(filePath, fallbackValue) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch {
    return fallbackValue;
  }
}

async function main() {
  const packageJson = await readJson(packageJsonPath, { version: "0.1.0" });
  const now = new Date();
  const parts = shanghaiParts(now);
  const dateStamp = `${parts.year.slice(2)}${parts.month}${parts.day}`;
  const timeStamp = `${parts.hour}${parts.minute}`;

  const [major, minor] = packageJson.version.split(".");
  const buildStamp = `${dateStamp}-${timeStamp}`;
  const displayVersion = `${major}.${minor}.${buildStamp}`;
  const updatedAt = now.toISOString();

  await fs.mkdir(generatedDir, { recursive: true });
  await fs.writeFile(
    generatedFilePath,
    [
      "export const BUILD_META = {",
      `  baseVersion: ${JSON.stringify(packageJson.version)},`,
      `  buildStamp: ${JSON.stringify(buildStamp)},`,
      `  displayVersion: ${JSON.stringify(displayVersion)},`,
      `  updatedAt: ${JSON.stringify(updatedAt)}`,
      "} as const;",
      ""
    ].join("\n"),
    "utf8"
  );
}

main().catch((error) => {
  console.error("[prepare-build-meta] failed", error);
  process.exitCode = 1;
});
