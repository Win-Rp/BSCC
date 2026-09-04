<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import DocumentOriginalPane from "@/components/DocumentOriginalPane.vue";
import { ArrowLeft, ArrowRight, Document, Back, Menu } from "@element-plus/icons-vue";
import { useAppI18n } from "@/composables/useAppI18n";
import {
  getDetail,
  getMiniTaskQrcode,
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
const { translateText } = useAppI18n();
const taskNo = ref(String(route.query.task ?? "") || getTaskNo());
const summary = ref<TaskSummary | null>(null);
const detail = ref<CompareDetail | null>(null);
const activeResultId = ref(Number(route.query.result || 0));
const activeMatchIndex = ref(0);
const drawerVisible = ref(false);
const relayOpen = ref(true);
const relayLoading = ref(false);
const relayQrUrl = ref("");

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
  return current?.name ?? detail.value?.b_document.name ?? translateText("对比文档");
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

function handleRowClick(row: MatchSegment) {
  const index = matches.value.findIndex(m => m === row);
  if (index !== -1) {
    activeMatchIndex.value = index;
  }
}

function getRowClassName({ rowIndex }: { rowIndex: number }) {
  return rowIndex === activeMatchIndex.value ? 'is-current-match' : '';
}

async function loadSummary() {
  if (!taskNo.value) {
    ElMessage.warning(translateText("没有找到任务号，请先上传文件"));
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
    ElMessage.error(error instanceof Error ? error.message : translateText("加载对比详情失败"));
    await router.push({ path: "/results", query: { task: taskNo.value, result: activeResultId.value } });
  }
}

watch(activeResultId, () => {
  if (activeResultId.value) {
    void router.replace({ path: "/compare", query: { task: taskNo.value, result: activeResultId.value } });
  }
});

async function loadRelayQr() {
  if (!taskNo.value) return;
  relayLoading.value = true;
  try {
    const res = await getMiniTaskQrcode(taskNo.value, "results");
    relayQrUrl.value = res.data_url || "";
  } catch {
    relayQrUrl.value = "";
  } finally {
    relayLoading.value = false;
  }
}

onMounted(async () => {
  try {
    await loadSummary();
    await loadDetail();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : translateText("加载对比数据失败"));
  }
  void loadRelayQr();
});
</script>

<template>
  <section class="single-view compact-compare compare-original-view">
    <div class="compare-original-toolbar">
      <div class="compare-original-toolbar__heading">
        <div class="heading-with-back">
          <el-button 
            class="back-btn" 
            circle 
            @click="router.push({ path: '/results', query: { task: taskNo, result: activeResultId } })"
          >
            <el-icon><Back /></el-icon>
          </el-button>
          <h2>{{ translateText("原文差异对比") }}</h2>
        </div>
        <div class="compare-title-vs" v-if="detail">
          <span class="compare-title-vs__doc" :title="detail.a_document.name">
            <el-icon><Document /></el-icon> {{ detail.a_document.name }}
          </span>
          <span class="compare-title-vs__badge">VS</span>
          <span class="compare-title-vs__doc" :title="currentResultName">
            <el-icon><Document /></el-icon> {{ currentResultName }}
          </span>
        </div>
        <p v-else class="loading-text">{{ translateText("正在加载原文档...") }}</p>
      </div>

      <div class="compare-original-toolbar__controls">
        <div class="control-group file-selector">
          <span class="control-label">{{ translateText("对比目标") }}</span>
          <el-select v-model="activeResultId" class="compare-original-toolbar__select" @change="handleResultChange">
            <el-option
              v-for="row in resultOptions"
              :key="row.id"
              :label="row.name"
              :value="row.id"
            />
          </el-select>
        </div>

        <div class="control-divider"></div>

        <div class="control-group match-navigator">
          <div class="match-info">
            <el-button 
              circle 
              class="drawer-trigger-btn"
              :disabled="!matches.length"
              @click="drawerVisible = true"
            >
              <el-icon><Menu /></el-icon>
            </el-button>
            <span class="match-count">
              {{ matches.length ? `${activeMatchIndex + 1} / ${matches.length}` : "0 / 0" }}
            </span>
            <span class="match-label">{{ translateText("处重复") }}</span>
            <el-tag 
              v-if="selectedMatch" 
              :type="selectedMatch.match_type === 'exact' ? 'danger' : 'warning'"
              effect="dark" 
              size="small"
              class="match-type-tag"
            >
              {{ translateText(selectedMatch.match_type === 'exact' ? '完全重复' : '改写相似') }}
            </el-tag>
          </div>
          
          <el-button-group class="nav-buttons">
            <el-button 
              type="primary" 
              :disabled="!matches.length" 
              @click="goPrevMatch"
            >
              <el-icon><ArrowLeft /></el-icon>
              {{ translateText("上一处") }}
            </el-button>
            <el-button 
              type="primary" 
              :disabled="!matches.length" 
              @click="goNextMatch"
            >
              {{ translateText("下一处") }}
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>
    </div>

    <!-- 原格式文档对比 (恢复原有的平分布局) -->
    <div class="doc-grid doc-grid--original">
      <DocumentOriginalPane
        :title="detail?.a_document.name ?? translateText('A 标书')"
        :file-url="aFileUrl"
        :file-name="detail?.a_document.name ?? ''"
        :active-text="selectedMatch?.a_text ?? ''"
      />

      <DocumentOriginalPane
        :title="detail?.b_document.name ?? translateText('B 标书')"
        :file-url="bFileUrl"
        :file-name="detail?.b_document.name ?? ''"
        :active-text="selectedMatch?.b_text ?? ''"
      />
    </div>

    <!-- 重复片段抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="translateText('重复片段列表')"
      size="400px"
      :with-header="true"
      class="matches-drawer"
    >
      <div class="matches-table-container">
        <el-table 
          :data="matches" 
          style="width: 100%" 
          :show-header="false"
          highlight-current-row
          :row-class-name="getRowClassName"
          @row-click="handleRowClick"
        >
          <el-table-column>
            <template #default="{ row, $index }">
              <div class="match-cell">
                <div class="match-cell-header">
                  <span class="match-index">#{{ $index + 1 }}</span>
                  <el-tag 
                    :type="row.match_type === 'exact' ? 'danger' : 'warning'"
                    size="small"
                    effect="dark"
                  >
                    {{ translateText(row.match_type === 'exact' ? '完全重复' : '改写相似') }}
                  </el-tag>
                </div>
                <div class="match-cell-text">{{ row.a_text }}</div>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
    <!-- 接力到手机：右侧边缘悬浮卡片，默认展开，可点击收起为侧边小签 -->
    <div class="relay-side" :class="{ 'relay-side--collapsed': !relayOpen }">
      <button type="button" class="relay-side__toggle" @click="relayOpen = !relayOpen">
        <span class="relay-side__toggle-text">{{ translateText("接力到手机") }}</span>
        <span class="relay-side__toggle-arrow" aria-hidden="true">‹</span>
      </button>
      <div class="relay-side__panel">
        <div class="relay-side__text">
          <h4>{{ translateText("接力到手机") }}</h4>
          <p>{{ translateText("扫码在手机上查看本任务结果，可一键转发给同事") }}</p>
        </div>
        <div class="relay-side__qr">
          <img v-if="relayQrUrl" :src="relayQrUrl" :alt="translateText('小程序码')" />
          <span v-else class="relay-side__status">{{ relayLoading ? translateText("正在生成小程序码...") : translateText("小程序码暂不可用") }}</span>
          <span v-if="relayQrUrl" class="relay-side__hint">{{ translateText("微信扫码") }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.compare-original-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  margin-bottom: 20px;
}

.heading-with-back {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.heading-with-back h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
}

.back-btn {
  border: 1px solid var(--line);
  color: var(--ink);
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: var(--ink);
  color: white;
  border-color: var(--ink);
  transform: translateX(-2px);
}

.compare-title-vs {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: rgba(20, 20, 20, 0.03);
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid var(--line);
}

.compare-title-vs__doc {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compare-title-vs__doc .el-icon {
  color: var(--muted);
  font-size: 16px;
}

.compare-title-vs__badge {
  font-size: 12px;
  font-weight: 900;
  font-style: italic;
  color: #fff;
  background: var(--warn);
  padding: 4px 10px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(138, 100, 20, 0.3);
  letter-spacing: 1px;
}

.loading-text {
  color: var(--muted);
  margin: 0;
}

/* 右侧控制区 */
.compare-original-toolbar__controls {
  display: flex;
  align-items: stretch;
  background: rgba(20, 20, 20, 0.02);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 12px;
  gap: 20px;
}

.control-group {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.control-divider {
  width: 1px;
  background: var(--line);
  margin: 4px 0;
}

.control-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.file-selector {
  min-width: 280px;
}

.compare-original-toolbar__select {
  width: 100%;
}

.compare-original-toolbar__select :deep(.el-input__wrapper) {
  background: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
  border-radius: 8px;
}

.match-navigator {
  min-width: 240px;
}

.match-info {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.match-count {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink);
  font-family: ui-monospace, 'JetBrains Mono', monospace;
  line-height: 1;
}

.match-label {
  font-size: 13px;
  color: var(--muted);
}

.match-type-tag {
  margin-left: 8px;
  border: none;
  font-weight: 600;
}

.nav-buttons {
  display: flex;
  width: 100%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-radius: 8px;
}

.nav-buttons .el-button {
  flex: 1;
  border: none;
  background: #111;
  color: white;
}

.nav-buttons .el-button:hover:not(:disabled) {
  background: #333;
}

.nav-buttons .el-button:disabled {
  background: #f5f5f5;
  color: #c0c4cc;
}

.nav-buttons .el-icon {
  margin: 0 4px;
}

.drawer-trigger-btn {
  border: none;
  background: rgba(20, 20, 20, 0.05);
  color: var(--ink);
  transition: all 0.3s ease;
}

.drawer-trigger-btn:hover:not(:disabled) {
  background: var(--ink);
  color: white;
  transform: scale(1.05);
}

.matches-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  font-weight: 700;
}

.matches-drawer :deep(.el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
}

/* 移除旧的侧边栏样式 */

.matches-table-container {
  flex: 1;
  overflow: auto;
}

.match-cell {
  padding: 8px 0;
}

.match-cell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.match-index {
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  font-family: ui-monospace, 'JetBrains Mono', monospace;
}

.match-cell-text {
  font-size: 13px;
  color: var(--ink);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 覆盖 el-table 默认样式以适配侧边栏 */
.matches-table-container :deep(.el-table) {
  --el-table-border-color: var(--line);
  --el-table-row-hover-bg-color: rgba(20, 20, 20, 0.03);
}

.matches-table-container :deep(.el-table__row) {
  cursor: pointer;
}

.matches-table-container :deep(.is-current-match) {
  background-color: rgba(187, 58, 47, 0.05) !important;
}

.matches-table-container :deep(.is-current-match .match-index) {
  color: var(--risk);
}

/* 接力到手机：右侧边缘悬浮卡片 */
.relay-side {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: stretch;
  z-index: 90;
  transition: transform 0.3s ease;
}

.relay-side__toggle {
  flex: none;
  width: 32px;
  border: 1px solid rgba(18, 110, 106, 0.4);
  border-right: none;
  border-radius: 10px 0 0 10px;
  background: #126e6a;
  color: #fff;
  cursor: pointer;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.relay-side__toggle-text {
  writing-mode: vertical-rl;
  letter-spacing: 3px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.relay-side__toggle-arrow {
  font-size: 14px;
  line-height: 1;
  transition: transform 0.3s ease;
}

.relay-side--collapsed .relay-side__toggle-arrow {
  transform: rotate(180deg);
}

.relay-side__panel {
  width: 236px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 14px 14px 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(18, 110, 106, 0.35);
  border-right: none;
  border-radius: 14px 0 0 14px;
  box-shadow: -6px 4px 24px rgba(0, 0, 0, 0.1);
}

.relay-side--collapsed .relay-side__panel {
  display: none;
}

.relay-side__text {
  flex: 1;
  min-width: 0;
}

.relay-side__text h4 {
  margin: 0 0 6px;
  font-size: 14px;
  color: var(--ink);
}

.relay-side__text p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--muted);
}

.relay-side__qr {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.relay-side__qr img {
  width: 84px;
  height: 84px;
  border-radius: 8px;
  border: 1px solid var(--line);
}

.relay-side__hint {
  font-size: 11px;
  color: var(--muted);
}

.relay-side__status {
  width: 84px;
  height: 84px;
  padding: 8px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  line-height: 1.5;
  color: var(--muted);
  text-align: center;
  border-radius: 8px;
  background: rgba(17, 17, 17, 0.04);
}

@media (max-width: 640px) {
  .relay-side__panel {
    width: 200px;
    padding: 10px 10px 10px 14px;
  }

  .relay-side__qr img,
  .relay-side__status {
    width: 72px;
    height: 72px;
  }
}
</style>
