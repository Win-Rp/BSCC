<template>
  <section class="single-view">
    <el-card shadow="never" class="glass-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>运营后台</h2>
            <p>围绕真实订单、任务与日志数据进行处理，所有动作都明确绑定到当前选中对象。</p>
          </div>
          <div class="button-row">
            <el-button v-if="token" plain @click="handleLogout">退出登录</el-button>
            <el-button type="primary" :disabled="!token" :loading="loading" @click="loadAdminData">刷新数据</el-button>
          </div>
        </div>
      </template>

      <section class="section-stack">
        <div class="summary-grid">
          <article class="summary-card">
            <span>订单总数</span>
            <strong>{{ orders.length }}</strong>
            <em>已支付 {{ paidOrderCount }}</em>
          </article>
          <article class="summary-card">
            <span>在途任务</span>
            <strong>{{ tasks.filter((item) => !['completed', 'failed'].includes(item.status)).length }}</strong>
            <em>处理中与排队任务</em>
          </article>
          <article class="summary-card">
            <span>待支付单</span>
            <strong>{{ pendingOrderCount }}</strong>
            <em>支持手动标记与补录</em>
          </article>
          <article class="summary-card emphasis">
            <span>异常任务</span>
            <strong>{{ failedTaskCount }}</strong>
            <em>优先人工复核</em>
          </article>
        </div>

        <div class="admin-console-grid">
          <aside class="side-stack">
            <article class="plain-panel">
              <div class="detail-section__head">
                <div>
                  <h3>后台登录</h3>
                  <p>登录后可刷新订单、任务和日志数据。</p>
                </div>
                <el-tag>{{ token ? "已鉴权" : "未登录" }}</el-tag>
              </div>

              <el-form label-position="top" class="admin-login-panel">
                <el-form-item label="账号">
                  <el-input v-model="loginForm.username" />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input v-model="loginForm.password" type="password" show-password />
                </el-form-item>
              </el-form>

              <div class="info-list" v-if="token">
                <div><span>当前会话</span><strong>管理员</strong></div>
                <div><span>数据状态</span><strong>{{ loading ? "刷新中" : "可操作" }}</strong></div>
              </div>

              <div class="button-row">
                <el-button v-if="token" @click="handleLogout">退出</el-button>
                <el-button v-if="token" type="primary" :loading="loading" @click="loadAdminData">刷新</el-button>
                <el-button v-else type="primary" :loading="loggingIn" @click="handleLogin">登录</el-button>
              </div>
            </article>

            <article class="plain-panel">
              <div class="detail-section__head">
                <div>
                  <h3>筛选条件</h3>
                  <p>用于定位订单、状态与人工处理范围。</p>
                </div>
              </div>

              <el-form label-position="top">
                <el-form-item label="订单状态">
                  <el-select v-model="filters.orderStatus" placeholder="全部状态">
                    <el-option label="全部状态" value="" />
                    <el-option label="待支付" value="pending" />
                    <el-option label="已支付" value="paid" />
                    <el-option label="待退款" value="refund" />
                  </el-select>
                </el-form-item>
                <el-form-item label="任务状态">
                  <el-select v-model="filters.taskStatus" placeholder="全部任务">
                    <el-option label="全部任务" value="" />
                    <el-option label="处理中" value="processing" />
                    <el-option label="失败" value="failed" />
                    <el-option label="已完成" value="completed" />
                  </el-select>
                </el-form-item>
                <el-form-item label="检索词">
                  <el-input v-model="filters.keyword" placeholder="任务号 / 订单号 / 联系方式" />
                </el-form-item>
              </el-form>

              <div class="info-list">
                <div><span>筛选结果</span><strong>{{ filteredOrders.length }} / {{ orders.length }}</strong></div>
                <div><span>任务匹配</span><strong>{{ filteredTasks.length }} / {{ tasks.length }}</strong></div>
              </div>

              <div class="button-row">
                <el-button @click="resetFilters">重置</el-button>
                <el-button type="primary" plain @click="handleApplyFilters">应用</el-button>
              </div>
            </article>
          </aside>

          <section class="section-stack">
            <article class="plain-panel plain-panel--embedded">
              <div class="detail-section__head">
                <div>
                  <h3>订单列表</h3>
                  <p>选中后会同步驱动右侧当前订单、关联任务和动作区。</p>
                </div>
                <div class="button-row">
                  <el-tag type="info">已选 {{ selectedOrder ? 1 : 0 }} 条</el-tag>
                </div>
              </div>
              <el-table
                :data="filteredOrders"
                border
                highlight-current-row
                row-key="order_no"
                empty-text="暂无订单"
                @row-click="selectOrder"
              >
                <el-table-column prop="order_no" label="订单号" min-width="170" />
                <el-table-column prop="task_no" label="任务号" min-width="170" />
                <el-table-column label="金额" width="100">
                  <template #default="{ row }">{{ formatMoney(row.amount_cents) }}</template>
                </el-table-column>
                <el-table-column prop="contact" label="联系方式" min-width="160" />
                <el-table-column label="状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'paid' ? 'success' : 'warning'">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" min-width="180" />
              </el-table>
            </article>
          </section>

          <aside class="side-stack">
            <article class="plain-panel">
              <span class="section-eyebrow">当前订单</span>
              <el-empty v-if="!selectedOrder" description="请先选择订单" />
              <div v-else class="info-list">
                <div><span>订单号</span><strong>{{ selectedOrder.order_no }}</strong></div>
                <div><span>任务号</span><strong>{{ selectedOrder.task_no }}</strong></div>
                <div><span>金额</span><strong>{{ formatMoney(selectedOrder.amount_cents) }}</strong></div>
                <div><span>联系方式</span><strong>{{ selectedOrder.contact }}</strong></div>
                <div><span>支付时间</span><strong>{{ selectedOrder.paid_at || "待补录" }}</strong></div>
              </div>
            </article>

            <article class="plain-panel">
              <span class="section-eyebrow">关联任务</span>
              <el-empty v-if="!selectedTask" description="请先选择任务" />
              <div v-else class="info-list">
                <div><span>任务号</span><strong>{{ selectedTask.task_no }}</strong></div>
                <div><span>模式</span><strong>{{ selectedTask.mode }}</strong></div>
                <div><span>状态</span><strong>{{ selectedTask.status }}</strong></div>
                <div><span>进度</span><strong>{{ selectedTask.progress }}%</strong></div>
                <div><span>错误</span><strong>{{ selectedTask.error_message || "-" }}</strong></div>
              </div>
            </article>

            <article class="plain-panel">
              <span class="section-eyebrow">动作面板</span>
              <div class="admin-actions">
                <el-button
                  type="primary"
                  :disabled="!selectedOrder || selectedOrder.status === 'paid'"
                  @click="handleMarkPaid"
                >
                  标记支付
                </el-button>
                <el-button :disabled="!selectedTask" @click="handleRetry">重试任务</el-button>
                <el-button :disabled="!selectedTask" @click="handleExtend">延长保留</el-button>
                <el-button type="danger" :disabled="!selectedTask" @click="handleDeleteData">删除数据</el-button>
              </div>
              <p>危险操作会二次确认，并保留操作人、时间与对象记录。</p>
            </article>
          </aside>
        </div>

        <div class="admin-bottom-grid">
          <article class="plain-panel plain-panel--embedded">
            <div class="detail-section__head">
              <div>
                <h3>任务列表</h3>
                <p>用于复核模式、进度、解锁与过期信息。</p>
              </div>
            </div>
            <el-table
              :data="filteredTasks"
              border
              highlight-current-row
              row-key="task_no"
              empty-text="暂无任务"
              @row-click="selectTask"
            >
              <el-table-column prop="task_no" label="任务号" min-width="170" />
              <el-table-column prop="mode" label="模式" width="110" />
              <el-table-column prop="status" label="状态" width="120" />
              <el-table-column prop="unlock_status" label="解锁" width="100" />
              <el-table-column prop="progress" label="进度" width="90">
                <template #default="{ row }">{{ row.progress }}%</template>
              </el-table-column>
              <el-table-column prop="expires_at" label="过期时间" min-width="170" />
              <el-table-column prop="error_message" label="错误说明" min-width="180" />
            </el-table>
          </article>

          <article class="plain-panel plain-panel--embedded">
            <div class="detail-section__head">
              <div>
                <h3>操作日志</h3>
                <p>日志表保留对象、动作与时间，便于审计追踪。</p>
              </div>
            </div>
            <el-table :data="logs" border empty-text="暂无日志">
              <el-table-column prop="created_at" label="时间" min-width="180" />
              <el-table-column prop="admin_username" label="操作人" width="110" />
              <el-table-column prop="action" label="动作" width="120" />
              <el-table-column prop="target_type" label="目标类型" width="100" />
              <el-table-column prop="target_id" label="目标 ID" min-width="150" />
            </el-table>
          </article>
        </div>
      </section>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  adminLogin,
  deleteTaskData,
  extendTask,
  getAdminLogs,
  getAdminOrders,
  getAdminTasks,
  markOrderPaid,
  retryTask,
  type AdminLogRow,
  type AdminOrderRow,
  type AdminTaskRow
} from "@/services/api";

const token = ref(localStorage.getItem("bscc.adminToken") ?? "");
const loggingIn = ref(false);
const loading = ref(false);
const orders = ref<AdminOrderRow[]>([]);
const tasks = ref<AdminTaskRow[]>([]);
const logs = ref<AdminLogRow[]>([]);
const selectedOrderNo = ref("");
const selectedTaskNo = ref("");
const loginForm = reactive({ username: "admin", password: "admin123" });
const filters = reactive({
  orderStatus: "",
  taskStatus: "",
  keyword: ""
});

const filteredOrders = computed(() => orders.value.filter((item) => {
  const keyword = filters.keyword.trim().toLowerCase();
  const matchKeyword = !keyword
    || item.order_no.toLowerCase().includes(keyword)
    || item.task_no.toLowerCase().includes(keyword)
    || item.contact.toLowerCase().includes(keyword);
  const matchStatus = !filters.orderStatus
    || (filters.orderStatus === "pending" && item.status !== "paid")
    || item.status === filters.orderStatus;
  return matchKeyword && matchStatus;
}));
const filteredTasks = computed(() => tasks.value.filter((item) => {
  const keyword = filters.keyword.trim().toLowerCase();
  const matchKeyword = !keyword || item.task_no.toLowerCase().includes(keyword);
  const matchStatus = !filters.taskStatus || item.status === filters.taskStatus;
  return matchKeyword && matchStatus;
}));
const selectedOrder = computed(() => filteredOrders.value.find((item) => item.order_no === selectedOrderNo.value)
  ?? orders.value.find((item) => item.order_no === selectedOrderNo.value)
  ?? null);
const selectedTask = computed(() => filteredTasks.value.find((item) => item.task_no === selectedTaskNo.value)
  ?? tasks.value.find((item) => item.task_no === selectedTaskNo.value)
  ?? null);
const paidOrderCount = computed(() => orders.value.filter((item) => item.status === "paid").length);
const pendingOrderCount = computed(() => orders.value.filter((item) => item.status !== "paid").length);
const failedTaskCount = computed(() => tasks.value.filter((item) => item.status === "failed").length);

function selectOrder(row: AdminOrderRow) {
  selectedOrderNo.value = row.order_no;
  if (tasks.value.some((item) => item.task_no === row.task_no)) {
    selectedTaskNo.value = row.task_no;
  }
}

function selectTask(row: AdminTaskRow) {
  selectedTaskNo.value = row.task_no;
  const linkedOrder = orders.value.find((item) => item.task_no === row.task_no);
  if (linkedOrder) {
    selectedOrderNo.value = linkedOrder.order_no;
  }
}

function resetFilters() {
  filters.orderStatus = "";
  filters.taskStatus = "";
  filters.keyword = "";
}

function handleApplyFilters() {
  if (!selectedOrder.value && filteredOrders.value[0]) {
    selectedOrderNo.value = filteredOrders.value[0].order_no;
  }
  if (!selectedTask.value && filteredTasks.value[0]) {
    selectedTaskNo.value = filteredTasks.value[0].task_no;
  }
}

async function handleLogin() {
  loggingIn.value = true;
  try {
    const data = await adminLogin(loginForm.username, loginForm.password);
    token.value = data.token;
    localStorage.setItem("bscc.adminToken", data.token);
    ElMessage.success(`欢迎回来，${data.display_name}`);
    await loadAdminData();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "登录失败");
  } finally {
    loggingIn.value = false;
  }
}

function handleLogout() {
  token.value = "";
  localStorage.removeItem("bscc.adminToken");
  orders.value = [];
  tasks.value = [];
  logs.value = [];
  selectedOrderNo.value = "";
  selectedTaskNo.value = "";
}

async function loadAdminData() {
  if (!token.value) return;

  loading.value = true;
  try {
    const [orderData, taskData, logData] = await Promise.all([
      getAdminOrders(token.value),
      getAdminTasks(token.value),
      getAdminLogs(token.value)
    ]);
    orders.value = orderData.items;
    tasks.value = taskData.items;
    logs.value = logData.items;

    if (!selectedOrderNo.value && orders.value[0]) {
      selectedOrderNo.value = orders.value[0].order_no;
    }
    if (!selectedTaskNo.value && tasks.value[0]) {
      selectedTaskNo.value = tasks.value[0].task_no;
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "后台数据加载失败");
  } finally {
    loading.value = false;
  }
}

async function handleMarkPaid() {
  if (!selectedOrder.value || !token.value) return;

  try {
    await markOrderPaid(token.value, selectedOrder.value.order_no);
    ElMessage.success("订单已标记为已支付");
    await loadAdminData();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "标记失败");
  }
}

async function handleRetry() {
  if (!selectedTask.value || !token.value) return;

  try {
    await ElMessageBox.confirm("确认将该任务重新加入查重流程？原结果将按后端逻辑重置。", "重新查重", { type: "warning" });
    await retryTask(token.value, selectedTask.value.task_no);
    ElMessage.success("任务已重新加入查重流程");
    await loadAdminData();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error instanceof Error ? error.message : "操作失败");
    }
  }
}

async function handleExtend() {
  if (!selectedTask.value || !token.value) return;

  try {
    await extendTask(token.value, selectedTask.value.task_no);
    ElMessage.success("任务结果保留时间已延长");
    await loadAdminData();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "操作失败");
  }
}

async function handleDeleteData() {
  if (!selectedTask.value || !token.value) return;

  try {
    await ElMessageBox.confirm("确定删除该任务的文件与比对数据？订单记录仍会保留。", "危险操作", { type: "error" });
    await deleteTaskData(token.value, selectedTask.value.task_no);
    ElMessage.success("任务数据已删除");
    await loadAdminData();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error instanceof Error ? error.message : "操作失败");
    }
  }
}

function formatMoney(cents: number) {
  return `¥${(cents / 100).toFixed(2)}`;
}

onMounted(async () => {
  await loadAdminData();
});
</script>
