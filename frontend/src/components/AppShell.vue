<template>
  <div class="page-shell">
    <header class="shell-hero" @click="router.push('/')" style="cursor: pointer;">
      <div class="shell-hero__main">
        <span class="shell-kicker">智能标书对比</span>
        <h1>标书查重系统</h1>
        <div class="feature-tags">
          <el-tag v-for="tag in homeTags" :key="tag" type="success" effect="light" round>
            {{ tag }}
          </el-tag>
        </div>
      </div>
    </header>

    <StepperNav 
      :steps="navSteps" 
      :active-value="currentRouteName" 
      @change="handleNavChange" 
    />

    <main class="shell-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import StepperNav from "./StepperNav.vue";
import { 
  Upload, 
  DataAnalysis, 
  DocumentCopy,
  Loading
} from "@element-plus/icons-vue";
import { isTaskProcessing } from "@/composables/useTaskState";
import { getSystemSettings } from "@/services/api";

const router = useRouter();
const route = useRoute();

const homeTags = ref(['无需登陆', '基础免费', '不限页数', '不限大小', '开箱即用']);

onMounted(async () => {
  try {
    // 尝试获取后台配置以动态渲染首页标签
    const settings = await getSystemSettings();
    if (settings && settings.home_tags && settings.home_tags.length > 0) {
      homeTags.value = settings.home_tags;
    }
  } catch (error) {
    // 忽略错误，如果后端接口未准备好则使用默认写死的标签
  }
});

const currentRouteName = computed(() => {
  if (isTaskProcessing.value && route.name === 'results') {
    return 'processing';
  }
  return route.name as string;
});

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
