import { createRouter, createWebHistory } from "vue-router";
import UploadView from "@/views/UploadView.vue";
import ResultsView from "@/views/ResultsView.vue";
import CompareView from "@/views/CompareView.vue";
import DocsView from "@/views/DocsView.vue";
import AdminLoginView from "@/views/AdminLoginView.vue";
import AdminDashboardView from "@/views/AdminDashboardView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", redirect: "/upload" },
    { path: "/upload", name: "upload", component: UploadView, meta: { requiresShell: true } },
    { path: "/docs", name: "docs", component: DocsView, meta: { requiresShell: true } },
    { path: "/results", name: "results", component: ResultsView, meta: { requiresShell: true } },
    { path: "/compare", name: "compare", component: CompareView, meta: { requiresShell: true } },
    { path: "/admin/login", name: "admin-login", component: AdminLoginView, meta: { requiresShell: false } },
    { path: "/admin", name: "admin-dashboard", component: AdminDashboardView, meta: { requiresShell: false } },
  ],
  scrollBehavior() {
    return { top: 0 };
  }
});

export default router;
