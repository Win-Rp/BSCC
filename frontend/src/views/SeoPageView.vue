<template>
  <section class="single-view seo-page">
    <el-card shadow="never" class="glass-card seo-hero-card">
      <div class="seo-hero-card__eyebrow">{{ page.eyebrow }}</div>
      <h1 class="seo-hero-card__title">{{ page.h1 }}</h1>
      <p class="seo-hero-card__intro">{{ page.intro }}</p>

      <div class="seo-chip-list">
        <span v-for="chip in page.chips" :key="chip" class="seo-chip-list__item">{{ chip }}</span>
      </div>

      <div class="seo-action-row">
        <el-button type="primary" size="large" @click="router.push(page.primaryCta.to)">
          {{ page.primaryCta.label }}
        </el-button>
        <el-button v-if="page.secondaryCta" size="large" plain @click="router.push(page.secondaryCta.to)">
          {{ page.secondaryCta.label }}
        </el-button>
      </div>
    </el-card>

    <el-card
      v-if="page.cardSection"
      shadow="never"
      class="glass-card seo-section-card"
    >
      <div class="seo-section-head">
        <span class="section-eyebrow">{{ t("seo.keyPoints") }}</span>
        <h2>{{ page.cardSection.title }}</h2>
      </div>
      <div class="seo-card-grid" :class="gridClass(page.cardSection.columns)">
        <article
          v-for="item in page.cardSection.items"
          :key="item.title"
          class="seo-info-card"
        >
          <strong>{{ item.title }}</strong>
          <p>{{ item.text }}</p>
        </article>
      </div>
    </el-card>

    <div v-if="page.textSections?.length" class="seo-text-stack">
      <el-card
        v-for="section in page.textSections"
        :key="section.title"
        shadow="never"
        class="glass-card seo-section-card"
      >
        <div class="seo-section-head">
          <span class="section-eyebrow">{{ t("seo.insight") }}</span>
          <h2>{{ section.title }}</h2>
        </div>
        <div class="seo-paragraph-stack">
          <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
        </div>
      </el-card>
    </div>

    <el-card
      v-if="page.stepSection"
      shadow="never"
      class="glass-card seo-section-card"
    >
      <div class="seo-section-head">
        <span class="section-eyebrow">{{ t("seo.workflow") }}</span>
        <h2>{{ page.stepSection.title }}</h2>
      </div>
      <div class="seo-step-grid">
        <article v-for="(step, index) in page.stepSection.items" :key="step.title" class="seo-step-card">
          <div class="seo-step-card__index">{{ String(index + 1).padStart(2, "0") }}</div>
          <div class="seo-step-card__body">
            <h3>{{ step.title }}</h3>
            <p>{{ step.text }}</p>
          </div>
        </article>
      </div>
    </el-card>

    <el-card
      v-if="page.faqSection"
      shadow="never"
      class="glass-card seo-section-card"
    >
      <div class="seo-section-head">
        <span class="section-eyebrow">{{ t("seo.faq") }}</span>
        <h2>{{ page.faqSection.title }}</h2>
      </div>
      <div class="seo-faq-list">
        <article v-for="faq in page.faqSection.items" :key="faq.question" class="seo-faq-item">
          <h3>{{ faq.question }}</h3>
          <p>{{ faq.answer }}</p>
        </article>
      </div>
    </el-card>

    <el-card
      v-if="page.relatedSection"
      shadow="never"
      class="glass-card seo-section-card"
    >
      <div class="seo-section-head">
        <span class="section-eyebrow">{{ t("seo.related") }}</span>
        <h2>{{ page.relatedSection.title }}</h2>
      </div>
      <div class="seo-card-grid seo-card-grid--three">
        <article
          v-for="link in page.relatedSection.items"
          :key="link.to"
          class="seo-link-card"
          @click="router.push(link.to)"
        >
          <strong>{{ link.title }}</strong>
          <p>{{ link.text }}</p>
          <span class="seo-link-card__cta">{{ t("seo.viewPage") }}</span>
        </article>
      </div>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useHead } from "@unhead/vue";
import { useRoute, useRouter } from "vue-router";
import { useAppI18n } from "@/composables/useAppI18n";
import { getSeoPage } from "@/content/seoPages";
import { createHeadConfig, resolveRouteSeo } from "@/utils/seo";

const route = useRoute();
const router = useRouter();
const { t } = useAppI18n();

const page = computed(() => getSeoPage(String(route.name || "home")));
const routeSeo = computed(() =>
  createHeadConfig(resolveRouteSeo(page.value.seo, { currentPath: route.path }))
);

useHead(() => routeSeo.value as any);

function gridClass(columns?: number) {
  if (columns === 4) return "seo-card-grid--four";
  if (columns === 2) return "seo-card-grid--two";
  return "seo-card-grid--three";
}
</script>

<style scoped>
.seo-page {
  gap: 18px;
}

.seo-hero-card__eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.06);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.seo-hero-card__title {
  margin: 16px 0 14px;
  font-size: clamp(32px, 4.8vw, 52px);
  line-height: 1.08;
}

.seo-hero-card__intro {
  max-width: 980px;
  font-size: 16px;
  line-height: 1.9;
}

.seo-chip-list,
.seo-action-row,
.seo-card-grid,
.seo-step-grid,
.seo-faq-list,
.seo-paragraph-stack,
.seo-text-stack {
  display: grid;
  gap: 16px;
}

.seo-chip-list {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20px;
}

.seo-chip-list__item {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.7);
  color: var(--ink);
  font-size: 13px;
}

.seo-action-row {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20px;
}

.seo-section-head {
  margin-bottom: 18px;
}

.seo-section-head h2 {
  margin: 8px 0 0;
  font-size: 28px;
  line-height: 1.2;
}

.seo-card-grid--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.seo-card-grid--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.seo-card-grid--four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.seo-info-card,
.seo-faq-item,
.seo-link-card,
.seo-step-card {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.74);
}

.seo-info-card,
.seo-faq-item,
.seo-link-card {
  padding: 20px;
}

.seo-info-card strong,
.seo-link-card strong {
  display: block;
  margin-bottom: 10px;
  font-size: 18px;
}

.seo-paragraph-stack p + p {
  margin-top: 12px;
}

.seo-step-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.seo-step-card {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 18px;
  padding: 22px;
}

.seo-step-card__index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: #111;
  color: #fff;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.seo-step-card__body h3,
.seo-faq-item h3 {
  margin: 0 0 10px;
  font-size: 18px;
}

.seo-link-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.seo-link-card:hover {
  transform: translateY(-2px);
  border-color: var(--line-strong);
  box-shadow: 0 12px 32px rgba(17, 17, 17, 0.06);
}

.seo-link-card__cta {
  display: inline-flex;
  margin-top: 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
}

@media (max-width: 1180px) {
  .seo-card-grid--four,
  .seo-card-grid--three {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .seo-card-grid--two,
  .seo-card-grid--three,
  .seo-card-grid--four,
  .seo-step-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .seo-step-card {
    grid-template-columns: 56px minmax(0, 1fr);
    padding: 18px;
  }

  .seo-step-card__index {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    font-size: 18px;
  }

  .seo-section-head h2 {
    font-size: 24px;
  }
}
</style>
