<template>
  <section class="view-grid">
    <el-card shadow="never" class="glass-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>任务恢复</h2>
            <p>通过任务号、订单号或联系方式重新定位结果，恢复后可继续查看摘要、预览或完整详情。</p>
          </div>
        </div>
      </template>

      <section class="section-stack">
        <article class="plain-panel">
          <div class="detail-section__head">
            <div>
              <h3>恢复方式</h3>
              <p>系统优先校验任务号，再结合订单号与联系方式确认任务归属。</p>
            </div>
            <el-tag>至少填写任务号或订单号</el-tag>
          </div>

          <el-form label-position="top">
            <el-form-item label="任务号">
              <el-input v-model="form.taskNo" placeholder="输入任务号" />
            </el-form-item>
            <el-form-item label="订单号">
              <el-input v-model="form.orderNo" placeholder="输入订单号" />
            </el-form-item>
            <el-form-item label="联系方式">
              <el-input v-model="form.contact" placeholder="输入邮箱、手机号或微信号" />
            </el-form-item>
          </el-form>

          <div class="audit-strip">
            <article class="audit-strip__item">
              <span>保留周期</span>
              <strong>7 天</strong>
            </article>
            <article class="audit-strip__item">
              <span>核验方式</span>
              <strong>任务 / 订单 / 联系方式</strong>
            </article>
            <article class="audit-strip__item">
              <span>恢复结果</span>
              <strong>摘要 / 预览 / 详情</strong>
            </article>
            <article class="audit-strip__item">
              <span>当前状态</span>
              <strong>{{ result ? "已完成恢复" : "等待查询" }}</strong>
            </article>
          </div>

          <div class="action-strip">
            <div class="inline-tags">
              <el-tag>支持任务号恢复</el-tag>
              <el-tag type="info">支持订单号恢复</el-tag>
              <el-tag type="warning">联系方式仅辅助校验</el-tag>
            </div>
            <el-button type="primary" size="large" :loading="loading" @click="handleRecover">
              查询恢复
            </el-button>
          </div>
        </article>
      </section>
    </el-card>

    <aside class="side-stack">
      <el-card shadow="never" class="glass-card">
        <span class="section-eyebrow">恢复结果</span>
        <div v-if="result" class="section-stack">
          <div class="info-list">
            <div><span>当前状态</span><strong>恢复成功</strong></div>
            <div><span>恢复目标</span><strong>结果总览</strong></div>
            <div><span>已校验字段</span><strong>{{ verifiedFieldsLabel }}</strong></div>
            <div><span>可继续动作</span><strong>{{ result.can_view_detail ? "查看详情" : "查看摘要" }}</strong></div>
          </div>
          <el-alert
            :title="`已找到任务 ${result.task_no}`"
            :description="`状态：${result.task_status}；${result.can_view_detail ? '当前可查看完整详情。' : '当前可查看摘要与预览，必要时继续支付。'}`"
            type="success"
            :closable="false"
            show-icon
          />
          <div class="button-row">
            <el-button type="primary" @click="goResults">查看结果</el-button>
          </div>
        </div>
        <p v-else>提交查询后，会先在这里返回恢复结果，再决定继续查看结果页。</p>
      </el-card>

      <el-card shadow="never" class="glass-card">
        <span class="section-eyebrow">操作说明</span>
        <ul class="rule-list">
          <li>优先填写任务号；若任务号缺失，再补充订单号与联系方式。</li>
          <li>提交后先确认恢复结果，再判断是否需要前往结果页。</li>
          <li>如遇订单未解锁、任务超期或信息不一致，请联系管理员。</li>
        </ul>
      </el-card>

      <el-card shadow="never" class="glass-card">
        <span class="section-eyebrow">恢复说明</span>
        <ul class="rule-list">
          <li>恢复入口仅处理 7 天内仍在保留期的任务与订单。</li>
          <li>联系方式用于辅助校验，不会单独作为找回依据。</li>
          <li>恢复成功后会保留当前任务上下文，便于继续对比与审阅。</li>
        </ul>
      </el-card>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { recoverTask, type RecoverResult } from "@/services/api";
import { saveOrderNo, saveTaskNo } from "@/services/session";

const router = useRouter();
const loading = ref(false);
const result = ref<RecoverResult | null>(null);
const form = reactive({
  taskNo: "",
  orderNo: "",
  contact: ""
});
const verifiedFieldsLabel = computed(() => {
  if (!result.value) return "-";
  const fields: string[] = [];
  if (form.taskNo) fields.push("任务号");
  if (form.orderNo) fields.push("订单号");
  if (form.contact) fields.push("联系方式");
  return fields.join(" + ") || "系统自动匹配";
});

async function handleRecover() {
  if (!form.taskNo && !form.orderNo) {
    ElMessage.warning("请至少填写任务号或订单号");
    return;
  }

  loading.value = true;
  try {
    result.value = await recoverTask({
      task_no: form.taskNo || undefined,
      order_no: form.orderNo || undefined,
      contact: form.contact || undefined
    });
    saveTaskNo(result.value.task_no);
    if (result.value.order_no) {
      saveOrderNo(result.value.order_no);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "恢复失败");
  } finally {
    loading.value = false;
  }
}

function goResults() {
  if (!result.value) return;
  void router.push({ path: "/results", query: { task: result.value.task_no } });
}
</script>
