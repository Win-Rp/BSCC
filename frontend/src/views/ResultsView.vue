<template>
  <section class="view-grid result-view">
    <!-- 全局 Loading 态：当任务尚未完成时，覆盖在最上层 -->
    <div v-if="isProcessing" class="processing-overlay">
      <div class="processing-content">
        <el-icon class="is-loading processing-icon"><Loading /></el-icon>
        <h2>正在处理您的任务</h2>
        <p>{{ processingMessage }}</p>
      </div>
    </div>

    <!-- 结果就绪后的大盘展示 -->
    <template v-else>
      <el-card shadow="never" class="glass-card">
        <template #header>
          <div class="card-header">
            <div>
              <h2>查重排行与数据可视化</h2>
            </div>
            <el-tag :type="summary?.payment_required ? 'warning' : 'success'">
              {{ summary?.payment_required ? "待支付解锁" : "完整详情可用" }}
            </el-tag>
          </div>
        </template>

      <section class="section-stack">
        <el-table
          :data="rankRows"
          border
          highlight-current-row
          row-key="id"
          empty-text="暂无结果"
          @row-click="handleSelectResult"
        >
          <el-table-column prop="rank" label="#" width="72" />
          <el-table-column prop="name" label="B 文件" min-width="240" />
          <el-table-column prop="score" label="总相似度" width="140">
            <template #default="{ row }">{{ row.score }}%</template>
          </el-table-column>
          <el-table-column prop="breakdown" label="风险摘要" min-width="260" />
          <el-table-column label="风险等级" width="120">
            <template #default="{ row }">
              <el-tag :type="row.levelType">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="handleSelectResult(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="detail-section" v-if="detailAvailable || summary?.payment_required">
          <div class="detail-section__head">
            <div>
              <h3>选中结果详情</h3>
            </div>
            <div class="button-row">
              <el-button
                type="primary"
                :disabled="!detailAvailable"
                @click="goCompare"
              >
                进入对比页
              </el-button>
            </div>
          </div>

          <el-alert
            v-if="detailMessage"
            :title="detailMessage"
            :type="summary?.payment_required ? 'warning' : 'info'"
            :closable="false"
            show-icon
          />

          <template v-if="detailAvailable">
            <div class="detail-guide">
              <el-alert
                title="看内容是不是一样，优先看“总相似度”“风险摘要”，再点击“进入对比页”查看左右原文高亮对比。格式相似项主要反映结构是否接近，不直接代表内容重复。"
                type="info"
                :closable="false"
                show-icon
              />
            </div>

            <div class="explain-table">
              <h3 class="table-title-with-help">
                <span>格式相似项</span>
                <el-tooltip
                  content="“句子数量”和“段落数量”是系统解析后的结构统计值，用来判断两份文档的组织方式是否接近，不直接表示正文内容是否相同。"
                  placement="top"
                >
                  <el-icon class="table-title-with-help__icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </h3>
              <el-table :data="formatRows" border empty-text="当前未返回格式详情">
                <el-table-column label="项目" width="170">
                  <template #default="{ row }">
                    <div class="table-item-name">
                      <span>{{ row.item_name }}</span>
                      <el-tooltip v-if="formatItemHelp(row.item_name)" :content="formatItemHelp(row.item_name)" placement="top">
                        <el-icon class="table-item-name__icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="a_value" label="A 文件" min-width="180" />
                <el-table-column prop="b_value" label="B 文件" min-width="180" />
                <el-table-column label="相似度" width="120">
                  <template #default="{ row }">{{ toPercent(row.similarity) }}%</template>
                </el-table-column>
                <el-table-column prop="description" label="说明" min-width="160" />
              </el-table>
            </div>

            <div class="explain-table">
              <h3>元数据结果</h3>
              <el-table :data="metadataRows" border empty-text="当前未返回元数据详情">
                <el-table-column prop="field_name" label="字段" width="150" />
                <el-table-column prop="a_value" label="A 文件" min-width="180" />
                <el-table-column prop="b_value" label="B 文件" min-width="180" />
                <el-table-column label="判断" width="120">
                  <template #default="{ row }">
                    <el-tag :type="metadataTagType(row.similarity_type)">{{ metadataLabel(row.similarity_type) }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="explain-table">
              <h3>关键字命中</h3>
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
        </div>
      </section>
      </el-card>

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

        <div class="action-strip" v-if="summary?.payment_required">
          <div class="inline-tags">
            <el-tag type="warning">完整详情需支付</el-tag>
          </div>
          <el-button type="primary" @click="paymentVisible = true">支付解锁</el-button>
        </div>
      </el-card>
    </aside>
    </template>

    <PaymentDialog v-model="paymentVisible" :task-no="taskNo" @paid="handlePaid" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Loading, QuestionFilled } from "@element-plus/icons-vue";
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

interface RankRow {
  id: number;
  rank: number;
  name: string;
  score: number;
  breakdown: string;
  level: string;
  levelType: "danger" | "warning" | "success";
}

const router = useRouter();
const route = useRoute();
const summary = ref<TaskSummary | null>(null);
const selectedResultId = ref<number>(Number(route.query.result || 0));
const selectedDetail = ref<CompareDetail | null>(null);
const paymentVisible = ref(false);
const loadingDetail = ref(false);
const isProcessing = ref(true);
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

// ECharts 选项：总排行柱状图
const rankChartOption = computed<EChartsOption>(() => {
  const data = [...(summary.value?.results ?? [])].sort((a, b) => a.total_similarity - b.total_similarity);
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
      type: "value",
      max: 100,
      axisLabel: { formatter: "{value}%" }
    },
    yAxis: {
      type: "category",
      data: names,
      axisLabel: { width: 100, overflow: "truncate" }
    },
    series: [
      {
        type: "bar",
        data: scores,
        itemStyle: {
          color: (params: any) => {
            if (params.value >= 70) return "#f56c6c"; // danger
            if (params.value >= 40) return "#e6a23c"; // warning
            return "#67c23a"; // success
          },
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: "right",
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
    levelType: score >= 70 ? "danger" : score >= 40 ? "warning" : "success"
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

onBeforeUnmount(() => {
  window.clearInterval(pollTimer);
});
</script>
