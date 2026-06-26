<template>
  <el-dialog
    v-model="visible"
    width="520px"
    class="payment-dialog"
    title="支付并解锁完整详情"
    align-center
  >
    <div class="payment-layout">
      <section class="payment-intro">
        <div>
          <span class="section-eyebrow">订单信息</span>
          <h3>本次解锁将开放完整对比详情</h3>
          <p>包括双栏文档对比、命中片段定位、格式项说明与元数据结果。</p>
        </div>
        <div class="payment-summary-grid">
          <article class="payment-summary-card">
            <span>任务号</span>
            <strong>{{ taskNo || "-" }}</strong>
          </article>
          <article class="payment-summary-card">
            <span>支付状态</span>
            <strong>{{ statusText }}</strong>
          </article>
        </div>
      </section>

      <el-form label-position="top" class="payment-form">
        <el-form-item label="联系方式">
          <el-input
            v-model="contact"
            placeholder="邮箱 / 手机号 / 微信号"
            maxlength="64"
          />
        </el-form-item>
      </el-form>

      <section class="payment-order-panel">
        <div class="payment-order-panel__head">
          <strong>{{ order ? "已生成待支付订单" : "支付单尚未生成" }}</strong>
          <el-tag :type="orderStatusTagType">{{ orderStatusLabel }}</el-tag>
        </div>

        <div v-if="order" class="payment-order-list">
          <div><span>订单号</span><strong>{{ order.order_no }}</strong></div>
          <div><span>任务范围</span><strong>{{ order.b_file_count }} 份 B 文件</strong></div>
          <div><span>订单金额</span><strong>{{ formatMoney(order.amount_cents) }}</strong></div>
          <div><span>联系方式</span><strong>{{ contact || "-" }}</strong></div>
        </div>
        <div v-else class="payment-empty-state">
          先填写联系方式并生成订单，随后可轮询支付状态或触发模拟支付。
        </div>
      </section>

      <section class="payment-qr-panel">
        <div class="payment-qr-panel__placeholder">
          <strong>{{ order?.qr_code_url ? "已返回支付二维码地址" : "等待生成支付二维码" }}</strong>
          <span>{{ order?.qr_code_url || "当前后端未返回实际二维码时，保持展示订单与状态信息。" }}</span>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="payment-footer">
        <el-button @click="visible = false">稍后处理</el-button>
        <el-button
          v-if="!order"
          type="primary"
          :loading="creating"
          @click="handleCreateOrder"
        >
          生成支付订单
        </el-button>
        <template v-else>
          <el-button :loading="checking" @click="checkPaymentStatus">刷新状态</el-button>
          <el-button type="primary" :loading="paying" @click="handlePaid">模拟支付成功</el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import {
  createOrder,
  getOrderStatus,
  simulateAlipayNotify,
  type OrderInfo,
  type OrderStatus
} from "@/services/api";
import { saveOrderNo } from "@/services/session";

const props = defineProps<{ modelValue: boolean; taskNo: string }>();
const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  paid: [];
}>();

const contact = ref("");
const creating = ref(false);
const checking = ref(false);
const paying = ref(false);
const order = ref<OrderInfo | null>(null);
const orderStatus = ref<OrderStatus | null>(null);
let pollTimer: number | undefined;

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit("update:modelValue", value)
});

const taskNo = computed(() => props.taskNo);
const statusText = computed(() => {
  if (!order.value) return "待创建";
  if (orderStatus.value?.status === "paid") return "已支付";
  return "待支付";
});
const orderStatusLabel = computed(() => {
  if (!order.value) return "未生成";
  return orderStatus.value?.status === "paid" ? "已支付" : "待支付";
});
const orderStatusTagType = computed(() => {
  if (!order.value) return "info";
  return orderStatus.value?.status === "paid" ? "success" : "warning";
});

async function handleCreateOrder() {
  if (!props.taskNo) {
    ElMessage.warning("缺少任务号，无法创建订单");
    return;
  }

  if (!contact.value.trim()) {
    ElMessage.warning("请填写联系方式，便于根据订单排查问题");
    return;
  }

  creating.value = true;
  try {
    order.value = await createOrder(props.taskNo, contact.value.trim());
    saveOrderNo(order.value.order_no);
    await checkPaymentStatus();
    startPolling();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "创建订单失败");
  } finally {
    creating.value = false;
  }
}

async function handlePaid() {
  if (!order.value) return;

  paying.value = true;
  try {
    await simulateAlipayNotify(order.value.order_no);
    await checkPaymentStatus();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "支付状态更新失败");
  } finally {
    paying.value = false;
  }
}

function startPolling() {
  window.clearInterval(pollTimer);
  pollTimer = window.setInterval(() => {
    void checkPaymentStatus();
  }, 2500);
}

async function checkPaymentStatus() {
  if (!order.value) return;

  checking.value = true;
  try {
    orderStatus.value = await getOrderStatus(order.value.order_no);
    if (orderStatus.value.status === "paid") {
      window.clearInterval(pollTimer);
      ElMessage.success("支付成功，本次任务已解锁完整详情");
      visible.value = false;
      emit("paid");
    }
  } catch (error) {
    window.clearInterval(pollTimer);
    ElMessage.error(error instanceof Error ? error.message : "查询支付状态失败");
  } finally {
    checking.value = false;
  }
}

function formatMoney(cents: number) {
  return `¥${(cents / 100).toFixed(2)}`;
}

watch(visible, (value) => {
  if (!value) {
    window.clearInterval(pollTimer);
  } else if (order.value && orderStatus.value?.status !== "paid") {
    startPolling();
  }
});

watch(() => props.taskNo, () => {
  window.clearInterval(pollTimer);
  order.value = null;
  orderStatus.value = null;
});

onBeforeUnmount(() => {
  window.clearInterval(pollTimer);
});
</script>
