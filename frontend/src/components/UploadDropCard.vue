<template>
  <div class="upload-drop-card" :class="variant">
    <div class="upload-drop-card__head">
      <div class="upload-drop-card__mark">{{ mark }}</div>
      <div class="upload-drop-card__meta">
        <strong>{{ title }}</strong>
        <span>{{ description }}</span>
      </div>
      <el-button
        v-if="files.length"
        text
        type="danger"
        class="upload-drop-card__clear"
        @click.stop="emit('update:files', [])"
      >
        清空
      </el-button>
    </div>

    <el-upload
      drag
      action="#"
      :auto-upload="false"
      :show-file-list="false"
      :multiple="multiple"
      :accept="accept"
      :on-change="handleChange"
      class="upload-box"
      :class="variant"
    >
      <div class="upload-drop-card__zone">
        <el-icon class="upload-drop-card__icon"><UploadFilled /></el-icon>
        <strong>{{ files.length ? selectedText : emptyTitle }}</strong>
        <span>{{ files.length ? "可继续拖入替换，系统不会自动上传。" : "拖拽文件到此处，或点击选择文件。" }}</span>
      </div>
    </el-upload>

    <ul class="upload-drop-card__list">
      <li v-if="!files.length" class="is-empty">尚未选择文件</li>
      <li v-for="file in files" :key="file.name + file.size">
        <div class="file-item-left">
          <svg v-if="isWord(file.name)" class="file-icon" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="6" fill="#2b579a"/>
            <path d="M21.5 10H24L20 22H17.5L16 15L14.5 22H12L8 10H10.5L13 18.5L14.7 10H17.3L19 18.5L21.5 10Z" fill="white"/>
          </svg>
          <svg v-else-if="isPdf(file.name)" class="file-icon" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="6" fill="#f40f02"/>
            <path d="M12.5 10.5V21.5H14.5V17.5H16.5C18.5 17.5 20 16 20 14C20 12 18.5 10.5 16.5 10.5H12.5ZM14.5 12.5H16.5C17.5 12.5 18 13 18 14C18 15 17.5 15.5 16.5 15.5H14.5V12.5Z" fill="white"/>
          </svg>
          <svg v-else class="file-icon" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="6" fill="#888888"/>
            <path d="M11 10V22H21V14L17 10H11ZM13 12H16V15H19V20H13V12Z" fill="white"/>
          </svg>
          <span>{{ file.name }}</span>
        </div>
        <em>{{ formatSize(file.size) }}</em>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import type { UploadFile, UploadFiles } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import { computed } from "vue";

const props = defineProps<{
  mark: string;
  title: string;
  description: string;
  multiple?: boolean;
  variant: "a-box" | "b-box";
  files: File[];
}>();

const emit = defineEmits<{
  "update:files": [files: File[]];
}>();

const accept = ".docx,.pdf";
const emptyTitle = computed(() => props.multiple ? "批量导入对比文件" : "导入主文档");
const selectedText = computed(() => {
  if (!props.files.length) {
    return "";
  }
  if (props.files.length === 1) {
    return props.files[0].name;
  }
  return `已选择 ${props.files.length} 份文件`;
});

function handleChange(_file: UploadFile, uploadFiles: UploadFiles) {
  const rawFiles: File[] = [];

  uploadFiles.forEach((item) => {
    if (item.raw) {
      rawFiles.push(item.raw);
    }
  });

  emit("update:files", props.multiple ? rawFiles.slice(0, 10) : rawFiles.slice(-1));
}

function formatSize(size: number) {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function isWord(filename: string) {
  return filename.toLowerCase().endsWith(".docx") || filename.toLowerCase().endsWith(".doc");
}

function isPdf(filename: string) {
  return filename.toLowerCase().endsWith(".pdf");
}
</script>
