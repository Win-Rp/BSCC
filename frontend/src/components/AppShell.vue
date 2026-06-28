<template>
  <div class="page-shell">
    <div v-if="systemNotice" class="shell-notice-float">
      <span class="shell-notice-float__label">系统公告</span>
      <span class="shell-notice-float__text">{{ systemNotice }}</span>
    </div>

    <nav class="shell-topbar">
      <div class="shell-topbar__logo" @click="router.push('/')" style="cursor: pointer;">
        <span class="shell-topbar__brand">{{ siteTitle || '标书查重系统' }}</span>
        <div class="feature-tags">
          <el-tag v-for="tag in homeTags" :key="tag" type="success" effect="light" round>
            {{ tag }}
          </el-tag>
        </div>
      </div>
      <div class="shell-topbar__menu">
        <router-link to="/" class="shell-topbar__link" active-class="is-active">主页</router-link>
        <router-link to="/docs" class="shell-topbar__link" active-class="is-active">文档</router-link>
      </div>
    </nav>

    <StepperNav
      v-if="showStepper"
      :steps="navSteps" 
      :active-value="currentRouteName" 
      @change="handleNavChange" 
    />

    <main class="shell-main">
      <slot />
    </main>

    <div class="floating-contact">
      <el-popover
        placement="left"
        trigger="hover"
        :width="260"
        popper-class="floating-contact-popover"
      >
        <template #reference>
          <div class="floating-btn floating-btn--wechat">
            <svg viewBox="0 0 1024 1024" width="24" height="24"><path d="M682.666667 341.333333c-115.2 0-213.333333 76.8-213.333334 170.666667 0 93.866667 98.133333 170.666667 213.333334 170.666667 21.333333 0 42.666667-4.266667 64-8.533334l64 34.133334-17.066667-42.666667c42.666667-34.133333 72.533333-81.066667 72.533333-132.266667-4.266667-106.666667-102.4-192-183.466666-192zM631.466667 448c-12.8 0-25.6-8.533333-25.6-21.333333s12.8-21.333333 25.6-21.333334c17.066667 0 25.6 8.533333 25.6 21.333334s-8.533333 21.333333-25.6 21.333333z m110.933333 0c-12.8 0-25.6-8.533333-25.6-21.333333s12.8-21.333333 25.6-21.333334c17.066667 0 25.6 8.533333 25.6 21.333334s-8.533333 21.333333-25.6 21.333333z" fill="currentColor"/><path d="M362.666667 618.666667c12.8 0 29.866667 0 42.666666-4.266667-8.533333-29.866667-12.8-59.733333-12.8-89.6 0-140.8 136.533333-256 302.933334-256 12.8 0 21.333333 0 34.133333 4.266667C691.2 166.4 546.133333 85.333333 384 85.333333 192 85.333333 34.133333 213.333333 34.133333 371.2c0 93.866667 51.2 174.933333 132.266667 226.133333l-25.6 76.8 98.133333-51.2c42.666667 8.533333 81.066667 12.8 123.733334 12.8z m-98.133334-315.733334c21.333333 0 34.133333 12.8 34.133334 34.133334s-12.8 34.133333-34.133334 34.133333-34.133333-12.8-34.133333-34.133333 17.066667-34.133333 34.133333-34.133334z m204.8 0c21.333333 0 34.133333 12.8 34.133333 34.133334s-12.8 34.133333-34.133333 34.133333c-21.333333 0-34.133333-12.8-34.133333-34.133333s12.8-34.133333 34.133333-34.133334z" fill="currentColor"/></svg>
          </div>
        </template>
        <img
          v-if="supportWechatQrVisible"
          class="floating-raw-qr"
          :src="supportWechatQrSrc"
          alt="客服微信二维码"
          @error="supportWechatQrVisible = false"
        />
        <div v-else class="floating-popover-content">
          <span class="floating-popover__fallback" style="text-align: center; display: block;">图片未就绪</span>
        </div>
      </el-popover>

      <el-popover
        v-if="supportEmail"
        placement="left"
        trigger="hover"
        :width="260"
        popper-class="floating-contact-popover"
      >
        <template #reference>
          <div class="floating-btn floating-btn--email">
            <svg viewBox="0 0 1024 1024" width="24" height="24"><path d="M853.333333 213.333333H170.666667c-46.933333 0-85.333333 38.4-85.333334 85.333334v426.666666c0 46.933333 38.4 85.333333 85.333334 85.333334h682.666666c46.933333 0 85.333333-38.4 85.333334-85.333334V298.666667c0-46.933333-38.4-85.333333-85.333334-85.333334zM499.2 584.533333c-8.533333 8.533333-21.333333 8.533333-25.6 0l-337.066667-311.466666h695.466667L499.2 584.533333z m354.133333 140.8H170.666667V332.8l294.4 273.066667c12.8 12.8 34.133333 17.066667 51.2 17.066666 17.066667 0 34.133333-4.266667 46.933333-17.066666l294.4-273.066667v392.533333z" fill="currentColor"/></svg>
          </div>
        </template>
        <div class="floating-popover-content">
          <span class="floating-popover__eyebrow">客服邮箱</span>
          <strong class="floating-popover__email">{{ supportEmail }}</strong>
          <span class="floating-popover__desc">适合发送问题截图、需求说明与联调信息</span>
        </div>
      </el-popover>
    </div>

    <div class="shell-copyright">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">陕ICP备2026010691号</a>
      <span class="shell-copyright__divider">|</span>
      <a href="https://www.beian.gov.cn/portal/registerSystemInfo?recordcode=61011302002444" target="_blank" rel="noopener noreferrer">公安备案 陕公网安备61011302002444号</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import StepperNav from "./StepperNav.vue";
import { Loading } from "@element-plus/icons-vue";
import { isTaskProcessing } from "@/composables/useTaskState";
import { getPublicSiteConfig, getSupport } from "@/services/api";

const router = useRouter();
const route = useRoute();

const siteTitle = ref("标书查重系统");
const homeTags = ref(['无需登陆', '基础免费', '不限页数', '不限大小', '开箱即用']);
const systemNotice = ref("");
const supportWechat = ref("");
const supportEmail = ref("");
const supportWechatQrSrc = "/support-wechat-qr.png";
const supportWechatQrVisible = ref(true);

onMounted(async () => {
  try {
    const [siteConfig, supportInfo] = await Promise.all([
      getPublicSiteConfig(),
      getSupport()
    ]);

    if (siteConfig?.site_title) {
      siteTitle.value = siteConfig.site_title;
    }
    if (siteConfig?.home_tags?.length > 0) {
      homeTags.value = siteConfig.home_tags;
    }
    systemNotice.value = siteConfig?.system_notice?.trim() ?? "";
    supportWechat.value = supportInfo?.wechat?.trim() ?? "";
    supportEmail.value = supportInfo?.email?.trim() ?? "";
  } catch {
    // 公开配置接口异常时，回退为默认标签。
  }
});

watch(
  siteTitle,
  (value) => {
    document.title = value?.trim() || "标书查重系统";
  },
  { immediate: true }
);

const hasSupportInfo = computed(() => Boolean(supportWechat.value || supportEmail.value));

const currentRouteName = computed(() => {
  if (isTaskProcessing.value && route.name === 'results') {
    return 'processing';
  }
  return route.name as string;
});
const showStepper = computed(() => route.name !== "docs");

const navSteps = computed(() => {
  const steps: Array<{ label: string; value: string; subLabel: string; icon?: any }> = [
    { label: "上传工作台", value: "upload", subLabel: "提交标书文件" }
  ];

  if (isTaskProcessing.value && route.name === 'results') {
    steps.push({ label: "AI 查重中", value: "processing", subLabel: "智能比对中", icon: Loading });
  }

  steps.push(
    { label: "结果总览", value: "results", subLabel: "查看查重排行" },
    { label: "对比证据", value: "compare", subLabel: "原文差异对比" }
  );

  return steps;
});

const handleNavChange = (value: string) => {
  if (value === 'processing') return;
  router.push({ name: value });
};
</script>
