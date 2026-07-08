<template>
  <el-config-provider namespace="el" :locale="elementPlusLocale">
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
import { computed, onMounted, watch } from "vue";
import { useHead } from "@unhead/vue";
import { useRoute } from "vue-router";
import AppShell from "@/components/AppShell.vue";
import { initAppLocale, useAppI18n } from "@/composables/useAppI18n";
import { applyRouteSeo, createHeadConfig, resolveRouteSeo, type RouteSeoMeta } from "@/utils/seo";

const route = useRoute();
const { elementPlusLocale, localizeDeep } = useAppI18n();
const routeSeo = computed(() =>
  resolveRouteSeo(localizeDeep(route.meta.seo as RouteSeoMeta | undefined), { currentPath: route.path })
);

useHead(() => createHeadConfig(routeSeo.value) as any);

watch(
  () => route.fullPath,
  () => {
    applyRouteSeo(localizeDeep(route.meta.seo as RouteSeoMeta | undefined), { currentPath: route.path });
  },
  { immediate: true }
);

onMounted(() => {
  initAppLocale();
});
</script>
