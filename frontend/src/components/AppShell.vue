<template>
  <div class="page-shell">
    <header class="shell-hero" @click="router.push('/')" style="cursor: pointer;">
      <div class="shell-hero__main">
        <span class="shell-kicker">智能标书对比</span>
        <h1>标书查重系统</h1>
        <div class="feature-tags">
          <el-tag type="success" effect="light" round>无需登陆</el-tag>
          <el-tag type="success" effect="light" round>基础免费</el-tag>
          <el-tag type="success" effect="light" round>不限页数</el-tag>
          <el-tag type="success" effect="light" round>不限大小</el-tag>
          <el-tag type="success" effect="light" round>开箱即用</el-tag>
        </div>
      </div>
    </header>

    <main class="shell-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
const router = useRouter();
</script>
