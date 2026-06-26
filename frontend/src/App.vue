<template>
  <el-config-provider namespace="el">
    <AppShell>
      <router-view />
    </AppShell>
  </el-config-provider>
</template>

<script setup lang="ts">
import AppShell from "@/components/AppShell.vue";
</script>
