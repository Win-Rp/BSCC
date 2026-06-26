<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import DocumentOriginalPane from "@/components/DocumentOriginalPane.vue";
import {
  getDetail,
  getOriginalFileAUrl,
  getOriginalFileBUrl,
  getTaskSummary,
  type CompareDetail,
  type MatchSegment,
  type TaskSummary
} from "@/services/api";
import { getTaskNo } from "@/services/session";

const route = useRoute();
const router = useRouter();
const taskNo = ref(String(route.query.task ?? "") || getTaskNo());
const summary = ref<TaskSummary | null>(null);
const detail = ref<CompareDetail | null>(null);
const activeResultId = ref(Number(route.query.result || 0));
const activeMatchIndex = ref(0);

const resultOptions = computed(() =>
  (summary.value?.results ?? []).map((row) => ({
  id: row.compare_result_id,
  name: row.b_file_name
})));

const matches = computed(() => detail.value?.matches ?? []);
const selectedMatch = computed(() => matches.value[activeMatchIndex.value] ?? null);
const aFileUrl = computed(() => (taskNo.value ? getOriginalFileAUrl(taskNo.value) : ""));
const bFileUrl = computed(() => (
  taskNo.value && activeResultId.value
    ? getOriginalFileBUrl(taskNo.value, activeResultId.value)
    : ""
));
const currentResultName = computed(() => {
  const current = resultOptions.value.find((item) => item.id === activeResultId.value);
  return current?.name ?? detail.value?.b_document.name ?? "对比文档";
});

function handleResultChange() {
  void loadDetail();
}

function goPrevMatch() {
  if (!matches.value.length) return;
  activeMatchIndex.value = activeMatchIndex.value === 0
    ? matches.value.length - 1
    : activeMatchIndex.value - 1;
}

function goNextMatch() {
  if (!matches.value.length) return;
  activeMatchIndex.value = activeMatchIndex.value === matches.value.length - 1
    ? 0
    : activeMatchIndex.value + 1;
}

async function loadSummary() {
  if (!taskNo.value) {
    ElMessage.warning("没有找到任务号，请先上传文件");
    await router.push("/upload");
    return;
  }

  summary.value = await getTaskSummary(taskNo.value);
  if (!activeResultId.value) {
    activeResultId.value = summary.value.results[0]?.compare_result_id ?? 0;
  }
}

async function loadDetail() {
  if (!taskNo.value || !activeResultId.value) return;

  try {
    detail.value = await getDetail(taskNo.value, activeResultId.value);
    activeMatchIndex.value = 0;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "加载对比详情失败");
    await router.push({ path: "/results", query: { task: taskNo.value, result: activeResultId.value } });
  }
}

watch(activeResultId, () => {
  if (activeResultId.value) {
    void router.replace({ path: "/compare", query: { task: taskNo.value, result: activeResultId.value } });
  }
});

onMounted(async () => {
  try {
    await loadSummary();
    await loadDetail();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "加载对比数据失败");
  }
});
</script>

<template>
  <section class="single-view compact-compare compare-original-view">
    <div class="compare-original-toolbar">
      <div class="compare-original-toolbar__heading">
        <h2>原格式文档对比</h2>
        <p>
          {{ detail ? `${detail.a_document.name} 对比 ${currentResultName}` : "正在加载原文档..." }}
        </p>
      </div>

      <div class="compare-original-toolbar__controls">
        <el-select v-model="activeResultId" class="compare-original-toolbar__select" @change="handleResultChange">
          <el-option
            v-for="row in resultOptions"
            :key="row.id"
            :label="row.name"
            :value="row.id"
          />
        </el-select>
        <span class="compare-original-toolbar__status">
          {{ matches.length ? `命中 ${activeMatchIndex + 1} / ${matches.length}` : "当前结果没有命中片段" }}
        </span>
        <el-tag v-if="selectedMatch" effect="plain">{{ selectedMatch.match_type }}</el-tag>
        <el-button plain :disabled="!matches.length" @click="goPrevMatch">上一处</el-button>
        <el-button plain :disabled="!matches.length" @click="goNextMatch">下一处</el-button>
        <el-button plain @click="router.push({ path: '/results', query: { task: taskNo, result: activeResultId } })">
          返回结果页
        </el-button>
      </div>
    </div>

    <div class="doc-grid doc-grid--original">
      <DocumentOriginalPane
        :title="detail?.a_document.name ?? 'A 标书'"
        :file-url="aFileUrl"
        :file-name="detail?.a_document.name ?? ''"
        :active-text="selectedMatch?.a_text ?? ''"
      />

      <DocumentOriginalPane
        :title="detail?.b_document.name ?? 'B 标书'"
        :file-url="bFileUrl"
        :file-name="detail?.b_document.name ?? ''"
        :active-text="selectedMatch?.b_text ?? ''"
      />
    </div>
  </section>
</template>
