<template>
  <section class="single-view docs-view">
    <el-card shadow="never" class="glass-card docs-hero">
      <div class="docs-hero__eyebrow">使用说明</div>
      <div class="docs-hero__body">
        <div class="docs-hero__content">
          <h1>用户端文档中心</h1>
          <p>
            这份文档只讲如何使用系统完成标书查重，不涉及安装、部署或后台配置。
            你可以按“上传文件 -> 等待处理 -> 查看结果 -> 进入对比 -> 按需解锁详情 -> 凭任务号找回结果”的顺序完成整套操作。
          </p>
        </div>
        <div class="docs-hero__chips">
          <span>无需登录</span>
          <span>支持 DOCX / PDF</span>
          <span>B 文件支持 1-10 份</span>
          <span>结果保留 7 天</span>
        </div>
      </div>
    </el-card>

    <section class="docs-anchor-nav">
      <a v-for="anchor in anchors" :key="anchor.id" class="docs-anchor-nav__item" :href="`#${anchor.id}`">
        {{ anchor.label }}
      </a>
    </section>

    <div class="docs-layout">
      <main class="docs-main">
        <el-card id="quick-start" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Quick Start</span>
              <h2>三分钟快速上手</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--four">
            <article class="docs-mini-card">
              <strong>1. 准备文件</strong>
              <p>上传 1 份主标书 A，再上传 1-10 份对比标书 B。当前支持 `DOCX` 与可复制文本的 `PDF`。</p>
            </article>
            <article class="docs-mini-card">
              <strong>2. 可选填关键字</strong>
              <p>在关键字输入框中输入词语后按回车添加，适合排查围标词、独家授权词和敏感表述。</p>
            </article>
            <article class="docs-mini-card">
              <strong>3. 发起查重</strong>
              <p>点击“开始智能查重”后系统自动进入处理流程，请保存任务号，便于稍后找回结果。</p>
            </article>
            <article class="docs-mini-card">
              <strong>4. 查看与复核</strong>
              <p>先在结果页看排行与风险摘要，再进入对比页逐段核验；多份 B 文件可按需支付解锁完整详情。</p>
            </article>
          </div>
        </el-card>

        <el-card id="prepare" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Before You Start</span>
              <h2>使用前需要知道什么</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--two">
            <article class="docs-info-card">
              <h3>A 文件与 B 文件的含义</h3>
              <p>`A` 是你的主标书，也就是需要自查风险的那一份文件。</p>
              <p>`B` 是用于比对的参考标书。上传 1 份时属于单份对比；上传 2-10 份时属于 1 对多查重。</p>
            </article>
            <article class="docs-info-card">
              <h3>文件与关键字要求</h3>
              <p>系统当前支持 `DOCX` 和可复制文本的 `PDF`。如果 PDF 本身无法选中文本，可能无法得到理想结果。</p>
              <p>关键字不是必填项；如果你有重点排查对象，建议按词逐个输入并回车保存。</p>
            </article>
            <article class="docs-info-card">
              <h3>单份与多份的区别</h3>
              <p>单份 B 文件查重完成后可以直接查看完整详情。</p>
              <p>多份 B 文件会先返回排行、摘要和免费预览；如需查看全部明细，需要按当前任务生成订单后解锁。</p>
            </article>
            <article class="docs-info-card">
              <h3>任务号很重要</h3>
              <p>每次查重都会生成一个以 `T` 开头的任务号。系统会在处理页和结果页展示它。</p>
              <p>请及时复制保存，结果保留 7 天，后续找回历史结果时会直接用到。</p>
            </article>
          </div>
        </el-card>

        <el-card id="workflow" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Workflow</span>
              <h2>标准使用流程</h2>
            </div>
          </div>
          <div class="docs-steps">
            <article v-for="step in steps" :key="step.index" class="docs-step-card">
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
              <span class="section-eyebrow">Pages</span>
              <h2>各页面分别做什么</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--three">
            <article class="docs-page-card">
              <h3>上传工作台</h3>
              <p>负责选择 A、B 文件和输入关键字，是每次发起新任务的入口。</p>
              <p>右上角还有“找回历史任务结果”，输入任务号即可恢复旧任务。</p>
            </article>
            <article class="docs-page-card">
              <h3>结果总览</h3>
              <p>展示查重排行、风险摘要、图表和重复片段预览，是判断哪些文件最需要优先复核的主页面。</p>
              <p>如果是多份 B 文件，支付入口也在这里。</p>
            </article>
            <article class="docs-page-card">
              <h3>对比证据</h3>
              <p>用于左右分屏查看原文，支持切换对比目标、上一处/下一处定位，以及抽屉浏览全部重复片段。</p>
              <p>适合在最终提交前逐条核验风险点。</p>
            </article>
          </div>
        </el-card>

        <el-card id="results" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Result Guide</span>
              <h2>结果页应该怎么看</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--two">
            <article class="docs-info-card">
              <h3>查重排行</h3>
              <p>每一行对应 1 份 B 文件，按总相似度和风险摘要展示。你可以先从相似度高、风险等级高的文件开始看。</p>
              <p>点击表格行或“查看”按钮，可以切换当前选中的比对结果。</p>
            </article>
            <article class="docs-info-card">
              <h3>重复片段摘录</h3>
              <p>结果页会展示重复片段预览。单份 B 文件可直接查看完整明细；多份 B 文件未解锁时只能先看免费预览。</p>
              <p>若需要更细致的逐段核验，建议进入对比页查看原文证据。</p>
            </article>
            <article class="docs-info-card">
              <h3>格式相似项与元数据对比</h3>
              <p>格式相似项用于观察文档结构是否接近，例如句子数量、段落数量等统计结果。</p>
              <p>元数据对比用于观察作者、创建信息等文档属性是否存在可疑一致性。</p>
            </article>
            <article class="docs-info-card">
              <h3>关键字命中</h3>
              <p>如果你在上传阶段输入了关键字，结果页会返回命中详情，并标明命中段落与句子位置。</p>
              <p>这部分适合用来排查敏感词、指定条款或固定短语。</p>
            </article>
          </div>
          <div class="docs-tip-strip">
            <article class="docs-tip-card">
              <strong>完全重复</strong>
              <p>通常表示文本高度一致，建议优先处理。</p>
            </article>
            <article class="docs-tip-card">
              <strong>改写相似</strong>
              <p>通常表示表达方式有调整，但语义与结构仍然接近。</p>
            </article>
            <article class="docs-tip-card">
              <strong>风险摘要</strong>
              <p>适合快速筛查问题文件，再决定是否进入原文对比。</p>
            </article>
          </div>
        </el-card>

        <el-card id="payment" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Unlock Detail</span>
              <h2>什么时候需要支付解锁</h2>
            </div>
          </div>
          <div class="docs-highlight-card">
            <h3>单份 B 文件</h3>
            <p>单份对比任务完成后，可直接查看完整详情和原文对比，无需额外解锁。</p>
          </div>
          <div class="docs-highlight-card docs-highlight-card--warn">
            <h3>2-10 份 B 文件</h3>
            <p>系统会先给出总体排行、风险摘要、图表和免费重复片段预览；如果你要查看全部重复片段、格式相似项、元数据对比和关键字命中详情，需要在结果页打开支付窗口解锁当前任务。</p>
          </div>
          <div class="docs-grid docs-grid--three">
            <article class="docs-page-card">
              <h3>如何发起解锁</h3>
              <p>在结果页点击“立即支付解锁”，填写联系方式后生成订单。</p>
            </article>
            <article class="docs-page-card">
              <h3>如何完成支付</h3>
              <p>系统会生成支付宝或微信扫码二维码，付款后会自动轮询支付状态，也可手动点击校验。</p>
            </article>
            <article class="docs-page-card">
              <h3>解锁后能看什么</h3>
              <p>解锁后会开放当前任务下全部 B 文件的完整详情，并可继续进入对比页逐条核验。</p>
            </article>
          </div>
        </el-card>

        <el-card id="compare" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Compare</span>
              <h2>如何使用对比页复核证据</h2>
            </div>
          </div>
          <div class="docs-grid docs-grid--two">
            <article class="docs-info-card">
              <h3>切换对比目标</h3>
              <p>当任务中有多份 B 文件时，可以在顶部下拉框里切换不同的对比文件，逐个核验风险。</p>
            </article>
            <article class="docs-info-card">
              <h3>定位重复片段</h3>
              <p>点击“上一处 / 下一处”可以在命中片段之间跳转；打开右侧抽屉后，也可以直接点选某一处重复。</p>
            </article>
            <article class="docs-info-card">
              <h3>左右原文同步查看</h3>
              <p>页面会同时显示 A、B 两份原文，并围绕当前命中片段做高亮和滚动定位，方便判断是否需要修改。</p>
            </article>
            <article class="docs-info-card">
              <h3>适合什么时候用</h3>
              <p>当你已经从结果页锁定高风险文件，或者要给团队、法务、商务同事做复核说明时，对比页最直观。</p>
            </article>
          </div>
        </el-card>

        <el-card id="recover" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">Recover</span>
              <h2>如何找回历史任务结果</h2>
            </div>
          </div>
          <div class="docs-recover-card">
            <div class="docs-recover-card__badge">任务号找回</div>
            <p>
              回到上传工作台，点击“找回历史任务结果”，输入以 `T` 开头的任务号后即可重新进入结果页。
              系统默认保留结果 7 天，因此建议在发起任务后立即复制并保存任务号。
            </p>
          </div>
          <div class="docs-grid docs-grid--three">
            <article class="docs-page-card">
              <h3>处理时间较长怎么办</h3>
              <p>处理中页面会提示你复制任务号。你可以先离开页面，稍后再凭任务号回来查看。</p>
            </article>
            <article class="docs-page-card">
              <h3>多份任务未支付怎么办</h3>
              <p>只要任务仍在保留期内，你重新进入结果页后仍可看到免费预览和支付入口。</p>
            </article>
            <article class="docs-page-card">
              <h3>已经完成支付怎么办</h3>
              <p>在保留期内重新找回任务后，已解锁的完整详情仍然可以继续查看。</p>
            </article>
          </div>
        </el-card>

        <el-card id="faq" shadow="never" class="glass-card docs-section">
          <div class="docs-section__head">
            <div>
              <span class="section-eyebrow">FAQ</span>
              <h2>常见问题</h2>
            </div>
          </div>
          <div class="docs-faq-list">
            <article class="docs-faq-item" v-for="faq in faqs" :key="faq.question">
              <h3>{{ faq.question }}</h3>
              <p>{{ faq.answer }}</p>
            </article>
          </div>
        </el-card>
      </main>

      <aside class="docs-side">
        <el-card shadow="never" class="glass-card docs-side-card">
          <span class="section-eyebrow">Tips</span>
          <h3>使用建议</h3>
          <div class="docs-side-list">
            <article v-for="tip in sideTips" :key="tip.title" class="docs-side-list__item">
              <strong>{{ tip.title }}</strong>
              <p>{{ tip.text }}</p>
            </article>
          </div>
        </el-card>

        <el-card shadow="never" class="glass-card docs-side-card">
          <span class="section-eyebrow">Support</span>
          <h3>需要帮助时</h3>
          <p>页面右下角提供微信与邮箱悬浮入口。遇到文件解析、结果理解或支付问题时，可直接联系支持人员。</p>
        </el-card>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useHead } from "@unhead/vue";
import { createHeadConfig, resolveRouteSeo } from "@/utils/seo";

useHead(
  createHeadConfig(
    resolveRouteSeo(
      {
        title: "标书查重使用说明_结果解读与对比证据查看_{siteTitle}",
        description:
          "查看标书查重使用说明，了解如何上传投标文件、阅读结果总览、使用对比证据页面和找回历史任务结果。",
        keywords: ["标书查重使用说明", "标书结果怎么看", "投标文件对比说明"],
        jsonLd: {
          "@context": "https://schema.org",
          "@type": "FAQPage",
          mainEntity: [
            {
              "@type": "Question",
              name: "为什么我只能看到预览，看不到完整详情？",
              acceptedAnswer: {
                "@type": "Answer",
                text: "当任务上传了 2-10 份 B 文件时，系统会先展示免费预览，解锁后可查看完整详情。"
              }
            },
            {
              "@type": "Question",
              name: "任务处理中可以关闭页面吗？",
              acceptedAnswer: {
                "@type": "Answer",
                text: "可以，建议先保存任务号，随后可凭任务号找回结果。"
              }
            }
          ]
        }
      },
      { currentPath: "/docs" }
    )
  ) as any
);

const anchors = [
  { id: "quick-start", label: "快速上手" },
  { id: "prepare", label: "使用前准备" },
  { id: "workflow", label: "使用流程" },
  { id: "results", label: "结果说明" },
  { id: "payment", label: "支付解锁" },
  { id: "recover", label: "任务找回" },
  { id: "faq", label: "常见问题" }
];

const steps = [
  {
    index: "01",
    title: "上传主标书 A 与对比标书 B",
    description: "A 文件只能上传 1 份，B 文件可上传 1-10 份。准备完毕后，如有需要可继续补充关键字。"
  },
  {
    index: "02",
    title: "输入关键字并发起智能查重",
    description: "关键字输入后按回车即可添加。点击“开始智能查重”后系统会自动创建任务并跳转到结果页。"
  },
  {
    index: "03",
    title: "等待处理并保存任务号",
    description: "任务处理中会显示任务号。查重耗时较长时，你可以先复制任务号离开，稍后再回来查看。"
  },
  {
    index: "04",
    title: "先看结果总览，再锁定高风险文件",
    description: "优先查看查重排行、总相似度、风险摘要和重复片段预览，找到最需要复核的 B 文件。"
  },
  {
    index: "05",
    title: "按需解锁完整详情",
    description: "单份 B 文件可直接看全量详情；多份 B 文件则先看预览，需要时再在结果页打开支付窗口完成解锁。"
  },
  {
    index: "06",
    title: "进入对比页逐条核验",
    description: "在对比页中切换文件、定位命中片段、查看左右原文高亮证据，辅助你进行最终修改与确认。"
  }
];

const faqs = [
  {
    question: "为什么我只能看到预览，看不到完整详情？",
    answer: "通常是因为当前任务上传了 2-10 份 B 文件，系统按照 1 对多模式先展示免费预览。完成解锁后即可查看完整详情。"
  },
  {
    question: "为什么上传后提示文件暂不支持？",
    answer: "当前只支持 DOCX 和可复制文本的 PDF。如果 PDF 无法选中文本，系统可能无法正常解析。"
  },
  {
    question: "任务处理中可以关闭页面吗？",
    answer: "可以。请先复制保存任务号，之后通过“找回历史任务结果”重新进入即可。"
  },
  {
    question: "关键字一定要填吗？",
    answer: "不是必填。只有你需要额外排查某些词语、条款或敏感表述时，才建议填写。"
  },
  {
    question: "结果会保留多久？",
    answer: "系统默认保留 7 天。保留期内可凭任务号找回结果；若已完成解锁，完整详情也会继续保留。"
  }
];

const sideTips = [
  {
    title: "先保任务号",
    text: "任务号是找回结果的唯一入口之一，建议在处理中就先复制保存。"
  },
  {
    title: "先看高风险",
    text: "结果页先按总相似度和风险摘要筛一轮，再进入对比页，效率会更高。"
  },
  {
    title: "关键字要精确",
    text: "关键字越聚焦，后续命中结果越容易解释和复核。"
  }
];
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
