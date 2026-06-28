import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ isSsrBuild }) => ({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: isSsrBuild
        ? undefined
        : {
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
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  }
}));
