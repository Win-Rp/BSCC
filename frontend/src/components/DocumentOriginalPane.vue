<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import VuePdfEmbed, {
  GlobalWorkerOptions,
  usePdfDocument,
  usePdfSearch
} from "vue-pdf-embed/dist/index.essential.mjs";
import { renderAsync } from "docx-preview";
import Mark from "mark.js";
import { useAppI18n } from "@/composables/useAppI18n";
import PdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

import "vue-pdf-embed/dist/styles/annotationLayer.css";
import "vue-pdf-embed/dist/styles/textLayer.css";

GlobalWorkerOptions.workerSrc = PdfWorker;

const props = defineProps<{
  title: string;
  fileUrl: string;
  fileName: string;
  activeText: string;
}>();
const { translateText } = useAppI18n();

const docxHost = ref<HTMLElement | null>(null);
const isRenderingDocx = ref(false);
const docxError = ref("");
const isLoadingPdf = ref(false);
const pdfError = ref("");
const pdfRendered = ref(false);
const pdfSource = ref("");
let markInstance: Mark | null = null;

const fileExt = computed(() => {
  const normalized = props.fileName.toLowerCase();
  if (normalized.endsWith(".pdf")) return ".pdf";
  if (normalized.endsWith(".docx")) return ".docx";
  return "";
});

const isPdf = computed(() => fileExt.value === ".pdf");
const isDocx = computed(() => fileExt.value === ".docx");

const { doc } = usePdfDocument({ source: pdfSource });
const { clear, find, findController } = usePdfSearch(doc);

function clearPdfSource() {
  if (pdfSource.value.startsWith("blob:")) {
    URL.revokeObjectURL(pdfSource.value);
  }
  pdfSource.value = "";
}

function buildCandidateUrls(url: string) {
  const candidates = [url];

  try {
    const parsed = new URL(url);
    const hostnames = parsed.hostname === "127.0.0.1"
      ? ["127.0.0.1", "localhost"]
      : parsed.hostname === "localhost"
        ? ["localhost", "127.0.0.1"]
        : [parsed.hostname];
    const ports = parsed.port === "8000" ? ["8000", "8010"] : [parsed.port];

    for (const hostname of hostnames) {
      for (const port of ports) {
        const next = new URL(url);
        next.hostname = hostname;
        next.port = port;
        candidates.push(next.toString());
      }
    }
  } catch {
    return candidates;
  }

  return [...new Set(candidates)];
}

async function fetchOriginalFile() {
  let lastError: Error | null = null;

  for (const candidate of buildCandidateUrls(props.fileUrl)) {
    try {
      const response = await fetch(candidate);
      if (!response.ok) {
        throw new Error(`${translateText("加载原文档失败")}：${response.status}`);
      }
      return response;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(translateText("加载原文档失败"));
    }
  }

  throw lastError ?? new Error(translateText("加载原文档失败"));
}

function updatePdfSearch() {
  if (!doc.value) return;

  try {
    clear();
    const keyword = props.activeText.trim();
    if (pdfRendered.value && keyword) {
      find(keyword, { highlightAll: true });
    }
  } catch {
    // PDF text layer may not be ready on the first tick; the next render will retry.
  }
}

async function renderDocxFile() {
  if (!isDocx.value || !docxHost.value) return;

  isRenderingDocx.value = true;
  docxError.value = "";
  docxHost.value.innerHTML = "";

  try {
    const response = await fetchOriginalFile();
    const blob = await response.blob();
    await renderAsync(blob, docxHost.value, docxHost.value, {
      className: "docx-viewer",
      inWrapper: true,
      breakPages: true,
      ignoreLastRenderedPageBreak: false,
      useBase64URL: true
    });
    markInstance = new Mark(docxHost.value);
    await highlightDocx();
  } catch (error) {
    docxError.value = error instanceof Error ? error.message : translateText("Word 原文档渲染失败");
  } finally {
    isRenderingDocx.value = false;
  }
}

async function loadPdfFile() {
  if (!isPdf.value || !props.fileUrl) return;

  isLoadingPdf.value = true;
  pdfError.value = "";
  pdfRendered.value = false;
  clearPdfSource();

  try {
    const response = await fetchOriginalFile();
    const blob = await response.blob();
    pdfSource.value = URL.createObjectURL(blob);
  } catch (error) {
    pdfError.value = error instanceof Error ? error.message : translateText("PDF 原文档渲染失败");
  } finally {
    isLoadingPdf.value = false;
  }
}

function clearDocxHighlight() {
  return new Promise<void>((resolve) => {
    if (!markInstance) {
      resolve();
      return;
    }
    markInstance.unmark({ done: () => resolve() });
  });
}

async function highlightDocx() {
  await clearDocxHighlight();

  const keyword = props.activeText.trim();
  if (!keyword || !markInstance || !docxHost.value) return;

  await new Promise<void>((resolve) => {
    markInstance?.mark(keyword, {
      acrossElements: true,
      separateWordSearch: false,
      className: "doc-hit",
      done: () => resolve()
    });
  });

  await nextTick();
  docxHost.value.querySelector<HTMLElement>("mark.doc-hit")?.scrollIntoView({
    behavior: "smooth",
    block: "center"
  });
}

watch(
  [() => props.fileUrl, () => fileExt.value],
  async () => {
    pdfRendered.value = false;
    docxError.value = "";
    pdfError.value = "";
    clearPdfSource();

    if (docxHost.value) {
      docxHost.value.innerHTML = "";
    }

    updatePdfSearch();

    if (isPdf.value && props.fileUrl) {
      await loadPdfFile();
      return;
    }

    if (isDocx.value && props.fileUrl) {
      await nextTick();
      await renderDocxFile();
    }
  },
  { immediate: true }
);

watch(
  () => props.activeText,
  async (value) => {
    if (isPdf.value) {
      if (!pdfRendered.value) return;
      updatePdfSearch();
      return;
    }

    if (isDocx.value && docxHost.value) {
      await highlightDocx();
    }
  }
);

onBeforeUnmount(() => {
  clear();
  clearPdfSource();
  if (docxHost.value) {
    docxHost.value.innerHTML = "";
  }
});
</script>

<template>
  <article class="original-pane">
    <header>{{ title }}</header>

    <div v-if="isPdf" class="original-pane__viewer original-pane__viewer--pdf">
      <div v-if="isLoadingPdf" class="original-pane__empty">{{ translateText("正在加载 PDF 原文档...") }}</div>
      <div v-else-if="pdfError" class="original-pane__empty">
        <p>{{ pdfError }}</p>
        <p class="original-pane__hint">{{ translateText("请确认后端已启用原文件接口，必要时重启当前开发服务。") }}</p>
      </div>
      <VuePdfEmbed
        v-else
        :find-controller="findController"
        annotation-layer
        text-layer
        :source="pdfSource"
        @rendered="pdfRendered = true; updatePdfSearch()"
      />
    </div>

    <div v-else-if="isDocx" class="original-pane__viewer original-pane__viewer--docx">
      <div v-if="isRenderingDocx" class="original-pane__empty">{{ translateText("正在渲染 Word 原文档...") }}</div>
      <div v-else-if="docxError" class="original-pane__empty">{{ docxError }}</div>
      <div ref="docxHost" class="docx-host" :class="{ 'is-hidden': isRenderingDocx || Boolean(docxError) }" />
    </div>

    <div v-else class="original-pane__empty">
      {{ translateText("当前格式暂不支持原样渲染，请下载原文件查看。") }}
    </div>
  </article>
</template>
