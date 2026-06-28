import type { RouteRecordRaw } from "vue-router";
import { seoPages } from "@/content/seoPages";

const SeoPageView = () => import("@/views/SeoPageView.vue");
const UploadView = () => import("@/views/UploadView.vue");
const ResultsView = () => import("@/views/ResultsView.vue");
const CompareView = () => import("@/views/CompareView.vue");
const DocsView = () => import("@/views/DocsView.vue");
const AdminLoginView = () => import("@/views/AdminLoginView.vue");
const AdminDashboardView = () => import("@/views/AdminDashboardView.vue");

export const routes: RouteRecordRaw[] = [
    { path: "/", name: "home", component: SeoPageView, meta: { requiresShell: true, seo: seoPages.home.seo } },
    {
      path: "/upload",
      name: "upload",
      component: UploadView,
      meta: {
        requiresShell: true,
        seo: {
          title: "标书查重工具入口_上传投标文件开始检查_{siteTitle}",
          description:
            "上传主标书 A 与对比标书 B，开始标书查重、标书检查和围标风险排查，支持 DOCX 与可复制文本 PDF。",
          keywords: ["标书查重入口", "投标文件查重", "标书检查工具", "围标风险排查"]
        }
      }
    },
    {
      path: "/free",
      name: "free-landing",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["free-landing"].seo }
    },
    {
      path: "/check",
      name: "check-landing",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["check-landing"].seo }
    },
    {
      path: "/compliance",
      name: "compliance-landing",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["compliance-landing"].seo }
    },
    {
      path: "/solutions/engineering",
      name: "engineering-solution",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["engineering-solution"].seo }
    },
    {
      path: "/solutions/business-team",
      name: "business-solution",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["business-solution"].seo }
    },
    {
      path: "/guides/biaoshu-chachong",
      name: "guide-biaoshu-chachong",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["guide-biaoshu-chachong"].seo }
    },
    {
      path: "/guides/biaoshu-check",
      name: "guide-biaoshu-check",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["guide-biaoshu-check"].seo }
    },
    {
      path: "/guides/similarity-risk",
      name: "guide-similarity-risk",
      component: SeoPageView,
      meta: { requiresShell: true, seo: seoPages["guide-similarity-risk"].seo }
    },
    {
      path: "/docs",
      name: "docs",
      component: DocsView,
      meta: {
        requiresShell: true,
        seo: {
          title: "标书查重使用说明_结果解读与对比证据查看_{siteTitle}",
          description:
            "查看标书查重使用说明，了解如何上传投标文件、阅读结果总览、使用对比证据页面和找回历史任务结果。",
          keywords: ["标书查重使用说明", "标书结果怎么看", "投标文件对比说明"],
          jsonLd: {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            mainEntity: [
              {
                "@type": "Question",
                name: "为什么我只能看到预览，看不到完整详情？",
                acceptedAnswer: {
                  "@type": "Answer",
                  text: "当任务上传了 2-10 份 B 文件时，系统会先展示免费预览，解锁后可查看完整详情。"
                }
              },
              {
                "@type": "Question",
                name: "任务处理中可以关闭页面吗？",
                acceptedAnswer: {
                  "@type": "Answer",
                  text: "可以，建议先保存任务号，随后可凭任务号找回结果。"
                }
              }
            ]
          }
        }
      }
    },
    {
      path: "/results",
      name: "results",
      component: ResultsView,
      meta: {
        requiresShell: true,
        seo: {
          title: "标书查重结果页_{siteTitle}",
          description: "当前任务的标书查重结果页，仅用于查看任务相似度排行、摘要和复核详情。",
          robots: "noindex,nofollow"
        }
      }
    },
    {
      path: "/compare",
      name: "compare",
      component: CompareView,
      meta: {
        requiresShell: true,
        seo: {
          title: "标书原文对比页_{siteTitle}",
          description: "当前任务的原文对比页面，仅用于查看命中片段证据与文档上下文。",
          robots: "noindex,nofollow"
        }
      }
    },
    {
      path: "/admin/login",
      name: "admin-login",
      component: AdminLoginView,
      meta: {
        requiresShell: false,
        seo: {
          title: "运营后台登录_{siteTitle}",
          description: "网站运营后台登录入口。",
          robots: "noindex,nofollow"
        }
      }
    },
    {
      path: "/admin",
      name: "admin-dashboard",
      component: AdminDashboardView,
      meta: {
        requiresShell: false,
        seo: {
          title: "运营后台_{siteTitle}",
          description: "网站运营后台工作台。",
          robots: "noindex,nofollow"
        }
      }
    },
];

export const nonPrerenderRoutes = ["/results", "/compare", "/admin", "/admin/login"];
