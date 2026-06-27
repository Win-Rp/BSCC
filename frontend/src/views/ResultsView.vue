<template>
  <section class="single-view result-view">
    <!-- 全局 Loading 态：当任务尚未完成时，覆盖在最上层 -->
    <div v-if="isProcessing" class="processing-overlay">
      <div class="processing-content">
        <el-icon class="is-loading processing-icon"><Loading /></el-icon>
        <h2>正在处理您的任务</h2>
        <p>{{ processingMessage }}</p>
        
        <div class="task-recovery-tip">
          <el-alert type="success" :closable="false">
            <template #title>
              <div class="recovery-title">
                <el-icon><InfoFilled /></el-icon>
                查重耗时较长？您可以离开页面稍后查看
              </div>
            </template>
            <div class="recovery-desc">
              请复制并保存下方任务号，7天内随时可凭此任务号找回查重结果。
            </div>
            <div class="task-id-box">
              <span class="task-id-text">{{ taskNo }}</span>
              <el-button size="small" type="primary" plain @click="copyTaskLink">复制任务ID</el-button>
            </div>
          </el-alert>
        </div>
      </div>
    </div>

    <!-- 结果就绪后的大盘展示 -->
    <template v-else>
      <el-card shadow="never" class="glass-card">
        <template #header>
          <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 16px;">
              <h2 style="margin: 0;">查重排行与数据可视化</h2>
              <el-tooltip content="结果将为您保留7天，您可随时凭任务号找回" placement="top">
                <el-tag type="info" class="task-id-tag" @click="copyTaskLink" style="margin: 0;">
                  任务号：{{ taskNo }}
                  <el-icon class="copy-icon"><CopyDocument /></el-icon>
                </el-tag>
              </el-tooltip>
            </div>
            <el-tag :type="summary?.payment_required ? 'warning' : 'success'">
              {{ summary?.payment_required ? "待支付解锁" : "完整详情可用" }}
            </el-tag>
          </div>
        </template>

        <div class="results-layout view-grid" v-if="summary">
          <section class="main-stack">
            <el-card shadow="never" class="glass-card" style="margin-bottom: 32px;">
              <div class="detail-section__head" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div style="display: flex; align-items: center;">
                  <h3 style="display: inline-block; margin: 0 16px 0 0;">总体查重结果</h3>
                </div>
                
                <el-tag v-if="summary?.a_file" type="info" effect="plain" style="margin: 0;">
                  主标书：{{ summary.a_file.name }}
                </el-tag>
              </div>
            
            <el-table 
              :data="rankRows" 
              style="width: 100%" 
              @row-click="handleSelectResult"
              highlight-current-row
            >
            <el-table-column prop="rank" label="#" width="50" />
            <el-table-column prop="name" label="B 文件" min-width="180" show-overflow-tooltip />
            <el-table-column prop="score" label="总相似度" width="90">
              <template #default="{ row }">
                <strong>{{ row.score }}%</strong>
              </template>
            </el-table-column>
            <el-table-column prop="breakdown" label="风险摘要" min-width="180" />
            <el-table-column label="重复片段数" min-width="180">
              <template #default="{ row }">
                <div class="match-counts">
                  <el-tag size="small" type="danger" effect="plain" v-if="row.exactCount > 0">
                    完全: {{ row.exactCount }}
                  </el-tag>
                  <el-tag size="small" type="warning" effect="plain" v-if="row.rewriteCount > 0">
                    改写: {{ row.rewriteCount }}
                  </el-tag>
                  <el-tag size="small" type="info" effect="plain" v-if="row.semanticCount > 0">
                    语义: {{ row.semanticCount }}
                  </el-tag>
                  <span v-if="!row.exactCount && !row.rewriteCount && !row.semanticCount" class="no-match">
                    无
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="风险等级" width="90">
              <template #default="{ row }">
                <el-tag :type="row.levelType" effect="light">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="handleSelectResult(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

              <el-card shadow="never" class="glass-card detail-section-card" v-if="detailAvailable || summary?.payment_required">
                <div class="detail-panel__content" v-loading="loadingDetail">
                  <template v-if="detailAvailable">
              <div class="explain-table">
              <h3>
                重复片段摘录 
                <span class="table-subtitle" v-if="totalMatches > 0">
                  (共 {{ totalMatches }} 处，预览前 {{ matchRows.length }} 处)
                </span>
              </h3>
              <el-table :data="matchRows" border empty-text="当前未返回重复片段">
                <el-table-column label="类型" width="100">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.match_type === 'exact' ? 'danger' : 'warning'"
                      size="small"
                      effect="dark"
                    >
                      {{ row.match_type === 'exact' ? '完全重复' : '改写相似' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="a_text" label="主标书 A 片段" min-width="260">
                  <template #default="{ row }">
                    <div class="text-snippet">{{ row.a_text }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="b_text" label="对比标书 B 片段" min-width="260">
                  <template #default="{ row }">
                    <div class="text-snippet">{{ row.b_text }}</div>
                  </template>
                </el-table-column>
                <el-table-column label="相似度" width="90">
                  <template #default="{ row }">
                    {{ toPercent(row.similarity) }}%
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="table-footer-action">
                  <el-button class="mega-compare-btn" @click="goCompare">
                    <span class="mega-compare-btn__main">进入对比页查看全部明细</span>
                    <el-icon class="mega-compare-btn__icon"><ArrowRight /></el-icon>
                  </el-button>
                </div>
            </div>

            <div class="explain-table">
              <h3 class="table-title-with-help">
                <span>格式相似项 ({{ formatRows.length }})</span>
                <el-tooltip
                  content="“句子数量”和“段落数量”是系统解析后的结构统计值，用来判断两份文档的组织方式是否接近，不直接表示正文内容是否相同。"
                  placement="top"
                >
                  <el-icon class="table-title-with-help__icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </h3>
              <el-table :data="formatRows" border empty-text="未发现格式相似">
                <el-table-column label="检测项" width="160">
                  <template #default="{ row }">
                    <div class="table-item-name">
                      <span>{{ row.item_name }}</span>
                      <el-tooltip v-if="formatItemHelp(row.item_name)" :content="formatItemHelp(row.item_name)" placement="top">
                        <el-icon class="table-item-name__icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="a_value" label="A 标书" min-width="160" />
                <el-table-column prop="b_value" label="B 标书" min-width="160" />
                <el-table-column label="相似度" width="120">
                  <template #default="{ row }">{{ toPercent(row.similarity) }}%</template>
                </el-table-column>
                <el-table-column prop="description" label="说明" min-width="200" />
              </el-table>
            </div>

            <div class="explain-table">
              <h3>元数据对比 ({{ metadataRows.length }})</h3>
              <el-table :data="metadataRows" border empty-text="未提取到元数据">
                <el-table-column prop="field_name" label="属性" width="160" />
                <el-table-column prop="a_value" label="A 标书" min-width="160" />
                <el-table-column prop="b_value" label="B 标书" min-width="160" />
                <el-table-column label="判断" width="120">
                  <template #default="{ row }">
                    <el-tag :type="metadataTagType(row.similarity_type)">{{ metadataLabel(row.similarity_type) }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="explain-table">
              <h3>关键字命中 ({{ keywordRows.length }})</h3>
              <el-table :data="keywordRows" border empty-text="当前未返回关键字详情">
                <el-table-column prop="keyword" label="关键字" width="130" />
                <el-table-column prop="hit_text" label="命中文本" min-width="220" />
                <el-table-column label="位置" width="160">
                  <template #default="{ row }">
                    第 {{ row.position.paragraph }} 段 / 第 {{ row.position.sentence }} 句
                  </template>
                </el-table-column>
              </el-table>
            </div>
            </template>
            <template v-else-if="!summary?.payment_required">
              <el-empty description="当前结果没有详情" />
            </template>
          </div>
        </el-card>
      </section>
      
      <aside class="side-stack">
        <el-card shadow="never" class="glass-card">
            <div class="detail-section__head">
              <div>
                <h3>数据可视化</h3>
              </div>
            </div>

            <!-- 总体排行柱状图 -->
            <div class="chart-container" style="height: 280px; width: 100%; margin-bottom: 24px;">
              <v-chart class="chart" :option="rankChartOption" autoresize />
            </div>

            <!-- 选中结果风险雷达图 -->
            <template v-if="detailAvailable">
              <el-divider border-style="dashed" />
              <div class="chart-container" style="height: 300px; width: 100%; margin-top: 24px;">
                <v-chart class="chart" :option="detailRadarOption" autoresize />
              </div>
            </template>

            <!-- 关键字命中词云/饼图 -->
            <template v-if="detailAvailable && keywordRows.length > 0">
              <el-divider border-style="dashed" />
              <div class="chart-container" style="height: 280px; width: 100%; margin-top: 24px;">
                <v-chart class="chart" :option="keywordChartOption" autoresize />
              </div>
            </template>

            <div class="action-strip" v-if="summary?.payment_required">
              <div class="inline-tags">
                <el-tag type="warning">完整详情需支付</el-tag>
              </div>
              <el-button type="primary" @click="paymentVisible = true">支付解锁</el-button>
            </div>
          </el-card>
      </aside>
    </div>
    
      <PaymentDialog v-model="paymentVisible" :task-no="taskNo" @paid="handlePaid" />
    </el-card>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  Document,
  Loading,
  QuestionFilled,
  ArrowRight,
  InfoFilled,
  CopyDocument
} from "@element-plus/icons-vue";
import type { EChartsOption } from "echarts";
import VChart from "vue-echarts";
import PaymentDialog from "@/components/PaymentDialog.vue";
import {
  getDetail,
  getTaskSummary,
  getTaskStatus,
  type CompareDetail,
  type SummaryResult,
  type TaskSummary
} from "@/services/api";
import { getTaskNo, saveTaskNo } from "@/services/session";
import { isTaskProcessing as isProcessing } from "@/composables/useTaskState";

interface RankRow {
  id: number;
  rank: number;
  name: string;
  score: number;
  breakdown: string;
  level: string;
  levelType: "danger" | "warning" | "success";
  exactCount: number;
  rewriteCount: number;
  semanticCount: number;
  rawItem: any;
}

const router = useRouter();
const route = useRoute();
const summary = ref<TaskSummary | null>(null);
const selectedResultId = ref<number>(Number(route.query.result || 0));
const selectedDetail = ref<CompareDetail | null>(null);
const paymentVisible = ref(false);
const loadingDetail = ref(false);
isProcessing.value = true;
const processingMessage = ref("正在查询任务状态...");
const detailError = ref("");
let pollTimer: number | undefined;

const taskNo = computed(() => String(route.query.task ?? "") || getTaskNo());
const selectedResult = computed(() => {
  return summary.value?.results.find((item) => item.compare_result_id === selectedResultId.value) ?? null;
});
const detailAvailable = computed(() => Boolean(selectedDetail.value));
const detailMessage = computed(() => {
  if (loadingDetail.value) return "";
  if (detailError.value) return detailError.value;
  if (!detailAvailable.value && summary.value?.payment_required) {
    return "当前任务尚未解锁完整详情，可先查看摘要排行与免费预览。";
  }
  if (!detailAvailable.value) {
    return "当前结果尚未返回完整详情，可稍后刷新。";
  }
  return "";
});
const rankRows = computed(() => (summary.value?.results ?? []).map((item, index) => toRankRow(item, index + 1)));
const formatRows = computed(() => selectedDetail.value?.format_results ?? []);
const metadataRows = computed(() => selectedDetail.value?.metadata_results ?? []);
const keywordRows = computed(() => selectedDetail.value?.keyword_hits ?? []);
const matchRows = computed(() => {
  const matches = selectedDetail.value?.matches ?? [];
  // 在总览页面仅截取前 5 条重复片段作为预览
  return matches.slice(0, 5);
});
const totalMatches = computed(() => selectedDetail.value?.matches.length ?? 0);

// ECharts 选项：总排行柱状图
const rankChartOption = computed<EChartsOption>(() => {
  const data = [...(summary.value?.results ?? [])].sort((a, b) => b.total_similarity - a.total_similarity);
  const names = data.map((item) => item.b_file_name.length > 12 ? item.b_file_name.substring(0, 12) + "..." : item.b_file_name);
  const scores = data.map((item) => toPercent(item.total_similarity));

  return {
    title: {
      text: "总体相似度排行",
      left: "center",
      textStyle: { fontSize: 14, fontWeight: "normal", color: "#333" }
    },
    tooltip: {
      trigger: "axis",
      formatter: "{b}: {c}%"
    },
    grid: { top: 40, left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: { interval: 0, rotate: 30, overflow: "truncate", width: 80 }
    },
    yAxis: {
      type: "value",
      max: 100,
      axisLabel: { formatter: "{value}%" }
    },
    series: [
      {
        type: "bar",
        data: scores,
        barMaxWidth: 60,
        itemStyle: {
          color: (params: any) => {
            if (params.value >= 70) return "#f56c6c"; // danger
            if (params.value >= 40) return "#e6a23c"; // warning
            return "#67c23a"; // success
          },
          borderRadius: [4, 4, 0, 0]
        },
        label: {
          show: true,
          position: "top",
          formatter: "{c}%"
        }
      }
    ]
  };
});

// ECharts 选项：选中结果多维雷达图
const detailRadarOption = computed<EChartsOption>(() => {
  if (!selectedResult.value) return {};

  return {
    title: {
      text: "多维相似度分析",
      left: "center",
      textStyle: { fontSize: 14, fontWeight: "normal", color: "#333" }
    },
    tooltip: {
      trigger: "item"
    },
    radar: {
      indicator: [
        { name: "完全重复", max: 100 },
        { name: "改写相似", max: 100 },
        { name: "语义相似", max: 100 },
        { name: "格式相似", max: 100 },
        { name: "元数据相似", max: 100 }
      ],
      center: ["50%", "55%"],
      radius: "60%"
    },
    series: [
      {
        name: "相似度多维分析",
        type: "radar",
        data: [
          {
            value: [
              toPercent(selectedResult.value.exact_similarity),
              toPercent(selectedResult.value.rewrite_similarity),
              toPercent(selectedResult.value.semantic_similarity),
              toPercent(selectedResult.value.format_similarity),
              toPercent(selectedResult.value.metadata_similarity)
            ],
            name: selectedResult.value.b_file_name,
            areaStyle: {
              color: "rgba(17, 17, 17, 0.1)"
            },
            lineStyle: {
              color: "#111"
            },
            itemStyle: {
              color: "#111"
            }
          }
        ]
      }
    ]
  };
});

// ECharts 选项：关键字命中统计饼图
const keywordChartOption = computed<EChartsOption>(() => {
  if (!keywordRows.value.length) return {};

  // 统计每个关键字的命中次数
  const keywordCounts: Record<string, number> = {};
  keywordRows.value.forEach((hit) => {
    keywordCounts[hit.keyword] = (keywordCounts[hit.keyword] || 0) + 1;
  });

  const data = Object.entries(keywordCounts).map(([name, value]) => ({
    name,
    value
  })).sort((a, b) => b.value - a.value);

  return {
    title: {
      text: "关键字命中统计",
      left: "center",
      textStyle: { fontSize: 14, fontWeight: "normal", color: "#333" }
    },
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c} 次 ({d}%)"
    },
    legend: {
      orient: "horizontal",
      bottom: "bottom",
      textStyle: { fontSize: 12, color: "#666" }
    },
    series: [
      {
        name: "命中次数",
        type: "pie",
        radius: ["40%", "70%"],
        center: ["50%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: "#fff",
          borderWidth: 2
        },
        label: {
          show: false,
          position: "center"
        },
        emphasis: {
          label: {
            show: true,
            fontSize: "16",
            fontWeight: "bold"
          }
        },
        labelLine: {
          show: false
        },
        data: data,
        // 使用内置调色盘或自定义颜色
        color: ["#111", "#444", "#777", "#999", "#bbb", "#ddd"]
      }
    ]
  };
});

function handleSelectResult(row: RankRow) {
  selectedResultId.value = row.id;
  void loadEvidence();
}

async function loadSummary() {
  if (!taskNo.value) {
    ElMessage.warning("没有找到任务号，请先上传文件");
    await router.push("/upload");
    return;
  }

  summary.value = await getTaskSummary(taskNo.value);
  saveTaskNo(summary.value.task_no);

  if (!selectedResultId.value) {
    selectedResultId.value = summary.value.results[0]?.compare_result_id ?? 0;
  }
}

async function loadEvidence(forceMessage = false) {
  if (!taskNo.value || !selectedResultId.value) return;

  selectedDetail.value = null;
  detailError.value = "";
  loadingDetail.value = true;

  try {
    const response = await getDetail(taskNo.value, selectedResultId.value);
    selectedDetail.value = response;
  } catch (error) {
    selectedDetail.value = null;
    detailError.value = error instanceof Error ? error.message : "详情加载失败";
    if (forceMessage && !summary.value?.payment_required) {
      ElMessage.error(detailError.value);
    }
  } finally {
    loadingDetail.value = false;
  }
}

async function handlePaid() {
  paymentVisible.value = false;
  await loadSummary();
  await loadEvidence(true);
}

function copyTaskLink() {
  navigator.clipboard.writeText(taskNo.value).then(() => {
    ElMessage.success("任务ID已复制，您可在上传界面点击“找回历史任务结果”进行查看");
  }).catch(() => {
    ElMessage.success(`任务号: ${taskNo.value}`);
  });
}

function goCompare() {
  if (!selectedResultId.value) return;
  void router.push({
    path: "/compare",
    query: { task: taskNo.value, result: selectedResultId.value }
  });
}

function toPercent(value = 0) {
  return Math.round(value * 100);
}

function toRankRow(row: SummaryResult, rank: number): RankRow {
  const score = toPercent(row.total_similarity);
  return {
    id: row.compare_result_id,
    rank,
    name: row.b_file_name,
    score,
    breakdown: `完全 ${toPercent(row.exact_similarity)}% / 改写 ${toPercent(row.rewrite_similarity)}% / 语义 ${toPercent(row.semantic_similarity)}%`,
    level: score >= 70 ? "高风险" : score >= 40 ? "中风险" : "低风险",
    levelType: score >= 70 ? "danger" : score >= 40 ? "warning" : "success",
    exactCount: (row as any).exact_count || 0,
    rewriteCount: (row as any).rewrite_count || 0,
    semanticCount: (row as any).semantic_count || 0,
    rawItem: row
  };
}

function metadataLabel(type: string) {
  return { same: "相同", similar: "相近", different: "不同", missing: "缺失" }[type] ?? type;
}

function metadataTagType(type: string) {
  return type === "same" ? "danger" : type === "similar" ? "warning" : type === "missing" ? "info" : "success";
}

function formatItemHelp(name: string) {
  const mapping: Record<string, string> = {
    "句子数量": "表示系统把文档解析后得到多少个可比对句子块，比较的是结构规模是否接近，不是直接比较句子内容。",
    "段落数量": "表示系统解析后识别出多少个结构段落，PDF 和 Word 的解析方式不同，因此这个值更偏结构参考。",
    "页数": "表示解析得到的文档页数，用来判断版式规模是否接近。",
    "标题层级": "表示系统识别到的标题结构数量，用来判断目录和章节组织是否接近。",
    "目录结构": "表示系统识别到的目录痕迹数量，用来辅助判断整体结构是否相似。"
  };
  return mapping[name] ?? "";
}

async function pollTaskStatus() {
  if (!taskNo.value) return;
  try {
    const status = await getTaskStatus(taskNo.value);
    if (status.status === "failed") {
      isProcessing.value = true;
      processingMessage.value = status.error_message || "任务执行失败，请检查文件内容后重新发起。";
      window.clearInterval(pollTimer);
      return;
    }

    if (["completed", "awaiting_payment"].includes(status.status)) {
      window.clearInterval(pollTimer);
      isProcessing.value = false;
      await loadSummary();
      await loadEvidence();
      return;
    }

    // 仍在处理中
    processingMessage.value = status.message || "后端正在处理，请稍候...";
  } catch (error) {
    window.clearInterval(pollTimer);
    processingMessage.value = "查询任务状态失败";
    ElMessage.error(error instanceof Error ? error.message : "查询任务状态失败");
  }
}

onMounted(async () => {
  if (!taskNo.value) {
    ElMessage.warning("请先上传文件创建任务");
    await router.replace("/upload");
    return;
  }

  try {
    // 开始轮询，替代原有的 Progress 逻辑
    await pollTaskStatus();
    if (isProcessing.value && !processingMessage.value.includes("失败")) {
      pollTimer = window.setInterval(() => {
        void pollTaskStatus();
      }, 2000);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "加载失败");
  }
});

onUnmounted(() => {
  window.clearInterval(pollTimer);
});
</script>

<style scoped>
.task-id-tag {
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: ui-monospace, 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.task-id-tag:hover {
  background: var(--line);
  color: var(--ink);
}

.copy-icon {
  margin-left: 4px;
  vertical-align: -2px;
}

.processing-content h2 {
  margin: 16px 0 8px;
  color: var(--ink);
}

.processing-content p {
  color: var(--muted);
  margin-bottom: 24px;
}

.task-recovery-tip {
  max-width: 460px;
  margin: 0 auto;
  text-align: left;
}

.recovery-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.recovery-desc {
  font-size: 13px;
  margin-top: 8px;
  line-height: 1.5;
  color: var(--ink);
}

.task-id-box {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.8);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--line);
}

.task-id-text {
  font-family: ui-monospace, 'JetBrains Mono', monospace;
  font-weight: 600;
  color: var(--ink);
  font-size: 14px;
}

.table-subtitle {
  font-size: 13px;
  font-weight: normal;
  color: var(--muted);
  margin-left: 8px;
}

.text-snippet {
  font-size: 13px;
  line-height: 1.6;
  color: var(--ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-counts {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.no-match {
  color: var(--muted);
  font-size: 13px;
}

.compare-title-vs {
  display: flex;
  align-items: center;
  background: transparent;
  padding: 0;
  margin: 0;
}

.compare-title-vs__doc {
  font-weight: 500;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
}

.compare-title-vs__badge {
  background: linear-gradient(135deg, #f56c6c, #ff9800);
  color: white;
  font-size: 12px;
  font-weight: 800;
  font-style: italic;
  padding: 2px 8px;
  border-radius: 4px;
  margin: 0 16px;
  letter-spacing: 1px;
}

.explain-table {
  margin-bottom: 40px;
}

.table-footer-action {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.mega-compare-btn {
  height: auto;
  padding: 16px 48px 16px 32px; /* 增加右侧 padding 为图标留出空间 */
  border-radius: 12px;
  background: linear-gradient(135deg, #111, #333);
  color: white;
  border: none;
  display: flex;
  flex-direction: row; /* 改为横向排列以适应主文本和图标 */
  align-items: center;
  justify-content: center;
  gap: 12px; /* 文本和图标之间的间距 */
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.mega-compare-btn__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.mega-compare-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
  background: linear-gradient(135deg, #000, #222);
}

.mega-compare-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mega-compare-btn__main {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
}

.mega-compare-btn__icon {
  font-size: 24px;
  opacity: 0.8;
  transition: transform 0.3s ease;
}

.mega-compare-btn:hover .mega-compare-btn__icon {
  transform: translateX(4px);
}
</style>
