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
import { computed, watch } from "vue";
import { useHead } from "@unhead/vue";
import { useRoute } from "vue-router";
import AppShell from "@/components/AppShell.vue";
import { applyRouteSeo, createHeadConfig, resolveRouteSeo, type RouteSeoMeta } from "@/utils/seo";

const route = useRoute();
const routeSeo = computed(() =>
  resolveRouteSeo(route.meta.seo as RouteSeoMeta | undefined, { currentPath: route.path })
);

useHead(() => createHeadConfig(routeSeo.value) as any);

watch(
  () => route.fullPath,
  () => {
    applyRouteSeo(route.meta.seo as RouteSeoMeta | undefined, { currentPath: route.path });
  },
  { immediate: true }
);
</script>
