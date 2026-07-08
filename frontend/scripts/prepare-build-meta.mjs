import crypto from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = fileURLToPath(new URL("../", import.meta.url));
const packageJsonPath = path.join(projectRoot, "package.json");
const metaPath = path.join(projectRoot, ".build-meta.json");
const generatedDir = path.join(projectRoot, "src", "generated");
const generatedFilePath = path.join(generatedDir, "buildMeta.ts");

const trackedEntries = [
  "index.html",
  "manifest.json",
  "package.json",
  "vite.config.ts",
  "vite.crx.config.ts",
  "src",
  "public"
];

const ignoredDirectories = new Set([
  "node_modules",
  "dist",
  "dist-crx",
  ".vite-ssg-temp"
]);

const ignoredFiles = new Set([
  ".build-meta.json",
  path.join("src", "generated", "buildMeta.ts").replaceAll("\\", "/")
]);

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function collectFiles(entryPath, relativePath, files) {
  const stat = await fs.stat(entryPath);
  if (stat.isDirectory()) {
    const baseName = path.basename(entryPath);
    if (ignoredDirectories.has(baseName)) {
      return;
    }

    const children = await fs.readdir(entryPath);
    for (const child of children.sort()) {
      const nextPath = path.join(entryPath, child);
      const nextRelative = path.join(relativePath, child);
      await collectFiles(nextPath, nextRelative, files);
    }
    return;
  }

  const normalizedRelative = relativePath.replaceAll("\\", "/");
  if (ignoredFiles.has(normalizedRelative)) {
    return;
  }
  files.push({ absolute: entryPath, relative: normalizedRelative });
}

async function computeSourceHash() {
  const files = [];

  for (const entry of trackedEntries) {
    const absoluteEntry = path.join(projectRoot, entry);
    if (await pathExists(absoluteEntry)) {
      await collectFiles(absoluteEntry, entry, files);
    }
  }

  files.sort((left, right) => left.relative.localeCompare(right.relative));

  const hash = crypto.createHash("sha256");
  for (const file of files) {
    hash.update(file.relative);
    hash.update("\n");
    hash.update(await fs.readFile(file.absolute));
    hash.update("\n");
  }

  return hash.digest("hex");
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
  const previousMeta = await readJson(metaPath, {
    baseVersion: packageJson.version,
    buildNumber: 0,
    sourceHash: ""
  });

  const sourceHash = await computeSourceHash();
  const sourceChanged =
    previousMeta.baseVersion !== packageJson.version ||
    previousMeta.sourceHash !== sourceHash;

  const buildNumber = sourceChanged
    ? Number(previousMeta.buildNumber || 0) + 1
    : Number(previousMeta.buildNumber || 0);

  const meta = {
    baseVersion: packageJson.version,
    buildNumber,
    sourceHash,
    updatedAt: new Date().toISOString()
  };

  const [major, minor, patch] = packageJson.version.split(".");
  const displayVersion = `${major}.${minor}.${patch}+build.${buildNumber}`;

  await fs.mkdir(generatedDir, { recursive: true });
  await fs.writeFile(
    metaPath,
    `${JSON.stringify(meta, null, 2)}\n`,
    "utf8"
  );
  await fs.writeFile(
    generatedFilePath,
    [
      "export const BUILD_META = {",
      `  baseVersion: ${JSON.stringify(packageJson.version)},`,
      `  buildNumber: ${buildNumber},`,
      `  displayVersion: ${JSON.stringify(displayVersion)},`,
      `  updatedAt: ${JSON.stringify(meta.updatedAt)}`,
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
