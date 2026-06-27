<template>
  <div class="admin-dashboard-container">
    <header class="admin-header">
      <div class="admin-header-content">
        <div class="header-left">
          <h1>BSCC 运营后台</h1>
          <p>统一承接上传、进度、结果、对比、恢复与运营场景的审计型工作台</p>
        </div>
        <div class="header-right">
          <div class="admin-user-info">
            <span class="admin-name">管理员：{{ currentAdmin }}</span>
            <el-button link type="primary" @click="handleLogout">退出登录</el-button>
          </div>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <el-row :gutter="24">
        <el-col :span="6">
          <!-- 筛选控制面板 -->
          <el-card shadow="never" class="admin-card filter-card">
            <template #header>
              <div class="card-header">
                <h3>筛选条件</h3>
                <p>左侧筛选用于定位订单、状态与人工处理范围</p>
              </div>
            </template>
            <el-form label-position="top">
              <el-form-item label="订单状态">
                <el-select v-model="filters.orderStatus" placeholder="全部状态">
                  <el-option label="全部状态" value="" />
                  <el-option label="待支付" value="pending" />
                  <el-option label="已支付" value="paid" />
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
                <el-input v-model="filters.keyword" placeholder="订单号/任务号" />
              </el-form-item>
              <div class="filter-actions">
                <el-button @click="resetFilters">重置</el-button>
                <el-button type="primary" @click="applyFilters">应用</el-button>
              </div>
            </el-form>
          </el-card>

          <!-- 动作面板 -->
          <el-card shadow="never" class="admin-card action-card">
            <template #header>
              <div class="card-header">
                <h3>动作面板</h3>
                <p>所有操作都绑定当前对象，并写入下方日志表</p>
              </div>
            </template>
            <div class="action-buttons">
              <el-button type="primary" class="w-full" :disabled="!selectedOrder || selectedOrder.status === 'paid'" @click="handleMarkPaid" :loading="actionLoading.markPaid">标记支付</el-button>
              <el-button class="w-full" :disabled="!selectedTask" @click="handleRetryTask" :loading="actionLoading.retryTask">重试任务</el-button>
              <el-button class="w-full" :disabled="!selectedTask" @click="handleExtendTask" :loading="actionLoading.extendTask">延长保留</el-button>
              <el-button type="danger" plain class="w-full" :disabled="!selectedTask" @click="handleDeleteTask" :loading="actionLoading.deleteTask">删除数据</el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :span="18">
          <!-- 数据表格区域 -->
          <el-card shadow="never" class="admin-card table-card">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="订单列表" name="orders">
                <el-table 
                  :data="filteredOrders" 
                  border 
                  style="width: 100%"
                  highlight-current-row
                  @current-change="handleOrderSelect"
                  v-loading="loadingOrders"
                >
                  <el-table-column prop="order_no" label="订单号" width="180" />
                  <el-table-column prop="task_no" label="任务号" width="180" />
                  <el-table-column prop="amount_cents" label="金额" width="100">
                    <template #default="{ row }">
                      ¥{{ (row.amount_cents / 100).toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'paid' ? 'success' : 'warning'">
                        {{ row.status === 'paid' ? '已支付' : '待支付' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="created_at" label="创建时间" />
                </el-table>
              </el-tab-pane>

              <el-tab-pane label="任务列表" name="tasks">
                <el-table 
                  :data="filteredTasks" 
                  border 
                  style="width: 100%"
                  highlight-current-row
                  @current-change="handleTaskSelect"
                  v-loading="loadingTasks"
                >
                  <el-table-column prop="task_no" label="任务号" width="180" />
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'completed' ? 'success' : (row.status === 'failed' ? 'danger' : 'warning')">
                        {{ row.status === 'completed' ? '已完成' : (row.status === 'failed' ? '失败' : '处理中') }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="expires_at" label="过期时间" width="180" />
                  <el-table-column prop="error_message" label="错误说明" />
                  <el-table-column label="操作" width="120" fixed="right">
                    <template #default="{ row }">
                      <el-button 
                        v-if="row.status === 'completed'"
                        type="primary" 
                        link 
                        @click.stop="viewTaskResult(row.task_no)"
                      >
                        查看结果
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>

              <el-tab-pane label="操作日志" name="logs">
                <el-table :data="logsData" border style="width: 100%" v-loading="loadingLogs">
                  <el-table-column prop="created_at" label="时间" width="180" />
                  <el-table-column prop="admin_username" label="操作人" width="120" />
                  <el-table-column prop="action" label="动作" width="120" />
                  <el-table-column prop="target_type" label="目标类型" width="100" />
                  <el-table-column prop="target_id" label="目标 ID" />
                </el-table>
              </el-tab-pane>

              <el-tab-pane label="系统配置" name="settings">
                <div v-loading="loadingSettings" class="settings-container">
                  <el-form :model="settingsForm" label-width="140px" class="settings-form">
                    <el-divider content-position="left">运营与客服信息</el-divider>
                    <el-form-item label="客服微信号">
                      <el-input v-model="settingsForm.support_wechat" placeholder="如：BSCC_Support" />
                    </el-form-item>
                    <el-form-item label="系统公告">
                      <el-input v-model="settingsForm.system_notice" placeholder="为空则不显示横幅公告" />
                    </el-form-item>
                    <el-form-item label="首页特点标签">
                      <el-select
                        v-model="settingsForm.home_tags"
                        multiple
                        filterable
                        allow-create
                        default-first-option
                        placeholder="输入标签并回车添加"
                      >
                      </el-select>
                      <div class="form-tip">显示在系统标题下方，按回车添加新的特点标签。</div>
                    </el-form-item>

                    <el-divider content-position="left">系统策略</el-divider>
                    <el-form-item label="结果保留期限(天)">
                      <el-input-number v-model="settingsForm.retention_days" :min="1" :max="365" />
                      <span class="form-inline-tip">过期后的解析文件和报告将被自动清理</span>
                    </el-form-item>

                    <el-divider content-position="left">查重算法与策略</el-divider>
                    <el-form-item label="高风险阈值(%)">
                      <el-slider v-model="settingsForm.high_risk_threshold" :min="0" :max="100" />
                      <div class="form-tip">相似度大于等于此值，显示为红色（严重风险）</div>
                    </el-form-item>
                    <el-form-item label="中风险阈值(%)">
                      <el-slider v-model="settingsForm.warning_threshold" :min="0" :max="100" />
                      <div class="form-tip">相似度大于等于此值，显示为橙色（中等风险）</div>
                    </el-form-item>

                    <el-form-item>
                      <el-button type="primary" @click="saveSettings" :loading="savingSettings">保存配置</el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  getAdminOrders, 
  getAdminTasks, 
  getAdminLogs, 
  markOrderPaid, 
  retryTask, 
  extendTask, 
  deleteTaskData,
  getSystemSettings,
  updateSystemSettings
} from '@/services/api';

const router = useRouter();
const currentAdmin = ref(localStorage.getItem('admin_username') || '未知管理员');
const activeTab = ref('orders');

const filters = reactive({
  orderStatus: '',
  taskStatus: '',
  keyword: ''
});

// 数据状态
const ordersData = ref<any[]>([]);
const tasksData = ref<any[]>([]);
const logsData = ref<any[]>([]);

// 加载状态
const loadingOrders = ref(false);
const loadingTasks = ref(false);
const loadingLogs = ref(false);
const loadingSettings = ref(false);
const savingSettings = ref(false);
const actionLoading = reactive({
  markPaid: false,
  retryTask: false,
  extendTask: false,
  deleteTask: false
});

// 系统配置表单
const settingsForm = reactive({
  support_wechat: '',
  system_notice: '',
  home_tags: ['无需登陆', '基础免费', '不限页数', '不限大小', '开箱即用'],
  retention_days: 7,
  high_risk_threshold: 70,
  warning_threshold: 40
});

// 选中状态
const selectedOrder = ref<any>(null);
const selectedTask = ref<any>(null);

// 过滤后的数据
const filteredOrders = computed(() => {
  return ordersData.value.filter(order => {
    const matchStatus = !filters.orderStatus || order.status === filters.orderStatus;
    const matchKeyword = !filters.keyword || 
      order.order_no.includes(filters.keyword) || 
      order.task_no.includes(filters.keyword);
    return matchStatus && matchKeyword;
  });
});

const filteredTasks = computed(() => {
  return tasksData.value.filter(task => {
    const matchStatus = !filters.taskStatus || task.status === filters.taskStatus;
    const matchKeyword = !filters.keyword || task.task_no.includes(filters.keyword);
    return matchStatus && matchKeyword;
  });
});

const viewTaskResult = (taskNo: string) => {
  const url = router.resolve({ path: '/results', query: { task: taskNo } }).href;
  window.open(url, '_blank');
};

// 获取数据方法
const fetchOrders = async () => {
  loadingOrders.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getAdminOrders(token);
    ordersData.value = res.items || [];
  } catch (error) {
    ElMessage.error('获取订单列表失败');
  } finally {
    loadingOrders.value = false;
  }
};

const fetchTasks = async () => {
  loadingTasks.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getAdminTasks(token);
    tasksData.value = res.items || [];
  } catch (error) {
    ElMessage.error('获取任务列表失败');
  } finally {
    loadingTasks.value = false;
  }
};

const fetchLogs = async () => {
  loadingLogs.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getAdminLogs(token);
    logsData.value = res.items || [];
  } catch (error) {
    ElMessage.error('获取操作日志失败');
  } finally {
    loadingLogs.value = false;
  }
};

const fetchSettings = async () => {
  loadingSettings.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getSystemSettings(token);
    if (res) {
      Object.assign(settingsForm, res);
    }
  } catch (error) {
    // ElMessage.error('获取系统配置失败');
  } finally {
    loadingSettings.value = false;
  }
};

const saveSettings = async () => {
  savingSettings.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    await updateSystemSettings(token, settingsForm);
    ElMessage.success('系统配置已保存');
    // 可选：触发一个自定义事件或者重新获取前台配置，让前台生效
  } catch (error) {
    ElMessage.error('保存系统配置失败');
  } finally {
    savingSettings.value = false;
  }
};

const refreshAll = () => {
  fetchOrders();
  fetchTasks();
  fetchLogs();
  fetchSettings();
};

// 行选择处理
const handleOrderSelect = (row: any) => {
  selectedOrder.value = row;
  if (row) {
    // 联动选中对应的任务
    const task = tasksData.value.find(t => t.task_no === row.task_no);
    if (task) selectedTask.value = task;
  }
};

const handleTaskSelect = (row: any) => {
  selectedTask.value = row;
  if (row) {
    // 联动选中对应的订单
    const order = ordersData.value.find(o => o.task_no === row.task_no);
    if (order) selectedOrder.value = order;
  }
};

// 动作处理
const handleMarkPaid = async () => {
  if (!selectedOrder.value) return;
  try {
    await ElMessageBox.confirm(`确认将订单 ${selectedOrder.value.order_no} 标记为已支付？`, '提示', { type: 'warning' });
    actionLoading.markPaid = true;
    const token = localStorage.getItem('admin_token') || '';
    await markOrderPaid(token, selectedOrder.value.order_no);
    ElMessage.success('标记支付成功');
    refreshAll();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('标记支付失败');
  } finally {
    actionLoading.markPaid = false;
  }
};

const handleRetryTask = async () => {
  if (!selectedTask.value) return;
  try {
    await ElMessageBox.confirm(`确认重试任务 ${selectedTask.value.task_no}？`, '提示', { type: 'warning' });
    actionLoading.retryTask = true;
    const token = localStorage.getItem('admin_token') || '';
    await retryTask(token, selectedTask.value.task_no);
    ElMessage.success('任务已提交重试');
    refreshAll();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('重试任务失败');
  } finally {
    actionLoading.retryTask = false;
  }
};

const handleExtendTask = async () => {
  if (!selectedTask.value) return;
  try {
    await ElMessageBox.confirm(`确认延长任务 ${selectedTask.value.task_no} 的保留时间（+7天）？`, '提示', { type: 'warning' });
    actionLoading.extendTask = true;
    const token = localStorage.getItem('admin_token') || '';
    await extendTask(token, selectedTask.value.task_no);
    ElMessage.success('延长保留成功');
    refreshAll();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('延长保留失败');
  } finally {
    actionLoading.extendTask = false;
  }
};

const handleDeleteTask = async () => {
  if (!selectedTask.value) return;
  try {
    await ElMessageBox.confirm(`确认删除任务 ${selectedTask.value.task_no} 的数据？删除后无法恢复！`, '危险操作', { type: 'error' });
    actionLoading.deleteTask = true;
    const token = localStorage.getItem('admin_token') || '';
    await deleteTaskData(token, selectedTask.value.task_no);
    ElMessage.success('数据删除成功');
    refreshAll();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('数据删除失败');
  } finally {
    actionLoading.deleteTask = false;
  }
};

const handleLogout = () => {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_username');
  ElMessage.success('已退出登录');
  router.push('/admin/login');
};

const resetFilters = () => {
  filters.orderStatus = '';
  filters.taskStatus = '';
  filters.keyword = '';
};

const applyFilters = () => {
  ElMessage.success('筛选已应用');
};

onMounted(() => {
  // 检查是否已登录
  const token = localStorage.getItem('admin_token');
  if (!token) {
    ElMessage.warning('请先登录后台');
    router.push('/admin/login');
  } else {
    refreshAll();
  }
});
</script>

<style scoped>
.admin-dashboard-container {
  min-height: 100vh;
  background-color: var(--background);
}

.admin-header {
  background-color: var(--surface);
  border-bottom: 1px solid var(--line);
  padding: 24px 0;
  margin-bottom: 24px;
}

.admin-header-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--ink);
}

.header-left p {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.admin-user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--panel);
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--line);
}

.admin-name {
  font-size: 14px;
  color: var(--ink);
  font-weight: 500;
}

.admin-main {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px 40px;
}

.admin-card {
  margin-bottom: 24px;
  border-radius: 8px;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.card-header h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: var(--ink);
}

.card-header p {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}

.filter-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 24px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.w-full {
  width: 100%;
  margin-left: 0 !important;
}

:deep(.el-tabs__nav-wrap) {
  padding: 0 20px;
}

:deep(.el-tabs__content) {
  padding: 20px;
}

.settings-container {
  max-width: 800px;
}

.settings-form .el-divider {
  margin: 32px 0 24px;
}

.settings-form .el-divider:first-child {
  margin-top: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.4;
  margin-top: 4px;
  width: 100%;
}

.form-inline-tip {
  font-size: 12px;
  color: var(--muted);
  margin-left: 12px;
}
</style>