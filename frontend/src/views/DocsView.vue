<template>
  <section class="single-view docs-view">
    <el-card shadow="never" class="glass-card docs-hero">
      <div class="docs-hero__eyebrow">{{ content.hero.eyebrow }}</div>
      <div class="docs-hero__body">
        <div class="docs-hero__content">
          <h1>{{ content.hero.title }}</h1>
          <p>{{ content.hero.description }}</p>
        </div>
        <div class="docs-hero__chips">
          <span v-for="chip in content.hero.chips" :key="chip">{{ chip }}</span>
        </div>
      </div>
    </el-card>

    <section class="docs-anchor-nav">
      <a v-for="anchor in content.anchors" :key="anchor.id" class="docs-anchor-nav__item" :href="`#${anchor.id}`">
        {{ anchor.label }}
      </a>
    </section>

    <div class="docs-layout">
      <main class="docs-main">
        <el-card id="quick-start" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.quickStart.eyebrow }}</span>
              <h2>{{ content.quickStart.title }}</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--four">
            <article v-for="card in content.quickStart.cards" :key="card.title" class="docs-mini-card">
              <strong>{{ card.title }}</strong>
              <p>{{ card.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="prepare" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.prepare.eyebrow }}</span>
              <h2>{{ content.prepare.title }}</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--two">
            <article v-for="card in content.prepare.cards" :key="card.title" class="docs-info-card">
              <h3>{{ card.title }}</h3>
              <p v-for="line in card.lines" :key="line">{{ line }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="workflow" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.workflow.eyebrow }}</span>
              <h2>{{ content.workflow.title }}</h2>
            </div>
          </div>
          <div class="docs-steps">
            <article v-for="step in content.workflow.steps" :key="step.index" class="docs-step-card">
              <div class="docs-step-card__index">{{ step.index }}</div>
              <div class="docs-step-card__body">
                <h3>{{ step.title }}</h3>
                <p>{{ step.description }}</p>
              </div>
            </article>
          </div>
        </el-card>

        <el-card id="pages" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.pages.eyebrow }}</span>
              <h2>{{ content.pages.title }}</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--three">
            <article v-for="card in content.pages.cards" :key="card.title" class="docs-page-card">
              <h3>{{ card.title }}</h3>
              <p v-for="line in card.lines" :key="line">{{ line }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="results" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.results.eyebrow }}</span>
              <h2>{{ content.results.title }}</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--two">
            <article v-for="card in content.results.cards" :key="card.title" class="docs-info-card">
              <h3>{{ card.title }}</h3>
              <p v-for="line in card.lines" :key="line">{{ line }}</p>
            </article>
          </div>
          <div class="docs-tip-strip">
            <article v-for="tip in content.results.tips" :key="tip.title" class="docs-tip-card">
              <strong>{{ tip.title }}</strong>
              <p>{{ tip.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="payment" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.payment.eyebrow }}</span>
              <h2>{{ content.payment.title }}</h2>
            </div>
          </div>
          <div
            v-for="highlight in content.payment.highlights"
            :key="highlight.title"
            class="docs-highlight-card"
            :class="{ 'docs-highlight-card--warn': highlight.warn }"
          >
            <h3>{{ highlight.title }}</h3>
            <p>{{ highlight.text }}</p>
          </div>
          <div class="docs-grid docs-grid--three">
            <article v-for="card in content.payment.cards" :key="card.title" class="docs-page-card">
              <h3>{{ card.title }}</h3>
              <p>{{ card.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="compare" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.compare.eyebrow }}</span>
              <h2>{{ content.compare.title }}</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--two">
            <article v-for="card in content.compare.cards" :key="card.title" class="docs-info-card">
              <h3>{{ card.title }}</h3>
              <p>{{ card.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="recover" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.recover.eyebrow }}</span>
              <h2>{{ content.recover.title }}</h2>
            </div>
          </div>
          <div class="docs-recover-card">
            <div class="docs-recover-card__badge">{{ content.recover.badge }}</div>
            <p>{{ content.recover.description }}</p>
          </div>
          <div class="docs-grid docs-grid--three">
            <article v-for="card in content.recover.cards" :key="card.title" class="docs-page-card">
              <h3>{{ card.title }}</h3>
              <p>{{ card.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card id="faq" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">{{ content.faq.eyebrow }}</span>
              <h2>{{ content.faq.title }}</h2>
            </div>
          </div>
          <div class="docs-faq-list">
            <article class="docs-faq-item" v-for="faq in content.faq.items" :key="faq.question">
              <h3>{{ faq.question }}</h3>
              <p>{{ faq.answer }}</p>
            </article>
          </div>
        </el-card>
      </main>

      <aside class="docs-side">
        <el-card shadow="never" class="glass-card docs-side-card">
          <span class="section-eyebrow">{{ content.side.tipsEyebrow }}</span>
          <h3>{{ content.side.tipsTitle }}</h3>
          <div class="docs-side-list">
            <article v-for="tip in content.side.tips" :key="tip.title" class="docs-side-list__item">
              <strong>{{ tip.title }}</strong>
              <p>{{ tip.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card shadow="never" class="glass-card docs-side-card">
          <span class="section-eyebrow">{{ content.side.supportEyebrow }}</span>
          <h3>{{ content.side.supportTitle }}</h3>
          <p>{{ content.side.supportText }}</p>
        </el-card>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useHead } from "@unhead/vue";
import { useAppI18n } from "@/composables/useAppI18n";
import { getDocsPageContent } from "@/content/docsPageContent";
import { createHeadConfig, resolveRouteSeo } from "@/utils/seo";

const { locale } = useAppI18n();
const content = computed(() => getDocsPageContent(locale.value));

useHead(() => createHeadConfig(resolveRouteSeo(content.value.seo, { currentPath: "/docs" })) as any);
</script>

<style scoped>
.docs-view {
  gap: 20px;
}

.docs-hero {
  overflow: hidden;
}

.docs-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.06);
  color: var(--ink);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.docs-hero__body {
  display: grid;
  gap: 24px;
  margin-top: 18px;
}

.docs-hero__content h1 {
  margin: 0 0 12px;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.1;
}

.docs-hero__content p {
  max-width: 860px;
  font-size: 15px;
  line-height: 1.9;
}

.docs-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.docs-hero__chips span,
.docs-anchor-nav__item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
}

.docs-anchor-nav {
  position: sticky;
  top: 18px;
  z-index: 8;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.docs-anchor-nav__item {
  font-size: 13px;
  color: var(--muted);
  transition: all 0.2s ease;
}

.docs-anchor-nav__item:hover {
  color: var(--ink);
  border-color: var(--line-strong);
  transform: translateY(-1px);
}

.docs-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
}

.docs-main,
.docs-side,
.docs-steps,
.docs-grid,
.docs-faq-list,
.docs-side-list {
  display: grid;
  gap: 16px;
}

.docs-section {
  scroll-margin-top: 88px;
}

.docs-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.docs-section__head h2 {
  margin: 6px 0 0;
  font-size: 26px;
  line-height: 1.2;
}

.docs-grid--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.docs-grid--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.docs-grid--four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.docs-mini-card,
.docs-info-card,
.docs-page-card,
.docs-tip-card,
.docs-faq-item,
.docs-side-list__item,
.docs-step-card,
.docs-highlight-card,
.docs-recover-card {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
}

.docs-mini-card,
.docs-info-card,
.docs-page-card,
.docs-tip-card,
.docs-faq-item,
.docs-side-list__item,
.docs-highlight-card,
.docs-recover-card {
  padding: 20px;
}

.docs-mini-card strong,
.docs-tip-card strong,
.docs-side-list__item strong {
  display: block;
  margin-bottom: 10px;
  font-size: 16px;
  color: var(--ink);
}

.docs-info-card h3,
.docs-page-card h3,
.docs-faq-item h3,
.docs-highlight-card h3 {
  margin: 0 0 10px;
  font-size: 18px;
}

.docs-mini-card p,
.docs-info-card p,
.docs-page-card p,
.docs-tip-card p,
.docs-faq-item p,
.docs-side-list__item p,
.docs-highlight-card p,
.docs-recover-card p,
.docs-side-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.docs-info-card,
.docs-page-card {
  min-height: 100%;
}

.docs-steps {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.docs-step-card {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 18px;
  padding: 22px;
}

.docs-step-card__index {
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

.docs-step-card__body h3 {
  margin: 2px 0 10px;
  font-size: 20px;
}

.docs-step-card__body p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.docs-tip-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.docs-highlight-card {
  margin-bottom: 16px;
  background: rgba(17, 17, 17, 0.03);
}

.docs-highlight-card--warn {
  background: rgba(138, 100, 20, 0.08);
  border-color: rgba(138, 100, 20, 0.18);
}

.docs-recover-card {
  position: relative;
  overflow: hidden;
  margin-bottom: 16px;
}

.docs-recover-card__badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  margin-bottom: 12px;
  border-radius: 999px;
  background: #111;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.docs-side {
  position: sticky;
  top: 88px;
  align-content: start;
}

.docs-side-card {
  position: static;
}

.docs-side-list__item + .docs-side-list__item {
  margin-top: 2px;
}

@media (max-width: 1180px) {
  .docs-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .docs-side {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .docs-grid--four,
  .docs-grid--three {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .docs-grid--two,
  .docs-grid--three,
  .docs-grid--four,
  .docs-steps,
  .docs-tip-strip,
  .docs-side {
    grid-template-columns: minmax(0, 1fr);
  }

  .docs-anchor-nav {
    top: 12px;
  }

  .docs-step-card {
    grid-template-columns: 56px minmax(0, 1fr);
    padding: 18px;
  }

  .docs-step-card__index {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    font-size: 18px;
  }

  .docs-section__head h2 {
    font-size: 22px;
  }
}
</style>
