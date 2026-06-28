import ElementPlus from "element-plus";
import { ID_INJECTION_KEY, ZINDEX_INJECTION_KEY } from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import { ViteSSG } from "vite-ssg";
import App from "./App.vue";
import { nonPrerenderRoutes, routes } from "./router";
import "./styles/main.css";
import * as echarts from "echarts";
import VChart from "vue-echarts";

export const createApp = ViteSSG(
  App,
  {
    base: import.meta.env.BASE_URL,
    routes,
    scrollBehavior() {
      return { top: 0 };
    }
  },
  ({ app }) => {
    for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
      app.component(key, component);
    }

    app.use(ElementPlus, { locale: zhCn });
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
);

export function includedRoutes(paths: string[]) {
  return paths.filter((path) => !nonPrerenderRoutes.includes(path));
}
