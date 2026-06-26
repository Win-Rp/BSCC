<template>
  <section class="single-view upload-view">
    <el-card shadow="never" class="glass-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>任务创建工作台</h2>
            <p>上传主标书 A 与对比标书 B 即可快速进行查重比对。</p>
          </div>
        </div>
      </template>

      <section class="section-stack">
        <div class="upload-cards-horizontal">
          <UploadDropCard
            v-model:files="aFiles"
            mark="A"
            title="主标书 A"
            description="建议上传最终提交版本，仅允许 1 份。"
            variant="a-box"
          />
          <UploadDropCard
            v-model:files="bFiles"
            mark="B"
            title="对比标书 B"
            description="支持 1-10 份，超过 1 份按 1 对多流程处理。"
            variant="b-box"
            multiple
          />
        </div>

        <el-form label-position="top" class="keyword-form">
          <el-form-item label="关键字查重">
            <el-select
              v-model="keywordsList"
              multiple
              filterable
              allow-create
              default-first-option
              :reserve-keyword="false"
              placeholder="输入关键字后按回车添加（示例：围标、独家授权）"
              class="keyword-select"
            />
          </el-form-item>
        </el-form>

        <div class="action-strip">
          <el-button type="primary" size="large" :loading="submitting" @click="startCheck">
            开始查重
          </el-button>
        </div>
      </section>
    </el-card>

  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import UploadDropCard from "@/components/UploadDropCard.vue";
import { createTask } from "@/services/api";
import { saveTaskNo } from "@/services/session";

const router = useRouter();
const keywordsList = ref<string[]>([]);
const submitting = ref(false);
const aFiles = ref<File[]>([]);
const bFiles = ref<File[]>([]);

async function startCheck() {
  if (!aFiles.value[0]) {
    ElMessage.warning("请先选择主标书 A");
    return;
  }

  if (!bFiles.value.length) {
    ElMessage.warning("请至少选择 1 份 B 标书");
    return;
  }

  if (bFiles.value.length > 10) {
    ElMessage.warning("B 标书最多选择 10 份");
    return;
  }

  const invalidFile = [...aFiles.value, ...bFiles.value].find((file) => !isSupportedFile(file));
  if (invalidFile) {
    ElMessage.error(`${invalidFile.name} 暂不支持，请上传 DOCX 或可复制文本 PDF`);
    return;
  }

  submitting.value = true;
  try {
    const task = await createTask({
      aFile: aFiles.value[0],
      bFiles: bFiles.value,
      keywords: keywordsList.value.join("\n")
    });
    saveTaskNo(task.task_no);
    await router.push({ path: "/results", query: { task: task.task_no } });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "创建任务失败");
  } finally {
    submitting.value = false;
  }
}

function formatSize(size: number) {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function isSupportedFile(file: File) {
  const name = file.name.toLowerCase();
  return name.endsWith(".docx") || name.endsWith(".pdf");
}
</script>
