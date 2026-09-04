<template>
  <section class="single-view result-view">
    <!-- 全局 Loading 态：当任务尚未完成时，覆盖在最上层 -->
    <div v-if="isProcessing" class="processing-overlay">
      <div class="processing-content">
        <el-icon class="is-loading processing-icon"><Loading /></el-icon>
        <h2>{{ translateText("正在处理您的任务") }}</h2>
        <p>{{ processingMessage }}</p>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          class="processing-queue-tip"
          title="当前人数较多，受服务器性能所限，当前查重可能较慢。你可以收藏当前页面，或记录任务 ID 后等待一段时间再回来查看查询结果。"
        />

        <div class="task-recovery-tip">
          <el-alert type="success" :closable="false">
            <template #title>
              <div class="recovery-title">
                <el-icon><InfoFilled /></el-icon>
                {{ translateText("查重耗时较长？您可以离开页面稍后查看") }}
              </div>
            </template>
            <div class="recovery-desc">
              {{ translateText("请复制并保存下方任务号，7天内随时可凭此任务号找回查重结果。") }}
            </div>
            <div class="task-id-box">
              <span class="task-id-text">{{ taskNo }}</span>
              <el-button size="small" type="primary" plain @click="copyTaskLink">{{ translateText("复制任务ID") }}</el-button>
            </div>
          </el-alert>

          <!-- 接力到手机：内联小程序码，扫码在手机上继续跟踪本任务 -->
          <div class="relay-inline">
            <div class="relay-inline__text">
              <strong>{{ translateText("接力到手机") }}</strong>
              <span>{{ translateText("扫码后在手机上跟踪任务进度，查重完成微信即时通知") }}</span>
            </div>
            <div class="relay-inline__qr">
              <img v-if="relayQrUrl" :src="relayQrUrl" :alt="translateText('小程序码')" />
              <span v-else class="relay-inline__status">{{ relayLoading ? translateText("正在生成小程序码...") : translateText("小程序码暂不可用") }}</span>
              <span v-if="relayQrUrl" class="relay-inline__hint">{{ translateText("微信扫码") }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果就绪后的大盘展示 -->
    <template v-else>
      <el-card shadow="never" class="glass-card">
        <template #header>
          <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 16px;">
              <h2 style="margin: 0;">{{ translateText("查重排行与数据可视化") }}</h2>
              <el-tooltip :content="translateText('结果将为您保留7天，您可随时凭任务号找回')" placement="top">
                <el-tag type="info" class="task-id-tag" @click="copyTaskLink" style="margin: 0;">
                  {{ translateText("任务号") }}：{{ taskNo }}
                  <el-icon class="copy-icon"><CopyDocument /></el-icon>
                </el-tag>
              </el-tooltip>
            </div>
              <el-tag :type="summary?.payment_required ? 'warning' : 'success'">
                {{ summary?.payment_required ? translateText("待支付解锁") : translateText("完整详情可用") }}
              </el-tag>
          </div>
        </template>

        <div class="results-layout view-grid" v-if="summary">
          <section class="main-stack">
            <el-card shadow="never" class="glass-card" style="margin-bottom: 32px;">
              <div class="detail-section__head" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div style="display: flex; align-items: center;">
                  <h3 style="display: inline-block; margin: 0 16px 0 0;">{{ translateText("总体查重结果") }}</h3>
                </div>
                
                <el-tag v-if="summary?.a_file" type="info" effect="plain" style="margin: 0;">
                  {{ translateText("主标书") }}：{{ summary.a_file.name }}
                </el-tag>
              </div>
            
            <el-table 
              :data="rankRows" 
              style="width: 100%" 
              @row-click="handleSelectResult"
              highlight-current-row
            >
            <el-table-column prop="rank" label="#" width="50" />
            <el-table-column prop="name" :label="translateText('B 文件')" min-width="180" show-overflow-tooltip />
            <el-table-column prop="score" :label="translateText('总相似度')" width="90">
              <template #default="{ row }">
                <strong>{{ row.score }}%</strong>
              </template>
            </el-table-column>
            <el-table-column prop="breakdown" :label="translateText('风险摘要')" min-width="180" />
            <el-table-column :label="translateText('重复片段数')" min-width="180">
              <template #default="{ row }">
                <div class="match-counts">
                  <el-tag size="small" type="danger" effect="plain" v-if="row.exactCount > 0">
                    {{ translateText("完全") }}: {{ row.exactCount }}
                  </el-tag>
                  <el-tag size="small" type="warning" effect="plain" v-if="row.rewriteCount > 0">
                    {{ translateText("改写") }}: {{ row.rewriteCount }}
                  </el-tag>
                  <el-tag size="small" type="info" effect="plain" v-if="row.semanticCount > 0">
                    {{ translateText("语义") }}: {{ row.semanticCount }}
                  </el-tag>
                  <span v-if="!row.exactCount && !row.rewriteCount && !row.semanticCount" class="no-match">
                    {{ translateText("无") }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column :label="translateText('风险等级')" width="90">
              <template #default="{ row }">
                <el-tag :type="row.levelType" effect="light">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="translateText('操作')" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="handleSelectResult(row)">{{ translateText("查看") }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

              <el-card shadow="never" class="glass-card detail-section-card" v-if="detailAvailable || lockedDetail">
                <div class="detail-panel__content" v-loading="loadingDetail">
                  <template v-if="detailAvailable">
              <div class="explain-table">
              <h3>
                {{ translateText("重复片段摘录") }}
                <span class="table-subtitle" v-if="totalMatches > 0">
                  ({{ text("共 {total} 处，预览前 {count} 处", { total: totalMatches, count: matchRows.length }) }})
                </span>
              </h3>
              <el-table :data="matchRows" border :empty-text="translateText('当前未返回重复片段')">
                <el-table-column :label="translateText('类型')" width="100">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.match_type === 'exact' ? 'danger' : 'warning'"
                      size="small"
                      effect="dark"
                    >
                      {{ translateText(row.match_type === 'exact' ? '完全重复' : '改写相似') }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="a_text" :label="translateText('主标书 A 片段')" min-width="260">
                  <template #default="{ row }">
                    <div class="text-snippet">{{ row.a_text }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="b_text" :label="translateText('对比标书 B 片段')" min-width="260">
                  <template #default="{ row }">
                    <div class="text-snippet">{{ row.b_text }}</div>
                  </template>
                </el-table-column>
                <el-table-column :label="translateText('相似度')" width="90">
                  <template #default="{ row }">
                    {{ toPercent(row.similarity) }}%
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="table-footer-action">
                  <el-button class="mega-compare-btn" @click="goCompare">
                    <span class="mega-compare-btn__main">{{ translateText("进入对比页查看全部明细") }}</span>
                    <el-icon class="mega-compare-btn__icon"><ArrowRight /></el-icon>
                  </el-button>
                </div>
            </div>

            <div class="explain-table">
              <h3 class="table-title-with-help">
                <span>{{ translateText("格式相似项") }} ({{ formatRows.length }})</span>
                <el-tooltip
                  :content="translateText('“句子数量”和“段落数量”是系统解析后的结构统计值，用来判断两份文档的组织方式是否接近，不直接表示正文内容是否相同。')"
                  placement="top"
                >
                  <el-icon class="table-title-with-help__icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </h3>
              <el-table :data="formatRows" border :empty-text="translateText('未发现格式相似')">
                <el-table-column :label="translateText('检测项')" width="160">
                  <template #default="{ row }">
                    <div class="table-item-name">
                      <span>{{ row.item_name }}</span>
                      <el-tooltip v-if="formatItemHelp(row.item_name)" :content="formatItemHelp(row.item_name)" placement="top">
                        <el-icon class="table-item-name__icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="a_value" :label="translateText('A 标书')" min-width="160" />
                <el-table-column prop="b_value" :label="translateText('B 文件')" min-width="160" />
                <el-table-column :label="translateText('相似度')" width="120">
                  <template #default="{ row }">{{ toPercent(row.similarity) }}%</template>
                </el-table-column>
                <el-table-column prop="description" :label="translateText('说明')" min-width="200" />
              </el-table>
            </div>

            <div class="explain-table">
              <h3>{{ translateText("元数据对比") }} ({{ metadataRows.length }})</h3>
              <el-table :data="metadataRows" border :empty-text="translateText('未提取到元数据')">
                <el-table-column prop="field_name" :label="translateText('属性')" width="160" />
                <el-table-column prop="a_value" :label="translateText('A 标书')" min-width="160" />
                <el-table-column prop="b_value" :label="translateText('B 文件')" min-width="160" />
                <el-table-column :label="translateText('判断')" width="120">
                  <template #default="{ row }">
                    <el-tag :type="metadataTagType(row.similarity_type)">{{ metadataLabel(row.similarity_type) }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="explain-table">
              <h3>{{ translateText("关键字命中") }} ({{ keywordRows.length }})</h3>
              <el-table :data="keywordRows" border :empty-text="translateText('当前未返回关键字详情')">
                <el-table-column prop="keyword" :label="translateText('关键字')" width="130" />
                <el-table-column prop="hit_text" :label="translateText('命中文本')" min-width="220" />
                <el-table-column :label="translateText('位置')" width="160">
                  <template #default="{ row }">
                    {{ text("第 {paragraph} 段 / 第 {sentence} 句", { paragraph: row.position.paragraph, sentence: row.position.sentence }) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
            </template>
            <template v-else-if="lockedDetail">
              <div class="explain-table">
                <h3>
                  {{ translateText("重复片段摘录") }}
                  <span class="table-subtitle" v-if="totalMatches > 0">
                    ({{ text("已展示前 {count} 处预览", { count: matchRows.length }) }})
                  </span>
                </h3>
                <el-alert
                  type="warning"
                  :closable="false"
                  :title="translateText('当前任务尚未支付，以下为免费重复片段预览，完整详情解锁后可查看全部明细。')"
                  style="margin-bottom: 16px;"
                />
                <el-table :data="matchRows" border :empty-text="translateText('当前暂无可展示的重复片段预览')">
                  <el-table-column :label="translateText('类型')" width="100">
                    <template #default="{ row }">
                      <el-tag
                        :type="row.match_type === 'exact' ? 'danger' : 'warning'"
                        size="small"
                        effect="dark"
                      >
                        {{ translateText(row.match_type === 'exact' ? '完全重复' : '改写相似') }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="a_text" :label="translateText('主标书 A 片段')" min-width="260">
                    <template #default="{ row }">
                      <div class="text-snippet">{{ row.a_text }}</div>
                    </template>
                  </el-table-column>
                  <el-table-column prop="b_text" :label="translateText('对比标书 B 片段')" min-width="260">
                    <template #default="{ row }">
                      <div class="text-snippet">{{ row.b_text }}</div>
                    </template>
                  </el-table-column>
                  <el-table-column :label="translateText('相似度')" width="90">
                    <template #default="{ row }">
                      {{ toPercent(row.similarity) }}%
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div class="explain-table">
                <h3>{{ translateText("格式相似项") }}</h3>
                <div class="locked-group">
                  <el-empty :description="translateText('支付解锁后显示格式相似项明细')" />
                </div>
              </div>

              <div class="explain-table">
                <h3>{{ translateText("元数据对比") }}</h3>
                <div class="locked-group">
                  <el-empty :description="translateText('支付解锁后显示元数据对比结果')" />
                </div>
              </div>

              <div class="explain-table">
                <h3>{{ translateText("关键字命中") }}</h3>
                <div class="locked-group">
                  <el-empty :description="translateText('支付解锁后显示关键字命中详情')" />
                </div>
              </div>

            </template>
            <template v-else-if="!summary?.payment_required">
              <el-empty :description="translateText('当前结果没有详情')" />
            </template>
          </div>
        </el-card>
      </section>
      
      <aside class="side-stack">
        <section v-if="summary?.payment_required" class="unlock-offer-card unlock-offer-card--sidebar">
          <div class="unlock-offer-card__badge">{{ promoBadgeText }}</div>
          <div class="unlock-offer-card__content">
            <div class="unlock-offer-card__text">
              <h3>{{ hasPromo ? translateText("先锁定优惠，再看完整详情") : translateText("支付后立即查看完整详情") }}</h3>
              <p>
                {{ translateText("完整解锁全部重复片段、格式相似项、元数据对比与关键字命中。") }}
                <template v-if="hasPromo && promoSummary">
                  {{ text("当前仅需 {price} / 每份对比文件，原价 {origin}，本次任务可立省 {save}。", {
                    price: formatMoney(promoSummary.effective_unit_price_cents),
                    origin: formatMoney(promoSummary.original_unit_price_cents),
                    save: formatMoney(promoSummary.savings_cents)
                  }) }}
                </template>
                <template v-else>
                  {{ translateText("当前按标准价格解锁，支付后立即开放全部详情与后续回看权限。") }}
                </template>
              </p>
              <div v-if="hasPromo" class="unlock-offer-card__promo-strip">
                <span>{{ translateText("原价总额") }} {{ formatMoney(promoSummary?.original_amount_cents ?? 0) }}</span>
                <span>{{ translateText("现价") }} {{ formatMoney(promoSummary?.effective_amount_cents ?? 0) }}</span>
                <span>{{ translateText("立省") }} {{ promoDiscountText }}</span>
              </div>
              <div v-if="showPromoCountdown" class="unlock-offer-card__countdown">
                <span>{{ translateText("距优惠结束仅剩") }}</span>
                <strong>{{ promoCountdownText }}</strong>
              </div>
              <div class="unlock-offer-card__chips">
                <span>{{ promoNoteText }}</span>
                <span>{{ translateText("结果保留期内随时回看") }}</span>
                <span>{{ promoLossAversionText }}</span>
              </div>
            </div>
            <div class="unlock-offer-card__action">
              <div class="unlock-offer-card__price">
                {{ promoSummary ? formatMoney(promoSummary.effective_amount_cents) : translateText("生成订单后显示") }}
              </div>
              <div v-if="promoSummary" class="unlock-offer-card__price-note">
                {{ summary?.b_file_count || 0 }} {{ translateText("份对比文件") }}
              </div>
              <el-button type="danger" class="unlock-offer-card__button" @click="paymentVisible = true">
                {{ hasPromo ? translateText("立即锁定优惠") : translateText("立即支付解锁") }}
              </el-button>
            </div>
          </div>
        </section>

        <!-- 接力到手机：内联小程序码，扫码在手机查看结果并可转发 -->
        <el-card shadow="never" class="glass-card relay-card">
          <div class="relay-card__content">
            <div class="relay-card__text">
              <h4>{{ translateText("接力到手机") }}</h4>
              <p>{{ translateText("扫码在手机上查看本任务结果，可一键转发给同事") }}</p>
            </div>
            <div class="relay-card__qr">
              <img v-if="relayQrUrl" :src="relayQrUrl" :alt="translateText('小程序码')" />
              <span v-else class="relay-card__status">{{ relayLoading ? translateText("正在生成小程序码...") : translateText("小程序码暂不可用") }}</span>
              <span v-if="relayQrUrl" class="relay-card__hint">{{ translateText("微信扫码") }}</span>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="glass-card side-stack__chart-card">
          <div class="detail-section__head side-stack__head">
            <div>
              <h3>{{ translateText("数据可视化") }}</h3>
              <p>{{ translateText("从总体风险到单份标书画像，右侧集中查看关键指标。") }}</p>
            </div>
          </div>

          <div class="chart-panel">
            <div class="chart-panel__head">
              <span class="chart-panel__eyebrow">{{ translateText("总览") }}</span>
              <h4>{{ translateText("总体相似度排行") }}</h4>
            </div>
            <div class="chart-container chart-container--rank">
              <v-chart class="chart" :option="rankChartOption" autoresize />
            </div>
          </div>

          <template v-if="detailAvailable">
            <div class="chart-panel chart-panel--soft">
              <div class="chart-panel__head">
                <span class="chart-panel__eyebrow">{{ translateText("当前选中") }}</span>
                <h4>{{ translateText("风险画像分析") }}</h4>
                <p>{{ selectedResult?.b_file_name || translateText("查看当前对比标书的多维相似度分布") }}</p>
              </div>
              <div class="chart-container chart-container--radar">
                <v-chart class="chart" :option="detailRadarOption" autoresize />
              </div>
            </div>
          </template>

          <template v-if="detailAvailable && keywordRows.length > 0">
            <div class="chart-panel chart-panel--soft">
              <div class="chart-panel__head">
                <span class="chart-panel__eyebrow">{{ translateText("命中分析") }}</span>
                <h4>{{ translateText("关键字分布") }}</h4>
                <p>{{ translateText("聚合展示当前选中结果中的高频命中词。") }}</p>
              </div>
              <div class="chart-container chart-container--keyword">
                <v-chart class="chart" :option="keywordChartOption" autoresize />
              </div>
            </div>
          </template>
        </el-card>
      </aside>
    </div>

      <PaymentDialog v-model="paymentVisible" :task-no="taskNo" :b-file-count="summary?.b_file_count || 1" @paid="handlePaid" />
    </el-card>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
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
import { useAppI18n } from "@/composables/useAppI18n";
import {
  getPreview,
  getPublicSiteConfig,
  getDetail,
  getMiniTaskQrcode,
  getTaskSummary,
  getTaskStatus,
  type CompareDetail,
  type MatchSegment,
  type PromoPricingSummary,
  type PublicSiteConfig,
  type SummaryResult,
  type TaskSummary
} from "@/services/api";
import { getTaskNo, saveTaskNo } from "@/services/session";
import { isTaskProcessing as isProcessing } from "@/composables/useTaskState";
import { buildPromoSummary, buildServerOffsetMs, formatCountdown, formatMoney, getRemainingMs } from "@/utils/promo";

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
const { locale, translateText } = useAppI18n();
const summary = ref<TaskSummary | null>(null);
const publicSiteConfig = ref<PublicSiteConfig | null>(null);
const selectedResultId = ref<number>(Number(route.query.result || 0));
const selectedDetail = ref<CompareDetail | null>(null);
const previewMatches = ref<MatchSegment[]>([]);
const paymentVisible = ref(false);
const loadingDetail = ref(false);
const relayLoading = ref(false);
const relayQrUrl = ref("");
const relayQrCache: Record<string, string> = {};
isProcessing.value = true;
const processingMessage = ref(translateText("正在查询任务状态..."));
const detailError = ref("");
let pollTimer: number | undefined;
let promoTimer: number | undefined;
const promoNow = ref(Date.now());

function text(source: string, params?: Record<string, string | number>) {
  return translateText(source).replace(/\{(\w+)\}/g, (_, key) => String(params?.[key] ?? ""));
}

const taskNo = computed(() => String(route.query.task ?? "") || getTaskNo());
const selectedResult = computed(() => {
  return summary.value?.results.find((item) => item.compare_result_id === selectedResultId.value) ?? null;
});
const detailAvailable = computed(() => Boolean(selectedDetail.value));
const lockedDetail = computed(() => Boolean(summary.value?.payment_required && !detailAvailable.value));
const detailMessage = computed(() => {
  if (loadingDetail.value) return "";
  if (detailError.value) return detailError.value;
  if (!detailAvailable.value && summary.value?.payment_required) {
    return translateText("当前任务尚未解锁完整详情，可先查看摘要排行与免费预览。");
  }
  if (!detailAvailable.value) {
    return translateText("当前结果尚未返回完整详情，可稍后刷新。");
  }
  return "";
});
const rankRows = computed(() => (summary.value?.results ?? []).map((item, index) => toRankRow(item, index + 1)));
const formatRows = computed(() => selectedDetail.value?.format_results ?? []);
const metadataRows = computed(() => selectedDetail.value?.metadata_results ?? []);
const keywordRows = computed(() => selectedDetail.value?.keyword_hits ?? []);
const matchRows = computed(() => {
  const matches = selectedDetail.value?.matches ?? previewMatches.value;
  // 在总览页面仅截取前 5 条重复片段作为预览
  return matches.slice(0, 5);
});
const totalMatches = computed(() => selectedDetail.value?.matches.length ?? previewMatches.value.length);
const promoSummary = computed<PromoPricingSummary | null>(() => buildPromoSummary(publicSiteConfig.value?.promo, summary.value?.b_file_count || 1));
const hasPromo = computed(() => Boolean(promoSummary.value?.promo_active));
const promoBadgeText = computed(() => promoSummary.value?.promo_badge || translateText("限时特惠"));
const promoNoteText = computed(() => hasPromo.value ? (promoSummary.value?.promo_note || translateText("完整明细立即开放")) : translateText("完整明细立即开放"));
const promoLossAversionText = computed(() => hasPromo.value ? (promoSummary.value?.promo_loss_aversion_text || translateText("错过后将恢复原价")) : translateText("支付后立即开放完整详情"));
const promoDiscountText = computed(() => `${promoSummary.value?.discount_percent ?? 0}%`);
const promoServerOffsetMs = computed(() => buildServerOffsetMs(publicSiteConfig.value?.promo.server_now));
const showPromoCountdown = computed(() => Boolean(promoSummary.value?.show_countdown && getRemainingMs(promoSummary.value, promoServerOffsetMs.value, promoNow.value) > 0));
const promoCountdownText = computed(() => formatCountdown(getRemainingMs(promoSummary.value, promoServerOffsetMs.value, promoNow.value)));

// ECharts 选项：总排行柱状图
const rankChartOption = computed<EChartsOption>(() => {
  const data = [...(summary.value?.results ?? [])].sort((a, b) => b.total_similarity - a.total_similarity);
  const names = data.map((item) => item.b_file_name.length > 12 ? item.b_file_name.substring(0, 12) + "..." : item.b_file_name);
  const scores = data.map((item) => toPercent(item.total_similarity));

  return {
    tooltip: {
      trigger: "axis",
      formatter: "{b}: {c}%"
    },
    grid: { top: 24, left: "6%", right: "4%", bottom: 64, containLabel: true },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: { interval: 0, rotate: 24, overflow: "truncate", width: 80, margin: 14 }
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
      text: translateText("多维相似度分析"),
      left: "center",
      textStyle: { fontSize: 14, fontWeight: "normal", color: "#333" }
    },
    tooltip: {
      trigger: "item"
    },
    radar: {
      indicator: [
        { name: translateText("完全重复"), max: 100 },
        { name: translateText("改写相似"), max: 100 },
        { name: translateText("语义相似"), max: 100 },
        { name: translateText("格式相似"), max: 100 },
        { name: translateText("元数据相似"), max: 100 }
      ],
      center: ["50%", "55%"],
      radius: "60%"
    },
    series: [
      {
        name: translateText("相似度多维分析"),
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
      text: translateText("关键字命中统计"),
      left: "center",
      textStyle: { fontSize: 14, fontWeight: "normal", color: "#333" }
    },
    tooltip: {
      trigger: "item",
      formatter: `{b}: {c} ${translateText("次")} ({d}%)`
    },
    legend: {
      orient: "horizontal",
      bottom: "bottom",
      textStyle: { fontSize: 12, color: "#666" }
    },
    series: [
      {
        name: translateText("命中次数"),
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
    ElMessage.warning(translateText("没有找到任务号，请先上传文件"));
    await router.push("/upload");
    return;
  }

  summary.value = await getTaskSummary(taskNo.value);
  saveTaskNo(summary.value.task_no);

  if (!selectedResultId.value) {
    selectedResultId.value = summary.value.results[0]?.compare_result_id ?? 0;
  }
}

async function loadPublicSiteConfig() {
  publicSiteConfig.value = await getPublicSiteConfig(locale.value);
}

async function loadEvidence(forceMessage = false) {
  if (!taskNo.value || !selectedResultId.value) return;

  selectedDetail.value = null;
  previewMatches.value = [];
  detailError.value = "";
  loadingDetail.value = true;

  try {
    if (summary.value?.payment_required) {
      try {
        const preview = await getPreview(taskNo.value, selectedResultId.value);
        previewMatches.value = preview.segments ?? [];
      } catch {
        previewMatches.value = [];
      }
    }

    const response = await getDetail(taskNo.value, selectedResultId.value);
    selectedDetail.value = response;
    previewMatches.value = response.matches ?? [];
  } catch (error) {
    selectedDetail.value = null;
    detailError.value = error instanceof Error ? error.message : translateText("详情加载失败");
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
    ElMessage.success(translateText("任务ID已复制，您可在上传界面点击“找回历史任务结果”进行查看"));
  }).catch(() => {
    ElMessage.success(`${translateText("任务号")}: ${taskNo.value}`);
  });
}

async function loadRelayQr(page: "progress" | "results") {
  if (relayQrCache[page]) {
    relayQrUrl.value = relayQrCache[page];
    return;
  }
  relayLoading.value = true;
  relayQrUrl.value = "";
  try {
    const res = await getMiniTaskQrcode(taskNo.value, page);
    relayQrUrl.value = res.data_url || "";
    if (relayQrUrl.value) {
      relayQrCache[page] = relayQrUrl.value;
    }
  } catch {
    relayQrUrl.value = "";
  } finally {
    relayLoading.value = false;
  }
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
    breakdown: text("完全 {exact}% / 改写 {rewrite}% / 语义 {semantic}%", {
      exact: toPercent(row.exact_similarity),
      rewrite: toPercent(row.rewrite_similarity),
      semantic: toPercent(row.semantic_similarity)
    }),
    level: score >= 70 ? translateText("高风险") : score >= 40 ? translateText("中风险") : translateText("低风险"),
    levelType: score >= 70 ? "danger" : score >= 40 ? "warning" : "success",
    exactCount: (row as any).exact_count || 0,
    rewriteCount: (row as any).rewrite_count || 0,
    semanticCount: (row as any).semantic_count || 0,
    rawItem: row
  };
}

function metadataLabel(type: string) {
  return {
    same: translateText("相同"),
    similar: translateText("相近"),
    different: translateText("不同"),
    missing: translateText("缺失")
  }[type] ?? type;
}

function metadataTagType(type: string) {
  return type === "same" ? "danger" : type === "similar" ? "warning" : type === "missing" ? "info" : "success";
}

function formatItemHelp(name: string) {
  const mapping: Record<string, string> = {
    "句子数量": translateText("表示系统把文档解析后得到多少个可比对句子块，比较的是结构规模是否接近，不是直接比较句子内容。"),
    "段落数量": translateText("表示系统解析后识别出多少个结构段落，PDF 和 Word 的解析方式不同，因此这个值更偏结构参考。"),
    "页数": translateText("表示解析得到的文档页数，用来判断版式规模是否接近。"),
    "标题层级": translateText("表示系统识别到的标题结构数量，用来判断目录和章节组织是否接近。"),
    "目录结构": translateText("表示系统识别到的目录痕迹数量，用来辅助判断整体结构是否相似。")
  };
  return mapping[name] ?? "";
}

async function pollTaskStatus() {
  if (!taskNo.value) return;
  try {
    const status = await getTaskStatus(taskNo.value);
    if (status.status === "failed") {
      isProcessing.value = true;
      processingMessage.value = status.error_message || translateText("任务执行失败，请检查文件内容后重新发起。");
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
    processingMessage.value = status.message || translateText("后端正在处理，请稍候...");
  } catch (error) {
    window.clearInterval(pollTimer);
    processingMessage.value = translateText("查询任务状态失败");
    ElMessage.error(error instanceof Error ? error.message : translateText("查询任务状态失败"));
  }
}

onMounted(async () => {
  if (!taskNo.value) {
    ElMessage.warning(translateText("请先上传文件创建任务"));
    await router.replace("/upload");
    return;
  }

  try {
    await loadPublicSiteConfig().catch(() => {
      publicSiteConfig.value = null;
    });
    promoNow.value = Date.now();
    promoTimer = window.setInterval(() => {
      promoNow.value = Date.now();
    }, 1000);
    // 开始轮询，替代原有的 Progress 逻辑
    await pollTaskStatus();
    void loadRelayQr(isProcessing.value ? "progress" : "results");
    if (isProcessing.value && processingMessage.value !== translateText("任务执行失败，请检查文件内容后重新发起。")) {
      pollTimer = window.setInterval(() => {
        void pollTaskStatus();
      }, 2000);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : translateText("加载失败"));
  }
});

onUnmounted(() => {
  window.clearInterval(pollTimer);
  window.clearInterval(promoTimer);
});

watch(locale, () => {
  if (!taskNo.value) return;
  void loadPublicSiteConfig().catch(() => {
    publicSiteConfig.value = null;
  });
});

watch(isProcessing, (processing) => {
  if (!processing) {
    void loadRelayQr("results");
  }
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

.processing-queue-tip {
  max-width: 640px;
  margin: 0 auto 18px;
  border-radius: 14px;
  text-align: left;
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

.relay-inline {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--line);
}

.relay-inline__text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.relay-inline__text strong {
  font-size: 14px;
  color: var(--ink);
}

.relay-inline__text span {
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
}

.relay-inline__qr {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.relay-inline__qr img {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  border: 1px solid var(--line);
}

.relay-inline__hint {
  font-size: 12px;
  color: var(--muted);
}

.relay-inline__status {
  width: 88px;
  height: 88px;
  padding: 8px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  line-height: 1.5;
  color: var(--muted);
  text-align: center;
  border-radius: 8px;
  background: rgba(17, 17, 17, 0.04);
}

.relay-card__content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.relay-card__text {
  flex: 1;
}

.relay-card__text h4 {
  margin: 0 0 6px;
  font-size: 15px;
  color: var(--ink);
}

.relay-card__text p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
}

.relay-card__qr {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.relay-card__qr img {
  width: 96px;
  height: 96px;
  border-radius: 10px;
  border: 1px solid var(--line);
}

.relay-card__hint {
  font-size: 12px;
  color: var(--muted);
}

.relay-card__status {
  width: 96px;
  height: 96px;
  padding: 8px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  line-height: 1.5;
  color: var(--muted);
  text-align: center;
  border-radius: 10px;
  background: rgba(17, 17, 17, 0.04);
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

.locked-group {
  border: 1px dashed var(--line);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  padding: 12px;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.side-stack__chart-card {
  overflow: hidden;
}

.side-stack__head {
  margin-bottom: 18px;
}

.chart-panel {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.62));
  border: 1px solid rgba(17, 17, 17, 0.06);
}

.chart-panel + .chart-panel {
  margin-top: 16px;
}

.chart-panel--soft {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(255, 255, 255, 0.54));
}

.chart-panel__head {
  margin-bottom: 14px;
}

.chart-panel__eyebrow {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.06);
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.4px;
}

.chart-panel__head h4 {
  margin: 10px 0 4px;
  font-size: 16px;
  color: var(--ink);
}

.chart-panel__head p {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.6;
}

.chart-container {
  width: 100%;
}

.chart-container--rank {
  height: 280px;
}

.chart-container--radar {
  height: 300px;
}

.chart-container--keyword {
  height: 280px;
}

.unlock-offer-card {
  position: relative;
  padding: 28px 24px 22px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(245, 108, 108, 0.18), transparent 36%),
    linear-gradient(135deg, rgba(17, 17, 17, 0.98), rgba(54, 32, 18, 0.95));
  color: #fff7ee;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(17, 17, 17, 0.16);
}

.unlock-offer-card--sidebar {
  padding: 24px 20px 20px;
}

.unlock-offer-card::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.06), transparent 38%),
    repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 16px,
      rgba(255, 255, 255, 0.025) 16px,
      rgba(255, 255, 255, 0.025) 32px
    );
  pointer-events: none;
}

.unlock-offer-card__badge {
  position: absolute;
  top: 14px;
  right: 16px;
  z-index: 1;
  padding: 6px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, #ffe08a, #ffb347);
  color: #3c2200;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.8px;
  box-shadow: 0 8px 18px rgba(255, 179, 71, 0.28);
}

.unlock-offer-card__content {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
}

.unlock-offer-card__text h3 {
  margin: 0 0 10px;
  font-size: 24px;
  line-height: 1.3;
  color: #ffffff;
}

.unlock-offer-card__text p {
  margin: 0;
  max-width: 680px;
  font-size: 14px;
  line-height: 1.8;
  color: rgba(255, 247, 238, 0.88);
}

.unlock-offer-card__origin-price {
  text-decoration: line-through;
  color: rgba(255, 247, 238, 0.64);
}

.unlock-offer-card__promo-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.unlock-offer-card__promo-strip span,
.unlock-offer-card__countdown {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 12px;
  color: rgba(255, 247, 238, 0.92);
}

.unlock-offer-card__countdown {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
}

.unlock-offer-card__countdown strong {
  font-size: 15px;
  color: #ffe08a;
  letter-spacing: 1px;
}

.unlock-offer-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.unlock-offer-card__chips span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 12px;
  color: rgba(255, 247, 238, 0.94);
}

.unlock-offer-card__action {
  min-width: 220px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.unlock-offer-card__price {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.4px;
  color: #ffe08a;
}

.unlock-offer-card__price-note {
  font-size: 12px;
  color: rgba(255, 247, 238, 0.72);
}

.unlock-offer-card__button {
  min-width: 200px;
  height: 48px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #ff7a59, #ff3d54);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 16px 30px rgba(255, 61, 84, 0.32);
}

.unlock-offer-card__button:hover {
  background: linear-gradient(135deg, #ff6d4a, #ff304c);
}

.unlock-offer-card--sidebar .unlock-offer-card__content {
  flex-direction: column;
  align-items: stretch;
  gap: 18px;
}

.unlock-offer-card--sidebar .unlock-offer-card__text h3 {
  font-size: 20px;
  line-height: 1.35;
  padding-right: 88px;
}

.unlock-offer-card--sidebar .unlock-offer-card__text p {
  max-width: none;
  line-height: 1.7;
}

.unlock-offer-card--sidebar .unlock-offer-card__action {
  min-width: auto;
  padding: 16px;
  border-radius: 16px;
  align-items: stretch;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.unlock-offer-card--sidebar .unlock-offer-card__price {
  font-size: 30px;
  line-height: 1;
}

.unlock-offer-card--sidebar .unlock-offer-card__button {
  width: 100%;
  min-width: 0;
}

@media (max-width: 900px) {
  .chart-panel {
    padding: 16px;
  }

  .unlock-offer-card__content {
    flex-direction: column;
    align-items: stretch;
  }

  .unlock-offer-card__action {
    min-width: auto;
    align-items: stretch;
  }

  .unlock-offer-card__button {
    width: 100%;
  }

  .unlock-offer-card--sidebar .unlock-offer-card__text h3 {
    padding-right: 72px;
  }
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
