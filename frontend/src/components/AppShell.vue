<template>
  <div class="page-shell">
    <div v-if="showNotice" class="shell-notice-float">
      <div class="shell-notice-float__bar">
        <button
          type="button"
          class="shell-notice-float__trigger"
          :title="translateText('点击查看完整公告')"
          @click="noticeExpanded = !noticeExpanded"
        >
          <span class="shell-notice-float__label">{{ t("shell.systemNotice") }}</span>
          <span class="shell-notice-float__text">{{ systemNotice }}</span>
          <el-icon class="shell-notice-float__arrow" :class="{ 'is-open': noticeExpanded }"><ArrowDown /></el-icon>
        </button>
        <button
          type="button"
          class="shell-notice-float__close"
          :title="translateText('关闭公告')"
          @click="noticeDismissed = true"
        >
          <el-icon><Close /></el-icon>
        </button>
      </div>
      <div v-if="noticeExpanded" class="shell-notice-float__panel">{{ systemNotice }}</div>
    </div>

    <nav class="shell-topbar">
      <div class="shell-topbar__logo" @click="router.push('/')" style="cursor: pointer;">
        <span class="shell-topbar__brand">{{ localizedSiteTitle }}</span>
        <div class="feature-tags">
          <el-tag v-for="tag in localizedHomeTags" :key="tag" type="success" effect="light" round>
            {{ tag }}
          </el-tag>
        </div>
      </div>
      <div class="shell-topbar__menu">
        <router-link
          v-for="item in menuItems"
          :key="item.to"
          :to="item.to"
          class="shell-topbar__link"
          :class="{ 'is-active': route.path === item.to }"
        >
          {{ item.label }}
        </router-link>
      </div>
      <div class="shell-topbar__meta">
        <div class="shell-lang-switcher">
          <span class="shell-lang-switcher__label">{{ t("shell.language") }}</span>
          <el-select
            :model-value="locale"
            size="small"
            class="shell-lang-switcher__select"
            @change="handleLocaleChange"
          >
            <el-option
              v-for="option in localeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
        <span class="shell-build-version">{{ t("shell.version") }} {{ buildVersion }}</span>
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
        v-if="mpQrcodeUrl"
        placement="left"
        trigger="hover"
        :width="240"
        popper-class="floating-contact-popover"
      >
        <template #reference>
          <div class="floating-btn floating-btn--mp">
            <svg viewBox="0 0 1024 1024" width="24" height="24"><path d="M512 128c-211.2 0-384 153.6-384 345.6 0 108.8 57.6 204.8 147.2 268.8l-19.2 89.6c-4.266667 17.066667 12.8 29.866667 29.866667 21.333333l108.8-51.2c38.4 12.8 76.8 17.066667 119.466666 17.066667 211.2 0 384-153.6 384-345.6S723.2 128 512 128z m-128 358.4c-21.333333 0-42.666667-17.066667-42.666667-42.666667s21.333333-42.666667 42.666667-42.666666 42.666667 17.066667 42.666667 42.666666-21.333333 42.666667-42.666667 42.666667z m256 0c-21.333333 0-42.666667-17.066667-42.666667-42.666667s21.333333-42.666667 42.666667-42.666666 42.666667 17.066667 42.666667 42.666666-21.333333 42.666667-42.666667 42.666667z" fill="currentColor"/></svg>
          </div>
        </template>
        <div class="floating-popover-content">
          <span class="floating-popover__text">{{ translateText("关注服务号") }}</span>
          <div class="floating-popover__qr">
            <img
              v-if="mpQrVisible"
              :src="mpQrcodeUrl"
              :alt="translateText('微信服务号二维码')"
              @error="mpQrVisible = false"
            />
            <span v-else class="floating-popover__fallback">{{ translateText("二维码图片加载失败") }}</span>
          </div>
          <span class="floating-popover__desc">{{ translateText("查重完成后通过服务号第一时间通知您") }}</span>
        </div>
      </el-popover>

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
          :alt="t('shell.qrFallback')"
          @error="supportWechatQrVisible = false"
        />
        <div v-else class="floating-popover-content">
          <span class="floating-popover__fallback" style="text-align: center; display: block;">{{ t("shell.qrFallback") }}</span>
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
          <span class="floating-popover__eyebrow">{{ t("shell.email.eyebrow") }}</span>
          <strong class="floating-popover__email">{{ supportEmail }}</strong>
          <span class="floating-popover__desc">{{ t("shell.email.desc") }}</span>
        </div>
      </el-popover>
    </div>

    <div class="shell-copyright">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">陕ICP备2026010691号</a>
      <span class="shell-copyright__divider">|</span>
      <a href="https://www.beian.gov.cn/portal/registerSystemInfo?recordcode=61011302002444" target="_blank" rel="noopener noreferrer">公安备案 陕公网安备61011302002444号</a>
      <span class="shell-copyright__divider">|</span>
      <a href="https://mic.mxitx.com" target="_blank" rel="noopener noreferrer">让你的手机变身电脑麦克风和摄像头</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import StepperNav from "./StepperNav.vue";
import { ArrowDown, Close, Loading } from "@element-plus/icons-vue";
import { isTaskProcessing } from "@/composables/useTaskState";
import { useAppI18n, type AppLocale } from "@/composables/useAppI18n";
import { BUILD_META } from "@/generated/buildMeta";
import { getPublicSiteConfig, getSupport } from "@/services/api";
import { applyRouteSeo, type RouteSeoMeta } from "@/utils/seo";

const router = useRouter();
const route = useRoute();
const { locale, localeOptions, defaultHomeTags, localizeDeep, setLocale, t, translateText } = useAppI18n();

const rawSiteTitle = ref("标书查重系统");
const rawHomeTags = ref<string[]>(["无需登陆", "基础免费", "不限页数", "不限大小", "开箱即用"]);
const rawSystemNotice = ref("");
const supportWechat = ref("");
const supportEmail = ref("");
const supportWechatQrSrc = "/support-wechat-qr.png";
const supportWechatQrVisible = ref(true);
const mpQrcodeUrl = ref("");
const mpQrVisible = ref(true);
const buildVersion = BUILD_META.displayVersion;
const localizedSiteTitle = computed(() => translateText(rawSiteTitle.value || t("app.defaultSiteTitle")));
const localizedHomeTags = computed(() => {
  if (!rawHomeTags.value.length) {
    return defaultHomeTags.value;
  }
  return rawHomeTags.value.map((tag) => translateText(tag));
});
const systemNotice = computed(() => translateText(rawSystemNotice.value));
const noticeExpanded = ref(false);
const noticeDismissed = ref(false);
const showNotice = computed(() => !!systemNotice.value && !noticeDismissed.value);
const menuItems = computed(() => [
  { label: t("shell.menu.home"), to: "/" },
  { label: t("shell.menu.upload"), to: "/upload" },
  { label: t("shell.menu.free"), to: "/free" },
  { label: t("shell.menu.check"), to: "/check" },
  { label: t("shell.menu.compliance"), to: "/compliance" },
  { label: t("shell.menu.docs"), to: "/docs" }
]);

onMounted(async () => {
  try {
    const [siteConfig, supportInfo] = await Promise.all([
      getPublicSiteConfig(),
      getSupport()
    ]);

    if (siteConfig?.site_title) {
      rawSiteTitle.value = siteConfig.site_title;
    }
    if (siteConfig?.home_tags?.length > 0) {
      rawHomeTags.value = localizeDeep(siteConfig.home_tags);
    }
    rawSystemNotice.value = siteConfig?.system_notice?.trim() ?? "";
    mpQrcodeUrl.value = siteConfig?.mp_qrcode_url?.trim() ?? "";
    supportWechat.value = supportInfo?.wechat?.trim() ?? "";
    supportEmail.value = supportInfo?.email?.trim() ?? "";
  } catch {
    // 公开配置接口异常时，回退为默认标签。
    rawSiteTitle.value = "标书查重系统";
    rawHomeTags.value = ["无需登陆", "基础免费", "不限页数", "不限大小", "开箱即用"];
  }
});

watch(
  [localizedSiteTitle, () => route.fullPath, locale],
  () => {
    applyRouteSeo(localizeDeep(route.meta.seo as RouteSeoMeta | undefined), {
      siteTitle: localizedSiteTitle.value,
      currentPath: route.path
    });
  },
  { immediate: true }
);

const currentRouteName = computed(() => {
  if (isTaskProcessing.value && route.name === 'results') {
    return 'processing';
  }
  return route.name as string;
});
const showStepper = computed(() => ["upload", "results", "compare"].includes(String(route.name || "")));

const navSteps = computed(() => {
  const steps: Array<{ label: string; value: string; subLabel: string; icon?: any }> = [
    { label: t("shell.step.upload"), value: "upload", subLabel: t("shell.step.uploadSub") }
  ];

  if (isTaskProcessing.value && route.name === 'results') {
    steps.push({ label: t("shell.step.processing"), value: "processing", subLabel: t("shell.step.processingSub"), icon: Loading });
  }

  steps.push(
    { label: t("shell.step.results"), value: "results", subLabel: t("shell.step.resultsSub") },
    { label: t("shell.step.compare"), value: "compare", subLabel: t("shell.step.compareSub") }
  );

  return steps;
});

const handleNavChange = (value: string) => {
  if (value === 'processing') return;
  router.push({ name: value });
};

function handleLocaleChange(value: AppLocale) {
  setLocale(value);
}
</script>
