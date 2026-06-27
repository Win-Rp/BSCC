<template>
  <el-config-provider namespace="el">
    <template v-if="route.meta.requiresShell !== false">
      <AppShell>
        <router-view />
      </AppShell>
    </template>
    <template v-else>
      <router-view />
    </template>
  </el-config-provider>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import AppShell from "@/components/AppShell.vue";

const route = useRoute();
</script>
