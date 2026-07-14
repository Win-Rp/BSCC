<template>
  <section class="single-view upload-view">
    <el-card shadow="never" class="glass-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>{{ t("upload.title") }}</h2>
            <p>{{ t("upload.subtitle") }}</p>
          </div>
          <el-button link type="primary" @click="recoverDialogVisible = true">
            {{ t("upload.recover") }}
          </el-button>
        </div>
      </template>

      <section class="section-stack">
        <div class="upload-cards-horizontal">
          <UploadDropCard
            v-model:files="aFiles"
            mark="A"
            :title="t('upload.aTitle')"
            :description="t('upload.aDesc')"
            variant="a-box"
          />
          <UploadDropCard
            v-model:files="bFiles"
            mark="B"
            :title="t('upload.bTitle')"
            :description="t('upload.bDesc')"
            variant="b-box"
            multiple
          />
        </div>

        <el-form label-position="top" class="keyword-form">
          <el-form-item :label="t('upload.keywordLabel')">
            <el-select
              v-model="keywordsList"
              multiple
              filterable
              allow-create
              default-first-option
              :reserve-keyword="false"
              :placeholder="t('upload.keywordPlaceholder')"
              class="keyword-select"
            />
          </el-form-item>
        </el-form>

        <el-alert
          type="warning"
          :closable="false"
          show-icon
          class="queue-tip"
          title="当前人数较多，受服务器性能所限，查重可能需要更长时间。你可以收藏当前页面，或记录任务 ID 后稍后回来查看结果。"
        />

        <div class="action-strip upload-action-strip">
          <el-button 
            type="primary" 
            size="large" 
            class="submit-button"
            :loading="submitting" 
            @click="startCheck"
          >
            <el-icon class="submit-icon" v-if="!submitting"><Search /></el-icon>
            {{ t("upload.start") }}
          </el-button>
        </div>
      </section>
    </el-card>

    <!-- 找回任务弹窗 -->
    <el-dialog v-model="recoverDialogVisible" :title="t('upload.recoverDialogTitle')" width="400px" center>
      <div class="recover-dialog-content">
        <p class="recover-tip">{{ t("upload.recoverTip") }}</p>
        <el-input 
          v-model="recoverTaskId" 
          :placeholder="t('upload.recoverPlaceholder')" 
          clearable 
          @keyup.enter="handleRecover"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="recoverDialogVisible = false">{{ t("upload.cancel") }}</el-button>
          <el-button type="primary" @click="handleRecover" :disabled="!recoverTaskId.trim()">
            {{ t("upload.recoverNow") }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useHead } from "@unhead/vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import UploadDropCard from "@/components/UploadDropCard.vue";
import { useAppI18n } from "@/composables/useAppI18n";
import { createTask } from "@/services/api";
import { saveTaskNo } from "@/services/session";
import { createHeadConfig, resolveRouteSeo } from "@/utils/seo";

const router = useRouter();
const { localizeDeep, t } = useAppI18n();
useHead(
  createHeadConfig(
    localizeDeep(resolveRouteSeo(
      {
        title: "标书查重工具入口_上传投标文件开始检查_{siteTitle}",
        description:
          "上传主标书 A 与对比标书 B，开始标书查重、标书检查和围标风险排查，支持 DOCX 与可复制文本 PDF。",
        keywords: ["标书查重入口", "投标文件查重", "标书检查工具", "围标风险排查"]
      },
      { currentPath: "/upload" }
    ))
  ) as any
);
const keywordsList = ref<string[]>([]);
const submitting = ref(false);
const aFiles = ref<File[]>([]);
const bFiles = ref<File[]>([]);

const recoverDialogVisible = ref(false);
const recoverTaskId = ref("");

function handleRecover() {
  const tid = recoverTaskId.value.trim();
  if (!tid) return;
  saveTaskNo(tid);
  router.push({ path: "/results", query: { task: tid } });
}

async function startCheck() {
  if (!aFiles.value[0]) {
    ElMessage.warning(t("upload.warnings.missingA"));
    return;
  }

  if (!bFiles.value.length) {
    ElMessage.warning(t("upload.warnings.missingB"));
    return;
  }

  if (bFiles.value.length > 10) {
    ElMessage.warning(t("upload.warnings.exceedB"));
    return;
  }

  const invalidFile = [...aFiles.value, ...bFiles.value].find((file) => !isSupportedFile(file));
  if (invalidFile) {
    ElMessage.error(t("upload.warnings.unsupported", { name: invalidFile.name }));
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
    ElMessage.error(error instanceof Error ? error.message : t("upload.warnings.createFailed"));
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

<style scoped>
.upload-action-strip {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.submit-button {
  width: min(100%, 360px);
  height: 56px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 28px;
  background: linear-gradient(135deg, #111, #333);
  border: none;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.submit-button:hover:not(.is-loading) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
  background: linear-gradient(135deg, #000, #222);
}

.submit-button:active:not(.is-loading) {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.submit-icon {
  margin-right: 8px;
  font-size: 20px;
}

.recover-dialog-content {
  text-align: center;
  padding: 10px 0;
}

.recover-tip {
  color: var(--muted);
  font-size: 13px;
  margin-bottom: 16px;
}

.queue-tip {
  margin-top: 8px;
  border-radius: 14px;
}
</style>
