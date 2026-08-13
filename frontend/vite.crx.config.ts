import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { crx } from "@crxjs/vite-plugin";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const buildMeta = JSON.parse(readFileSync(resolve(__dirname, ".build-meta.json"), "utf8"));
const [major, minor] = buildMeta.baseVersion.split(".");
const displayVersion = `${major}.${minor}.${buildMeta.buildNumber}`;

// 动态覆盖 manifest 版本号，保持与 web 版本一致
const rawManifest = JSON.parse(readFileSync(resolve(__dirname, "./manifest.json"), "utf8"));
rawManifest.version = displayVersion;

export default defineConfig({
  base: "./",
  plugins: [
    vue(),
    AutoImport({
      imports: ["vue", "vue-router"],
      resolvers: [ElementPlusResolver()]
    }),
    Components({
      resolvers: [ElementPlusResolver()]
    }),
    crx({ manifest: rawManifest }),
    {
      name: "strip-web-analytics-for-crx",
      transformIndexHtml(html) {
        return html.replace(
          /<script>\s*var _hmt = _hmt \|\| \[\];[\s\S]*?<\/script>/,
          ""
        );
      }
    },
    {
      name: "sanitize-mv3-unsafe-eval-patterns",
      generateBundle(_, bundle) {
        for (const item of Object.values(bundle)) {
          if (item.type !== "chunk") {
            continue;
          }
          item.code = item.code
            .replace(/Function\("return this"\)\(\)/g, "globalThis")
            .replace(/Function\('return this'\)\(\)/g, "globalThis");
        }
      }
    }
  ],
  build: {
    outDir: "dist-crx",
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL("./index.html", import.meta.url))
      },
      output: {
        manualChunks: {
          vue: ["vue", "vue-router"],
          element: ["element-plus", "@element-plus/icons-vue"],
          charts: ["echarts"]
        }
      }
    }
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "lodash": "lodash-es"
    }
  },
  define: {
    "import.meta.env.VITE_CRX": JSON.stringify("true"),
    "import.meta.env.VITE_API_BASE_URL": JSON.stringify("https://biaoshu.mxitx.com")
  }
});
