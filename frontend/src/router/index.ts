import { createRouter, createWebHistory } from "vue-router";
import UploadView from "@/views/UploadView.vue";
import ResultsView from "@/views/ResultsView.vue";
import CompareView from "@/views/CompareView.vue";
import RecoverView from "@/views/RecoverView.vue";
import AdminView from "@/views/AdminView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", redirect: "/upload" },
    { path: "/upload", name: "upload", component: UploadView },
    { path: "/results", name: "results", component: ResultsView },
    { path: "/compare", name: "compare", component: CompareView },
    { path: "/recover", name: "recover", component: RecoverView },
    { path: "/admin", name: "admin", component: AdminView }
  ],
  scrollBehavior() {
    return { top: 0 };
  }
});

export default router;
