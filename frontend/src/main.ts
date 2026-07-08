import ElementPlus from "element-plus";
import { ID_INJECTION_KEY, ZINDEX_INJECTION_KEY } from "element-plus";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import { createHead } from "@unhead/vue/client";
import { ViteSSG } from "vite-ssg";
import { createApp as createClientApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import { nonPrerenderRoutes, routes } from "./router";
import "./styles/main.css";
import * as echarts from "echarts";
import VChart from "vue-echarts";

const isCrx = import.meta.env.VITE_CRX === "true";

function setupApp(app: any) {
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
  }
  if (!isCrx) {
    app.use(ElementPlus);
  }
  app.provide(ID_INJECTION_KEY, {
    prefix: 1024,
    current: 0
  });
  app.provide(ZINDEX_INJECTION_KEY, {
    current: 0
  });
  app.provide("echarts", echarts);
  app.component("v-chart", VChart);
}

export const createApp = !isCrx
  ? ViteSSG(
      App,
      {
        base: import.meta.env.BASE_URL,
        routes,
        scrollBehavior() {
          return { top: 0 };
        }
      },
      ({ app }) => {
        setupApp(app);
      }
    )
  : (() => {
      // Return a dummy create app for ViteSSG export when in CRX mode,
      // but we actually mount manually below.
      return {} as any;
    })();

// In CRX mode, we mount the app manually since we bypass ViteSSG.
if (isCrx) {
  const app = createClientApp(App);
  const router = createRouter({
    history: createWebHashHistory(),
    routes,
    scrollBehavior() {
      return { top: 0 };
    }
  });
  app.use(createHead());
  app.use(router);
  setupApp(app);
  // Important: Mount when DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    app.mount("#app");
  });
}

export function includedRoutes(paths: string[]) {
  return paths.filter((path) => !nonPrerenderRoutes.includes(path));
}
