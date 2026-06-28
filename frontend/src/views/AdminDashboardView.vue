<template>
  <div class="admin-dashboard-container">
    <header class="admin-header">
      <div class="admin-header-content">
        <div class="header-left">
          <h1 class="admin-site-title" @click="router.push('/')">{{ adminPanelTitle }}</h1>
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
          <template v-if="isHomeTab">
            <el-card shadow="never" class="admin-card home-side-card">
              <template #header>
                <div class="card-header">
                  <h3>管理首页</h3>
                  <p>先看概况，再进入具体列表与配置。</p>
                </div>
              </template>
              <div class="home-side-actions">
                <el-button type="primary" class="w-full" @click="activeTab = 'orders'">进入订单列表</el-button>
                <el-button class="w-full" @click="activeTab = 'tasks'">进入任务列表</el-button>
                <el-button class="w-full" @click="activeTab = 'logs'">查看操作日志</el-button>
                <el-button class="w-full" @click="activeTab = 'settings'">前往系统配置</el-button>
              </div>
            </el-card>

            <el-card shadow="never" class="admin-card home-side-card">
              <template #header>
                <div class="card-header">
                  <h3>支付状态</h3>
                  <p>快速确认支付通道是否可用于联调与收款。</p>
                </div>
              </template>
              <div class="home-channel-status">
                <div class="home-channel-item">
                  <div>
                    <strong>支付宝</strong>
                    <p>{{ overviewData?.payment.alipay_notify_url || '尚未生成默认回调地址' }}</p>
                  </div>
                  <el-tag :type="overviewData?.payment.alipay_enabled ? (overviewData?.payment.alipay_configured ? 'success' : 'warning') : 'info'">
                    {{ !overviewData?.payment.alipay_enabled ? '未启用' : (overviewData?.payment.alipay_configured ? '可用' : '待补齐') }}
                  </el-tag>
                </div>
                <div class="home-channel-item">
                  <div>
                    <strong>微信支付</strong>
                    <p>{{ overviewData?.payment.wechat_notify_url || '尚未生成默认回调地址' }}</p>
                  </div>
                  <el-tag :type="overviewData?.payment.wechat_enabled ? (overviewData?.payment.wechat_configured ? 'success' : 'warning') : 'info'">
                    {{ !overviewData?.payment.wechat_enabled ? '未启用' : (overviewData?.payment.wechat_configured ? '可用' : '待补齐') }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </template>

          <template v-else>
            <el-card v-if="showFilterPanel" shadow="never" class="admin-card filter-card">
              <template #header>
                <div class="card-header">
                  <h3>筛选条件</h3>
                  <p>{{ filterPanelDescription }}</p>
                </div>
              </template>
              <el-form label-position="top">
                <el-form-item v-if="showOrderFilters" label="订单状态">
                  <el-select v-model="filters.orderStatus" placeholder="全部状态">
                    <el-option label="全部状态" value="" />
                    <el-option label="待支付" value="pending" />
                    <el-option label="已支付" value="paid" />
                  </el-select>
                </el-form-item>
                <el-form-item v-if="showTaskFilters" label="任务状态">
                  <el-select v-model="filters.taskStatus" placeholder="全部任务">
                    <el-option label="全部任务" value="" />
                    <el-option label="处理中" value="processing" />
                    <el-option label="失败" value="failed" />
                    <el-option label="已完成" value="completed" />
                  </el-select>
                </el-form-item>
                <el-form-item v-if="showDateFilters" label="创建日期">
                  <el-date-picker
                    v-model="filters.createdDateRange"
                    type="daterange"
                    unlink-panels
                    clearable
                    value-format="YYYY-MM-DD"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                  />
                  <div class="form-tip">按创建日期筛选订单或任务，起止日期均包含当天。</div>
                </el-form-item>
                <el-form-item label="检索词">
                  <el-input
                    v-model="filters.keyword"
                    :placeholder="keywordPlaceholder"
                    clearable
                    @keyup.enter="applyFilters"
                  />
                </el-form-item>
                <div class="filter-actions">
                  <el-button @click="resetFilters">重置</el-button>
                  <el-button type="primary" @click="applyFilters">应用</el-button>
                </div>
              </el-form>
            </el-card>

            <el-card v-if="showActionPanel" shadow="never" class="admin-card action-card">
              <template #header>
                <div class="card-header">
                  <h3>动作面板</h3>
                  <p>所有操作都绑定当前对象，并写入下方日志表</p>
                </div>
              </template>
              <div class="action-buttons">
                <el-button type="primary" class="w-full" :disabled="!selectedOrder || selectedOrder.status === 'paid'" @click="handleMarkPaid" :loading="actionLoading.markPaid">标记支付</el-button>
                  <el-button class="w-full" :disabled="!selectedTask || selectedTaskIsDeleted" @click="handleRetryTask" :loading="actionLoading.retryTask">重试任务</el-button>
                  <el-button class="w-full" :disabled="!selectedTask || selectedTaskIsDeleted" @click="handleExtendTask" :loading="actionLoading.extendTask">延长保留</el-button>
                  <el-button type="danger" class="w-full" plain :disabled="!selectedTaskRows.length" @click="handleBatchDeleteTasks" :loading="actionLoading.batchDeleteTask">批量删除选中任务</el-button>
                  <el-button type="danger" plain class="w-full" :disabled="!selectedTask || selectedTaskIsDeleted" @click="handleDeleteTask" :loading="actionLoading.deleteTask">删除数据</el-button>
              </div>
            </el-card>

            <el-card v-if="activeTab === 'settings'" shadow="never" class="admin-card action-card">
              <template #header>
                <div class="card-header">
                  <h3>配置说明</h3>
                  <p>系统配置保存后会立即回读校验，确保标题、域名与支付配置真实落库。</p>
                </div>
              </template>
              <div class="action-buttons">
                <el-button type="primary" class="w-full" @click="fetchSettings" :loading="loadingSettings">重新拉取配置</el-button>
                <el-button class="w-full" @click="fetchOverview" :loading="loadingOverview">刷新首页概况</el-button>
              </div>
            </el-card>
          </template>
        </el-col>

        <el-col :span="18">
          <!-- 数据表格区域 -->
          <el-card shadow="never" class="admin-card table-card">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="首页" name="home">
                <div v-loading="loadingOverview" class="overview-container">
                  <section class="overview-hero">
                    <div>
                      <h2>运营总览</h2>
                      <p>聚合订单、任务、支付配置与最近操作，适合作为后台默认首页。</p>
                    </div>
                    <el-button @click="fetchOverview">刷新概况</el-button>
                  </section>

                  <section class="overview-stats">
                    <article class="overview-stat-card">
                      <span>订单总数</span>
                      <strong>{{ overviewData?.totals.orders ?? 0 }}</strong>
                      <p>待支付 {{ overviewData?.totals.orders_pending ?? 0 }} / 已支付 {{ overviewData?.totals.orders_paid ?? 0 }}</p>
                    </article>
                    <article class="overview-stat-card">
                      <span>已支付金额</span>
                      <strong>{{ formatAmount(overviewData?.revenue.paid_amount_cents ?? 0) }}</strong>
                      <p>待支付金额 {{ formatAmount(overviewData?.revenue.pending_amount_cents ?? 0) }}</p>
                    </article>
                    <article class="overview-stat-card">
                      <span>任务总数</span>
                      <strong>{{ overviewData?.totals.tasks ?? 0 }}</strong>
                      <p>处理中 {{ overviewData?.totals.tasks_processing ?? 0 }}</p>
                    </article>
                    <article class="overview-stat-card">
                      <span>已完成任务</span>
                      <strong>{{ overviewData?.totals.tasks_completed ?? 0 }}</strong>
                      <p>失败任务 {{ overviewData?.totals.tasks_failed ?? 0 }}</p>
                    </article>
                    <article class="overview-stat-card">
                      <span>首页运营配置</span>
                      <strong>{{ overviewData?.system.home_tags_count ?? 0 }}</strong>
                      <p>{{ overviewData?.system.system_notice_enabled ? '公告已开启' : '公告未开启' }}</p>
                    </article>
                    <article class="overview-stat-card">
                      <span>操作日志</span>
                      <strong>{{ overviewData?.totals.logs ?? 0 }}</strong>
                      <p>结果保留 {{ overviewData?.system.result_retention_days ?? 0 }} 天</p>
                    </article>
                  </section>

                  <section class="overview-panels">
                    <article class="overview-panel">
                      <div class="overview-panel__head">
                        <h3>站点与支付配置</h3>
                        <el-button link type="primary" @click="activeTab = 'settings'">去配置</el-button>
                      </div>
                      <div class="overview-kv-list">
                        <div class="overview-kv-item">
                          <span>网站域名</span>
                          <strong>{{ overviewData?.system.site_base_url || '未填写' }}</strong>
                        </div>
                        <div class="overview-kv-item">
                          <span>支付宝回调</span>
                          <strong>{{ overviewData?.payment.alipay_notify_url || '未生成' }}</strong>
                        </div>
                        <div class="overview-kv-item">
                          <span>微信回调</span>
                          <strong>{{ overviewData?.payment.wechat_notify_url || '未生成' }}</strong>
                        </div>
                      </div>
                    </article>

                    <article class="overview-panel">
                      <div class="overview-panel__head">
                        <h3>快捷入口</h3>
                        <el-button link type="primary" @click="refreshAll">刷新全部</el-button>
                      </div>
                      <div class="overview-shortcuts">
                        <button type="button" class="overview-shortcut" @click="activeTab = 'orders'">
                          <strong>订单管理</strong>
                          <span>处理待支付、人工补单与联系方式核对</span>
                        </button>
                        <button type="button" class="overview-shortcut" @click="activeTab = 'tasks'">
                          <strong>任务管理</strong>
                          <span>查看处理进度、失败原因与结果跳转</span>
                        </button>
                        <button type="button" class="overview-shortcut" @click="activeTab = 'logs'">
                          <strong>操作审计</strong>
                          <span>追踪配置变更、人工操作与后台行为</span>
                        </button>
                      </div>
                    </article>
                  </section>

                  <section class="overview-tables">
                    <article class="overview-panel">
                      <div class="overview-panel__head">
                        <h3>最近订单</h3>
                        <el-button link type="primary" @click="activeTab = 'orders'">查看全部</el-button>
                      </div>
                      <el-table :data="overviewData?.recent_orders || []" border>
                        <el-table-column prop="order_no" label="订单号" min-width="170" />
                        <el-table-column prop="task_no" label="任务号" min-width="170" />
                        <el-table-column prop="amount_cents" label="金额" width="110">
                          <template #default="{ row }">
                            {{ formatAmount(row.amount_cents) }}
                          </template>
                        </el-table-column>
                        <el-table-column prop="status" label="状态" width="100">
                          <template #default="{ row }">
                            <el-tag :type="row.status === 'paid' ? 'success' : 'warning'">
                              {{ row.status === 'paid' ? '已支付' : '待支付' }}
                            </el-tag>
                          </template>
                        </el-table-column>
                      </el-table>
                    </article>

                    <article class="overview-panel">
                      <div class="overview-panel__head">
                        <h3>最近任务</h3>
                        <el-button link type="primary" @click="activeTab = 'tasks'">查看全部</el-button>
                      </div>
                      <el-table :data="overviewData?.recent_tasks || []" border>
                        <el-table-column prop="task_no" label="任务号" min-width="170" />
                        <el-table-column prop="status" label="状态" width="100">
                          <template #default="{ row }">
                            <el-tag :type="getTaskStatusTagType(row.status)">
                              {{ getTaskStatusLabel(row.status) }}
                            </el-tag>
                          </template>
                        </el-table-column>
                        <el-table-column prop="progress" label="进度" width="90" />
                        <el-table-column label="操作" width="120">
                          <template #default="{ row }">
                            <el-button v-if="row.status === 'completed'" type="primary" link @click="viewTaskResult(row.task_no)">
                              查看结果
                            </el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                    </article>
                  </section>

                  <section class="overview-panel">
                    <div class="overview-panel__head">
                      <h3>最近操作</h3>
                      <el-button link type="primary" @click="activeTab = 'logs'">查看全部</el-button>
                    </div>
                    <div v-if="overviewData?.recent_logs.length" class="overview-log-list">
                      <div v-for="log in overviewData?.recent_logs" :key="log.id" class="overview-log-item">
                        <strong>{{ log.action }}</strong>
                        <span>{{ log.admin_username || '系统' }} · {{ log.target_type }} · {{ log.target_id }}</span>
                        <time>{{ log.created_at }}</time>
                      </div>
                    </div>
                    <el-empty v-else description="暂无操作记录" />
                  </section>
                </div>
              </el-tab-pane>

              <el-tab-pane label="订单列表" name="orders">
                <el-table 
                  :data="ordersData" 
                  border 
                  style="width: 100%"
                  highlight-current-row
                  @current-change="handleOrderSelect"
                  v-loading="loadingOrders"
                >
                  <el-table-column prop="order_no" label="订单号" width="180" />
                  <el-table-column prop="task_no" label="任务号" width="180" />
                  <el-table-column
                    prop="contact"
                    label="联系方式"
                    min-width="180"
                    show-overflow-tooltip
                  />
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
                <div class="table-pagination">
                  <el-pagination
                    v-model:current-page="orderPagination.page"
                    v-model:page-size="orderPagination.pageSize"
                    background
                    layout="total, sizes, prev, pager, next"
                    :total="orderPagination.total"
                    :page-sizes="[10, 20, 50]"
                    @current-change="handleOrderPageChange"
                    @size-change="handleOrderSizeChange"
                  />
                </div>
              </el-tab-pane>

              <el-tab-pane label="任务列表" name="tasks">
                <div class="task-table-toolbar">
                  <div class="task-table-toolbar__meta">
                    <strong>已选 {{ selectedTaskRows.length }} 项</strong>
                    <span>支持批量删除选中任务，并同步走后台删除流程。</span>
                  </div>
                  <el-button
                    type="danger"
                    plain
                    :disabled="!selectedTaskRows.length"
                    :loading="actionLoading.batchDeleteTask"
                    @click="handleBatchDeleteTasks"
                  >
                    批量删除
                  </el-button>
                </div>
                <el-table 
                  :data="tasksData" 
                  border 
                  style="width: 100%"
                  highlight-current-row
                  @current-change="handleTaskSelect"
                  @selection-change="handleTaskSelectionChange"
                  v-loading="loadingTasks"
                >
                  <el-table-column type="selection" width="48" />
                  <el-table-column prop="task_no" label="任务号" width="180" />
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                      <el-tag :type="getTaskStatusTagType(row.status)">
                        {{ getTaskStatusLabel(row.status) }}
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
                <div class="table-pagination">
                  <el-pagination
                    v-model:current-page="taskPagination.page"
                    v-model:page-size="taskPagination.pageSize"
                    background
                    layout="total, sizes, prev, pager, next"
                    :total="taskPagination.total"
                    :page-sizes="[10, 20, 50]"
                    @current-change="handleTaskPageChange"
                    @size-change="handleTaskSizeChange"
                  />
                </div>
              </el-tab-pane>

              <el-tab-pane label="操作日志" name="logs">
                <el-table :data="logsData" border style="width: 100%" v-loading="loadingLogs">
                  <el-table-column prop="created_at" label="时间" width="180" />
                  <el-table-column prop="admin_username" label="操作人" width="120" />
                  <el-table-column prop="action" label="动作" width="120" />
                  <el-table-column prop="target_type" label="目标类型" width="100" />
                  <el-table-column prop="target_id" label="目标 ID" show-overflow-tooltip />
                </el-table>
                <div class="table-pagination">
                  <el-pagination
                    v-model:current-page="logPagination.page"
                    v-model:page-size="logPagination.pageSize"
                    background
                    layout="total, sizes, prev, pager, next"
                    :total="logPagination.total"
                    :page-sizes="[10, 20, 50]"
                    @current-change="handleLogPageChange"
                    @size-change="handleLogSizeChange"
                  />
                </div>
              </el-tab-pane>

              <el-tab-pane label="系统配置" name="settings">
                <div v-loading="loadingSettings" class="settings-container">
                  <el-form :model="settingsForm" label-width="140px" class="settings-form">
                    <el-divider content-position="left">支付与价格</el-divider>
                    <el-form-item label="原价(分)">
                      <el-input-number v-model="settingsForm.price_per_b_file_cents" :min="1" :step="100" />
                      <span class="form-inline-tip">未开启促销时，实际下单金额 = 原价 x B 标书数量</span>
                    </el-form-item>
                    <el-form-item label="启用促销">
                      <el-switch v-model="settingsForm.promo_enabled" />
                      <span class="form-inline-tip">开启后结果页和支付弹窗会显示活动价与倒计时</span>
                    </el-form-item>
                    <el-form-item label="优惠价(分)">
                      <el-input-number v-model="settingsForm.promo_price_per_b_file_cents" :min="1" :step="100" />
                      <span class="form-inline-tip">活动期间的每份 B 标书优惠价，必须低于原价</span>
                    </el-form-item>
                    <el-form-item label="活动截止时间">
                      <el-date-picker
                        v-model="settingsForm.promo_ends_at"
                        type="datetime"
                        value-format="YYYY-MM-DDTHH:mm:ss"
                        placeholder="选择活动截止时间"
                      />
                      <div class="form-tip">倒计时由服务端截止时间驱动，留空则不限制活动结束时间。</div>
                    </el-form-item>
                    <el-form-item label="活动标签">
                      <el-input v-model="settingsForm.promo_badge" placeholder="如：限时特惠" />
                    </el-form-item>
                    <el-form-item label="活动说明">
                      <el-input v-model="settingsForm.promo_note" placeholder="如：限时活动，仅限当前批次查重任务" />
                    </el-form-item>
                    <el-form-item label="损失厌恶文案">
                      <el-input v-model="settingsForm.promo_loss_aversion_text" placeholder="如：错过后将恢复原价" />
                    </el-form-item>
                    <el-form-item label="展示倒计时">
                      <el-switch v-model="settingsForm.promo_countdown_enabled" />
                      <span class="form-inline-tip">开启后在结果页和支付弹窗显示活动倒计时</span>
                    </el-form-item>

                    <el-form-item label="结果预览条数">
                      <el-input-number v-model="settingsForm.preview_segment_limit" :min="1" :max="20" />
                      <span class="form-inline-tip">未支付时可查看的重复片段预览数量</span>
                    </el-form-item>

                    <el-divider content-position="left">运营与客服信息</el-divider>
                    <el-form-item label="主页标题">
                      <el-input v-model="settingsForm.site_title" placeholder="如：标书查重系统" />
                    </el-form-item>
                    <el-form-item label="客服微信号">
                      <el-input v-model="settingsForm.customer_service_wechat" placeholder="如：BSCC_Support" />
                    </el-form-item>
                    <el-form-item label="客服邮箱">
                      <el-input v-model="settingsForm.customer_service_email" placeholder="如：support@example.com" />
                    </el-form-item>
                    <el-form-item label="系统公告">
                      <el-input v-model="settingsForm.system_notice" placeholder="为空则不显示横幅公告" />
                    </el-form-item>
                    <el-form-item label="网站域名">
                      <el-input
                        v-model="settingsForm.site_base_url"
                        placeholder="如：https://your-domain.com"
                      />
                      <div class="form-tip">用于拼接支付宝与微信支付的默认异步回调地址，请填写公网可访问的域名或基准地址。</div>
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
                      <el-input-number v-model="settingsForm.result_retention_days" :min="1" :max="365" />
                      <span class="form-inline-tip">过期后的解析文件和报告将被自动清理</span>
                    </el-form-item>

                    <el-divider content-position="left">查重算法与策略</el-divider>
                    <el-form-item label="完全重复阈值(%)">
                      <el-slider v-model="exactThresholdPercent" :min="0" :max="100" />
                      <div class="form-tip">超过该阈值时，判定为完全重复。</div>
                    </el-form-item>
                    <el-form-item label="改写重复阈值(%)">
                      <el-slider v-model="rewriteThresholdPercent" :min="0" :max="100" />
                      <div class="form-tip">用于识别表达改写但语义高度接近的内容。</div>
                    </el-form-item>
                    <el-form-item label="语义重复阈值(%)">
                      <el-slider v-model="semanticThresholdPercent" :min="0" :max="100" />
                      <div class="form-tip">用于识别语义相近但表述不同的段落。</div>
                    </el-form-item>

                    <el-divider content-position="left">支付宝配置</el-divider>
                    <el-form-item label="启用支付宝支付">
                      <el-switch v-model="settingsForm.alipay_enabled" />
                      <span class="form-inline-tip">开启后前台可选择支付宝扫码支付</span>
                    </el-form-item>
                    <el-form-item label="支付宝网关">
                      <el-input
                        v-model="settingsForm.alipay_gateway"
                        placeholder="必填，如：https://openapi.alipay.com/gateway.do"
                      />
                      <div class="gateway-presets">
                        <el-button text @click="settingsForm.alipay_gateway = 'https://openapi-sandbox.dl.alipaydev.com/gateway.do'">
                          使用沙箱网关
                        </el-button>
                        <el-button text @click="settingsForm.alipay_gateway = 'https://openapi.alipay.com/gateway.do'">
                          使用正式网关
                        </el-button>
                      </div>
                      <div class="form-tip">必须显式填写支付宝网关，沙箱或正式环境均以这里的网关地址为准。</div>
                    </el-form-item>
                    <el-form-item label="应用 App ID">
                      <el-input v-model="settingsForm.alipay_app_id" placeholder="请输入支付宝应用 APP_ID" />
                    </el-form-item>
                    <el-form-item label="异步通知地址">
                      <el-input
                        v-model="settingsForm.alipay_notify_url"
                        placeholder="留空则自动使用下方默认地址"
                      />
                      <div class="form-tip">
                        默认地址：{{ defaultAlipayNotifyUrl || '请先填写上方“网站域名”以自动生成默认回调地址' }}
                      </div>
                    </el-form-item>
                    <el-form-item label="应用私钥">
                      <el-input
                        v-model="settingsForm.alipay_private_key"
                        type="textarea"
                        :rows="5"
                        placeholder="请输入 RSA2 应用私钥，支持直接粘贴多行文本"
                      />
                    </el-form-item>
                    <el-form-item label="支付宝公钥">
                      <el-input
                        v-model="settingsForm.alipay_public_key"
                        type="textarea"
                        :rows="5"
                        placeholder="请输入支付宝公钥，支持直接粘贴多行文本"
                      />
                    </el-form-item>

                    <el-divider content-position="left">微信 Native 支付配置</el-divider>
                    <el-form-item label="启用微信支付">
                      <el-switch v-model="settingsForm.wechat_enabled" />
                      <span class="form-inline-tip">开启后前台可选择微信 Native 扫码支付</span>
                    </el-form-item>
                    <el-form-item label="微信 AppID">
                      <el-input v-model="settingsForm.wechat_app_id" placeholder="请输入微信支付 AppID" />
                    </el-form-item>
                    <el-form-item label="微信商户号">
                      <el-input v-model="settingsForm.wechat_mch_id" placeholder="请输入微信支付商户号 MCH_ID" />
                    </el-form-item>
                    <el-form-item label="APIv2 Key">
                      <el-input
                        v-model="settingsForm.wechat_api_v2_key"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入微信支付 APIv2 Key"
                      />
                      <div class="form-tip">Native 下单、查单与回调验签均依赖该密钥，建议使用 HMAC-SHA256。</div>
                    </el-form-item>
                    <el-form-item label="异步通知地址">
                      <el-input
                        v-model="settingsForm.wechat_notify_url"
                        placeholder="留空则自动使用下方默认地址"
                      />
                      <div class="form-tip">
                        默认地址：{{ defaultWechatNotifyUrl || '请先填写上方“网站域名”以自动生成默认回调地址' }}
                      </div>
                    </el-form-item>

                    <el-form-item>
                      <el-button type="primary" @click="saveSettings" :loading="savingSettings">保存配置</el-button>
                    </el-form-item>
                  </el-form>

                  <el-form :model="passwordForm" label-width="140px" class="settings-form password-form">
                    <el-divider content-position="left">账号安全</el-divider>
                    <el-form-item label="当前密码">
                      <el-input
                        v-model="passwordForm.current_password"
                        type="password"
                        show-password
                        placeholder="请输入当前管理员密码"
                      />
                    </el-form-item>
                    <el-form-item label="新密码">
                      <el-input
                        v-model="passwordForm.new_password"
                        type="password"
                        show-password
                        placeholder="请输入至少 6 位新密码"
                      />
                    </el-form-item>
                    <el-form-item label="确认新密码">
                      <el-input
                        v-model="passwordForm.confirm_password"
                        type="password"
                        show-password
                        placeholder="请再次输入新密码"
                      />
                    </el-form-item>
                    <el-form-item>
                      <el-button type="danger" @click="handleChangePassword" :loading="changingPassword">
                        修改管理员密码
                      </el-button>
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
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  getAdminOverview,
  changeAdminPassword,
  getAdminOrders, 
  getAdminTasks, 
  getAdminLogs, 
  markOrderPaid, 
  retryTask, 
  extendTask, 
  deleteTaskData,
  batchDeleteTaskData,
  getSystemSettings,
  updateSystemSettings,
  type AdminOverview
} from '@/services/api';
import { applyRouteSeo } from '@/utils/seo';

const router = useRouter();
const currentAdmin = ref(localStorage.getItem('admin_username') || '未知管理员');
const activeTab = ref('home');

const filters = reactive({
  orderStatus: '',
  taskStatus: '',
  keyword: '',
  createdDateRange: [] as string[]
});

// 数据状态
const ordersData = ref<any[]>([]);
const tasksData = ref<any[]>([]);
const logsData = ref<any[]>([]);
const orderPagination = reactive({ page: 1, pageSize: 10, total: 0 });
const taskPagination = reactive({ page: 1, pageSize: 10, total: 0 });
const logPagination = reactive({ page: 1, pageSize: 10, total: 0 });

// 加载状态
const loadingOrders = ref(false);
const loadingTasks = ref(false);
const loadingLogs = ref(false);
const loadingOverview = ref(false);
const loadingSettings = ref(false);
const savingSettings = ref(false);
const changingPassword = ref(false);
const actionLoading = reactive({
  markPaid: false,
  retryTask: false,
  extendTask: false,
  deleteTask: false,
  batchDeleteTask: false
});

// 系统配置表单
const createDefaultSettingsForm = () => ({
  price_per_b_file_cents: 1000,
  promo_enabled: false,
  promo_price_per_b_file_cents: 100,
  promo_ends_at: '',
  promo_note: '限时活动，仅限当前批次查重任务',
  promo_badge: '限时特惠',
  promo_countdown_enabled: true,
  promo_loss_aversion_text: '错过后将恢复原价',
  preview_segment_limit: 3,
  customer_service_wechat: '',
  customer_service_email: '',
  system_notice: '',
  site_base_url: '',
  site_title: '标书查重系统',
  home_tags: ['无需登陆', '基础免费', '不限页数', '不限大小', '开箱即用'],
  result_retention_days: 7,
  threshold_exact: 1,
  threshold_rewrite: 0.82,
  threshold_semantic: 0.68,
  alipay_enabled: false,
  alipay_gateway: '',
  alipay_app_id: '',
  alipay_notify_url: '',
  alipay_private_key: '',
  alipay_public_key: '',
  wechat_enabled: false,
  wechat_app_id: '',
  wechat_mch_id: '',
  wechat_api_v2_key: '',
  wechat_notify_url: ''
});

const settingsForm = reactive(createDefaultSettingsForm());
const adminPanelTitle = computed(() => `${(settingsForm.site_title || '标书查重系统').trim()} 运营后台`);

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
});

// 选中状态
const selectedOrder = ref<any>(null);
const selectedTask = ref<any>(null);
const selectedTaskRows = ref<any[]>([]);
const overviewData = ref<AdminOverview | null>(null);
const isHomeTab = computed(() => activeTab.value === 'home');
const selectedTaskIsDeleted = computed(() => selectedTask.value?.status === 'deleted');
const showOrderFilters = computed(() => activeTab.value === 'orders');
const showTaskFilters = computed(() => activeTab.value === 'tasks');
const showDateFilters = computed(() => activeTab.value === 'orders' || activeTab.value === 'tasks');
const showFilterPanel = computed(() => activeTab.value === 'orders' || activeTab.value === 'tasks' || activeTab.value === 'logs');
const showActionPanel = computed(() => activeTab.value === 'orders' || activeTab.value === 'tasks');
const filterPanelDescription = computed(() => {
  if (activeTab.value === 'orders') return '按订单状态、创建日期与关键词定位目标订单';
  if (activeTab.value === 'tasks') return '按任务状态、创建日期与关键词定位目标任务';
  if (activeTab.value === 'logs') return '按关键词检索操作日志与人工处理记录';
  return '使用左侧条件快速定位需要处理的数据';
});

const exactThresholdPercent = computed({
  get: () => Math.round(Number(settingsForm.threshold_exact || 0) * 100),
  set: (value: number) => {
    settingsForm.threshold_exact = Number((value / 100).toFixed(2));
  }
});

const rewriteThresholdPercent = computed({
  get: () => Math.round(Number(settingsForm.threshold_rewrite || 0) * 100),
  set: (value: number) => {
    settingsForm.threshold_rewrite = Number((value / 100).toFixed(2));
  }
});

const semanticThresholdPercent = computed({
  get: () => Math.round(Number(settingsForm.threshold_semantic || 0) * 100),
  set: (value: number) => {
    settingsForm.threshold_semantic = Number((value / 100).toFixed(2));
  }
});

const normalizedSiteBaseUrl = computed(() => settingsForm.site_base_url.trim().replace(/\/+$/, ''));
const defaultAlipayNotifyUrl = computed(() => normalizedSiteBaseUrl.value ? `${normalizedSiteBaseUrl.value}/api/payments/alipay/notify` : '');
const defaultWechatNotifyUrl = computed(() => normalizedSiteBaseUrl.value ? `${normalizedSiteBaseUrl.value}/api/payments/wechat/notify` : '');

const handleAdminRequestError = (error: unknown, fallbackMessage: string) => {
  const message = error instanceof Error ? error.message : fallbackMessage;
  if (message === '后台未登录') {
    ElMessage.warning('后台登录已失效，请重新登录');
    handleLogout();
    return;
  }
  ElMessage.error(message || fallbackMessage);
};

const keywordPlaceholder = computed(() => {
  if (activeTab.value === 'orders') return '模糊搜索订单号 / 任务号 / 联系方式';
  if (activeTab.value === 'tasks') return '模糊搜索任务号 / 错误说明 / 模式';
  if (activeTab.value === 'logs') return '模糊搜索动作 / 目标类型 / 目标 ID / 操作人';
  return '输入关键词后回车搜索';
});

const viewTaskResult = (taskNo: string) => {
  const url = router.resolve({ path: '/results', query: { task: taskNo } }).href;
  window.open(url, '_blank');
};

const formatAmount = (amountCents: number) => `¥${(Number(amountCents || 0) / 100).toFixed(2)}`;
const getTaskStatusLabel = (status: string) => {
  if (status === 'completed') return '已完成';
  if (status === 'failed') return '失败';
  if (status === 'deleted') return '已删除';
  return '处理中';
};
const getTaskStatusTagType = (status: string) => {
  if (status === 'completed') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'deleted') return 'info';
  return 'warning';
};

// 获取数据方法
const fetchOverview = async () => {
  loadingOverview.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    overviewData.value = await getAdminOverview(token);
  } catch (error) {
    handleAdminRequestError(error, '获取后台首页概况失败');
  } finally {
    loadingOverview.value = false;
  }
};

const fetchOrders = async () => {
  loadingOrders.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getAdminOrders(token, {
      page: orderPagination.page,
      page_size: orderPagination.pageSize,
      status: filters.orderStatus,
      keyword: filters.keyword.trim(),
      created_from: filters.createdDateRange[0] || undefined,
      created_to: filters.createdDateRange[1] || undefined
    });
    ordersData.value = res.items || [];
    orderPagination.total = res.total || 0;
  } catch (error) {
    handleAdminRequestError(error, '获取订单列表失败');
  } finally {
    loadingOrders.value = false;
  }
};

const fetchTasks = async () => {
  loadingTasks.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getAdminTasks(token, {
      page: taskPagination.page,
      page_size: taskPagination.pageSize,
      status: filters.taskStatus,
      keyword: filters.keyword.trim(),
      created_from: filters.createdDateRange[0] || undefined,
      created_to: filters.createdDateRange[1] || undefined
    });
    tasksData.value = res.items || [];
    taskPagination.total = res.total || 0;
    selectedTaskRows.value = [];
  } catch (error) {
    handleAdminRequestError(error, '获取任务列表失败');
  } finally {
    loadingTasks.value = false;
  }
};

const fetchLogs = async () => {
  loadingLogs.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getAdminLogs(token, {
      page: logPagination.page,
      page_size: logPagination.pageSize,
      keyword: filters.keyword.trim()
    });
    logsData.value = res.items || [];
    logPagination.total = res.total || 0;
  } catch (error) {
    handleAdminRequestError(error, '获取操作日志失败');
  } finally {
    loadingLogs.value = false;
  }
};

const fetchSettings = async () => {
  loadingSettings.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await getSystemSettings(token);
    Object.assign(settingsForm, createDefaultSettingsForm(), res || {});
  } catch (error) {
    handleAdminRequestError(error, '获取系统配置失败');
  } finally {
    loadingSettings.value = false;
  }
};

const saveSettings = async () => {
  const trimmedSiteBaseUrl = normalizedSiteBaseUrl.value;
  const trimmedSiteTitle = settingsForm.site_title.trim();
  const trimmedGateway = settingsForm.alipay_gateway.trim();
  const trimmedPromoEndsAt = settingsForm.promo_ends_at.trim();
  const trimmedPromoNote = settingsForm.promo_note.trim();
  const trimmedPromoBadge = settingsForm.promo_badge.trim();
  const trimmedPromoLossAversionText = settingsForm.promo_loss_aversion_text.trim();
  if (settingsForm.alipay_enabled && !trimmedGateway) {
    ElMessage.warning('请填写支付宝网关');
    return;
  }

  if (settingsForm.promo_enabled && settingsForm.promo_price_per_b_file_cents >= settingsForm.price_per_b_file_cents) {
    ElMessage.warning('优惠价必须低于原价');
    return;
  }
  if (settingsForm.promo_enabled && settingsForm.promo_countdown_enabled && !trimmedPromoEndsAt) {
    ElMessage.warning('开启倒计时时请填写活动截止时间');
    return;
  }

  const trimmedAlipayNotifyUrl = settingsForm.alipay_notify_url.trim();
  if (settingsForm.alipay_enabled && !trimmedAlipayNotifyUrl && !trimmedSiteBaseUrl) {
    ElMessage.warning('请填写网站域名或手动填写支付宝异步通知地址');
    return;
  }

  const trimmedWechatAppId = settingsForm.wechat_app_id.trim();
  const trimmedWechatMchId = settingsForm.wechat_mch_id.trim();
  const trimmedWechatApiKey = settingsForm.wechat_api_v2_key.trim();
  const trimmedWechatNotifyUrl = settingsForm.wechat_notify_url.trim();
  if (settingsForm.wechat_enabled && (!trimmedWechatAppId || !trimmedWechatMchId || !trimmedWechatApiKey)) {
    ElMessage.warning('请完整填写微信支付配置');
    return;
  }
  if (settingsForm.wechat_enabled && !trimmedWechatNotifyUrl && !trimmedSiteBaseUrl) {
    ElMessage.warning('请填写网站域名或手动填写微信异步通知地址');
    return;
  }

  savingSettings.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const submittedSnapshot = {
      site_base_url: trimmedSiteBaseUrl,
      site_title: trimmedSiteTitle,
      promo_enabled: settingsForm.promo_enabled,
      promo_price_per_b_file_cents: settingsForm.promo_price_per_b_file_cents,
      promo_ends_at: trimmedPromoEndsAt,
      promo_note: trimmedPromoNote,
      promo_badge: trimmedPromoBadge,
      promo_countdown_enabled: settingsForm.promo_countdown_enabled,
      promo_loss_aversion_text: trimmedPromoLossAversionText,
      alipay_gateway: trimmedGateway,
      wechat_enabled: settingsForm.wechat_enabled,
      wechat_app_id: trimmedWechatAppId,
      wechat_mch_id: trimmedWechatMchId,
      wechat_api_v2_key: trimmedWechatApiKey,
      wechat_notify_url: trimmedWechatNotifyUrl
    };
    await updateSystemSettings(token, {
      ...settingsForm,
      site_base_url: trimmedSiteBaseUrl,
      site_title: trimmedSiteTitle,
      promo_ends_at: trimmedPromoEndsAt,
      promo_note: trimmedPromoNote,
      promo_badge: trimmedPromoBadge,
      promo_loss_aversion_text: trimmedPromoLossAversionText,
      alipay_gateway: trimmedGateway,
      alipay_notify_url: trimmedAlipayNotifyUrl,
      wechat_app_id: trimmedWechatAppId,
      wechat_mch_id: trimmedWechatMchId,
      wechat_api_v2_key: trimmedWechatApiKey,
      wechat_notify_url: trimmedWechatNotifyUrl
    });
    await fetchSettings();
    const paymentConfigMismatch =
      settingsForm.site_base_url !== submittedSnapshot.site_base_url ||
      settingsForm.site_title.trim() !== submittedSnapshot.site_title ||
      settingsForm.promo_enabled !== submittedSnapshot.promo_enabled ||
      settingsForm.promo_price_per_b_file_cents !== submittedSnapshot.promo_price_per_b_file_cents ||
      settingsForm.promo_ends_at !== submittedSnapshot.promo_ends_at ||
      settingsForm.promo_note.trim() !== submittedSnapshot.promo_note ||
      settingsForm.promo_badge.trim() !== submittedSnapshot.promo_badge ||
      settingsForm.promo_countdown_enabled !== submittedSnapshot.promo_countdown_enabled ||
      settingsForm.promo_loss_aversion_text.trim() !== submittedSnapshot.promo_loss_aversion_text ||
      settingsForm.alipay_gateway !== submittedSnapshot.alipay_gateway ||
      settingsForm.wechat_enabled !== submittedSnapshot.wechat_enabled ||
      settingsForm.wechat_app_id !== submittedSnapshot.wechat_app_id ||
      settingsForm.wechat_mch_id !== submittedSnapshot.wechat_mch_id ||
      settingsForm.wechat_api_v2_key !== submittedSnapshot.wechat_api_v2_key ||
      settingsForm.wechat_notify_url !== submittedSnapshot.wechat_notify_url;

    if (paymentConfigMismatch) {
      ElMessage.warning('保存请求已发送，但后端未返回最新的标题或支付配置。请先重启后端服务，再重新保存一次。');
      return;
    }

    ElMessage.success('系统配置已保存');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存系统配置失败');
  } finally {
    savingSettings.value = false;
  }
};

const handleChangePassword = async () => {
  if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
    ElMessage.warning('请完整填写密码信息');
    return;
  }

  changingPassword.value = true;
  try {
    const token = localStorage.getItem('admin_token') || '';
    const res = await changeAdminPassword(token, passwordForm);
    ElMessage.success('管理员密码已修改，请重新登录');
    passwordForm.current_password = '';
    passwordForm.new_password = '';
    passwordForm.confirm_password = '';

    if (res.force_relogin) {
      handleLogout();
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '修改密码失败');
  } finally {
    changingPassword.value = false;
  }
};

const refreshAll = () => {
  fetchOverview();
  fetchOrders();
  fetchTasks();
  fetchLogs();
  fetchSettings();
};

watch(
  adminPanelTitle,
  (value) => {
    applyRouteSeo(
      {
        title: value,
        description: '网站运营后台工作台。',
        robots: 'noindex,nofollow'
      },
      { currentPath: '/admin' }
    );
  },
  { immediate: true }
);

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

const handleTaskSelectionChange = (rows: any[]) => {
  selectedTaskRows.value = rows;
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
    await ElMessageBox.confirm(`确认物理删除任务 ${selectedTask.value.task_no} 吗？关联订单记录、任务记录和上传文件都会被彻底删除，且无法恢复！`, '危险操作', { type: 'error' });
    actionLoading.deleteTask = true;
    const token = localStorage.getItem('admin_token') || '';
    await deleteTaskData(token, selectedTask.value.task_no);
    ElMessage.success('任务及其关联文件已物理删除');
    refreshAll();
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('数据删除失败');
  } finally {
    actionLoading.deleteTask = false;
  }
};

const handleBatchDeleteTasks = async () => {
  if (!selectedTaskRows.value.length) return;
  const taskNos = selectedTaskRows.value.map((row) => row.task_no);
  try {
    await ElMessageBox.confirm(
      `确认物理删除已选中的 ${taskNos.length} 条任务吗？关联订单记录、任务记录和上传文件都会被彻底删除，且无法恢复。`,
      '危险操作',
      { type: 'error' }
    );
    actionLoading.batchDeleteTask = true;
    const token = localStorage.getItem('admin_token') || '';
    const result = await batchDeleteTaskData(token, taskNos);
    selectedTask.value = null;
    selectedTaskRows.value = [];
    ElMessage.success(`已物理删除 ${result.deleted_count} 条任务`);
    refreshAll();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '批量删除失败');
    }
  } finally {
    actionLoading.batchDeleteTask = false;
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
  filters.createdDateRange = [];
  orderPagination.page = 1;
  taskPagination.page = 1;
  logPagination.page = 1;
  refreshAll();
};

const applyFilters = () => {
  orderPagination.page = 1;
  taskPagination.page = 1;
  logPagination.page = 1;
  refreshAll();
  ElMessage.success('筛选已应用');
};

const handleOrderPageChange = (page: number) => {
  orderPagination.page = page;
  fetchOrders();
};

const handleOrderSizeChange = (size: number) => {
  orderPagination.page = 1;
  orderPagination.pageSize = size;
  fetchOrders();
};

const handleTaskPageChange = (page: number) => {
  taskPagination.page = page;
  fetchTasks();
};

const handleTaskSizeChange = (size: number) => {
  taskPagination.page = 1;
  taskPagination.pageSize = size;
  fetchTasks();
};

const handleLogPageChange = (page: number) => {
  logPagination.page = page;
  fetchLogs();
};

const handleLogSizeChange = (size: number) => {
  logPagination.page = 1;
  logPagination.pageSize = size;
  fetchLogs();
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

.admin-site-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--ink);
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.admin-site-title:hover {
  opacity: 0.72;
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

.gateway-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.overview-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.overview-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 4px 0 8px;
}

.overview-hero h2 {
  margin: 0 0 6px;
  font-size: 24px;
  color: var(--ink);
}

.overview-hero p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.overview-stat-card {
  border: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(245, 247, 250, 0.95));
  border-radius: 16px;
  padding: 18px;
}

.overview-stat-card span {
  display: block;
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 10px;
}

.overview-stat-card strong {
  display: block;
  font-size: 28px;
  line-height: 1.1;
  color: var(--ink);
}

.overview-stat-card p {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.overview-panels,
.overview-tables {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.overview-panel {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--surface);
  padding: 18px;
}

.overview-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.overview-panel__head h3 {
  margin: 0;
  font-size: 16px;
  color: var(--ink);
}

.overview-kv-list,
.home-channel-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.overview-kv-item,
.home-channel-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--panel);
  border: 1px solid var(--line);
}

.overview-kv-item span,
.home-channel-item p {
  color: var(--muted);
  font-size: 12px;
}

.overview-kv-item strong,
.home-channel-item strong {
  display: block;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.5;
  word-break: break-all;
}

.overview-kv-item strong {
  max-width: 72%;
  text-align: right;
}

.home-side-actions,
.overview-shortcuts {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.overview-shortcut {
  text-align: left;
  width: 100%;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 14px;
  padding: 14px 16px;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.overview-shortcut:hover {
  border-color: var(--el-color-primary);
  transform: translateY(-1px);
}

.overview-shortcut strong {
  display: block;
  margin-bottom: 6px;
  font-size: 15px;
  color: var(--ink);
}

.overview-shortcut span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.overview-log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.overview-log-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px 16px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--panel);
}

.overview-log-item strong {
  color: var(--ink);
  font-size: 14px;
}

.overview-log-item span,
.overview-log-item time {
  color: var(--muted);
  font-size: 12px;
}

.overview-log-item time {
  grid-row: span 2;
  align-self: center;
}

.home-side-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.task-table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.task-table-toolbar__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-table-toolbar__meta strong {
  color: var(--ink);
  font-size: 14px;
}

.task-table-toolbar__meta span {
  color: var(--muted);
  font-size: 12px;
}

@media (max-width: 1200px) {
  .overview-stats,
  .overview-panels,
  .overview-tables {
    grid-template-columns: 1fr;
  }

  .task-table-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
