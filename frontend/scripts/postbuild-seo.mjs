import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const DIST_DIR = path.resolve("dist");
const SITE_URL = "https://biaoshu.mxitx.com";
const DEFAULT_SITE_TITLE = "标书查重系统";

const pages = [
  {
    file: "index.html",
    routePath: "/",
    title: `${DEFAULT_SITE_TITLE}_投标文件相似度检测_围标风险排查平台`,
    description:
      "提供标书查重、投标文件检查、围标风险排查、改写相似识别与原文证据对比，支持 DOCX 与可复制文本 PDF，适合工程企业与乙方商务团队快速复核投标文件。",
    keywords: "标书查重,投标文件查重,标书检查,标书合规,围标风险排查,标书相似度检测",
    jsonLd: [
      {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        name: DEFAULT_SITE_TITLE,
        applicationCategory: "BusinessApplication",
        operatingSystem: "Web",
        url: `${SITE_URL}/`,
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "CNY",
          description: "支持基础免费查重与结果预览"
        }
      },
      {
        "@context": "https://schema.org",
        "@type": "Organization",
        name: DEFAULT_SITE_TITLE,
        url: `${SITE_URL}/`
      }
    ]
  },
  {
    file: "upload.html",
    routePath: "/upload",
    title: `标书查重工具入口_上传投标文件开始检查_${DEFAULT_SITE_TITLE}`,
    description:
      "上传主标书 A 与对比标书 B，开始标书查重、标书检查和围标风险排查，支持 DOCX 与可复制文本 PDF。",
    keywords: "标书查重入口,投标文件查重,标书检查工具,围标风险排查"
  },
  {
    file: "free.html",
    routePath: "/free",
    title: `免费标书查重入口_DOCX/PDF 标书检测与结果预览_${DEFAULT_SITE_TITLE}`,
    description:
      "免费标书查重入口，支持 DOCX 与可复制文本 PDF 上传，可先查看投标文件相似度排行、风险摘要与重复片段预览，适合工程企业和商务团队做首轮复核。",
    keywords: "免费标书查重,免费投标文件查重,标书免费检测,投标文件相似度预览"
  },
  {
    file: "check.html",
    routePath: "/check",
    title: `标书检查工具_快速排查重复内容与风险表述_${DEFAULT_SITE_TITLE}`,
    description:
      "标书检查工具不仅看重复内容，还结合关键字命中、格式相似项、元数据和原文证据对比，适合工程企业与乙方商务团队在投标前做快速复核。",
    keywords: "标书检查,投标文件检查,标书风险检查,标书复核工具"
  },
  {
    file: "compliance.html",
    routePath: "/compliance",
    title: `标书合规检查辅助工具_排查相似内容与高风险表达_${DEFAULT_SITE_TITLE}`,
    description:
      "标书合规检查辅助工具，结合标书查重、关键字命中、结构相似性和原文证据对比，帮助团队在投标前开展更有针对性的合规复核。",
    keywords: "标书合规,标书合规检查,投标文件合规,标书审查辅助"
  },
  {
    file: "solutions/engineering.html",
    routePath: "/solutions/engineering",
    title: `工程企业标书查重方案_投标文件相似度与围标风险排查_${DEFAULT_SITE_TITLE}`,
    description:
      "面向工程企业的标书查重方案，适合在技术标、商务标和历史版本汇总后进行相似度排查、关键字检查和原文证据复核，降低投标前风险。",
    keywords: "工程企业标书查重,工程标书检查,投标文件相似度排查,围标风险检测"
  },
  {
    file: "solutions/business-team.html",
    routePath: "/solutions/business-team",
    title: `乙方销售与商务团队标书检查工具_投标文件快速复核_${DEFAULT_SITE_TITLE}`,
    description:
      "面向乙方销售和商务团队的标书检查工具，适合在汇总多个版本、代理稿和合作方资料后，快速完成标书查重、风险筛查和原文证据复核。",
    keywords: "商务团队标书检查,乙方投标文件检查,商务标书查重,投标文件复核"
  },
  {
    file: "guides/biaoshu-chachong.html",
    routePath: "/guides/biaoshu-chachong",
    title: `标书查重是什么意思_投标文件查重怎么用_${DEFAULT_SITE_TITLE}`,
    description:
      "了解标书查重是什么意思、适合哪些场景、和普通文章查重有什么区别，以及工程企业和商务团队如何使用标书查重系统完成首轮筛查与证据复核。",
    keywords: "标书查重是什么意思,投标文件查重,标书查重怎么用",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: "标书查重是什么意思",
      about: ["标书查重", "投标文件查重"]
    }
  },
  {
    file: "guides/biaoshu-check.html",
    routePath: "/guides/biaoshu-check",
    title: `标书检查一般检查什么_投标文件复核重点_${DEFAULT_SITE_TITLE}`,
    description:
      "了解标书检查一般检查什么，包括重复内容、改写相似、关键字命中、结构相似项和原文证据，适合工程企业与商务团队建立高效复核流程。",
    keywords: "标书检查一般检查什么,投标文件检查重点,标书复核",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: "标书检查一般检查什么",
      about: ["标书检查", "投标文件复核"]
    }
  },
  {
    file: "guides/similarity-risk.html",
    routePath: "/guides/similarity-risk",
    title: `投标文件相似度高怎么办_标书高风险处理建议_${DEFAULT_SITE_TITLE}`,
    description:
      "当投标文件相似度高时，如何通过结果总览、关键字命中和原文证据定位高风险内容，并组织工程团队或商务团队高效修改与复核。",
    keywords: "投标文件相似度高怎么办,标书高风险怎么处理,围标风险排查",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: "投标文件相似度高怎么办",
      about: ["投标文件相似度", "标书风险处理"]
    }
  },
  {
    file: "docs.html",
    routePath: "/docs",
    title: `标书查重使用说明_结果解读与对比证据查看_${DEFAULT_SITE_TITLE}`,
    description:
      "查看标书查重使用说明，了解如何上传投标文件、阅读结果总览、使用对比证据页面和找回历史任务结果。",
    keywords: "标书查重使用说明,标书结果怎么看,投标文件对比说明",
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
  }
];

function buildHeadTags(page) {
  const canonical = `${SITE_URL}${page.routePath === "/" ? "/" : page.routePath}`;
  const jsonLdArray = page.jsonLd ? (Array.isArray(page.jsonLd) ? page.jsonLd : [page.jsonLd]) : [];
  const jsonLdTags = jsonLdArray
    .map(
      (entry) =>
        `    <script type="application/ld+json">${JSON.stringify(entry)}</script>`
    )
    .join("\n");

  return [
    `    <meta name="description" content="${escapeAttribute(page.description)}">`,
    `    <meta name="keywords" content="${escapeAttribute(page.keywords)}">`,
    '    <meta name="robots" content="index,follow">',
    '    <meta property="og:locale" content="zh_CN">',
    '    <meta property="og:type" content="website">',
    `    <meta property="og:title" content="${escapeAttribute(page.title)}">`,
    `    <meta property="og:description" content="${escapeAttribute(page.description)}">`,
    `    <meta property="og:url" content="${canonical}">`,
    `    <meta name="application-name" content="${DEFAULT_SITE_TITLE}">`,
    `    <link rel="canonical" href="${canonical}">`,
    `    <title>${escapeHtml(page.title)}</title>`,
    jsonLdTags
  ]
    .filter(Boolean)
    .join("\n");
}

function escapeAttribute(value) {
  return value.replaceAll("&", "&amp;").replaceAll('"', "&quot;");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function cleanHead(html) {
  return html
    .replace(/<meta name="description"[^>]*>\s*/g, "")
    .replace(/<meta name="keywords"[^>]*>\s*/g, "")
    .replace(/<meta name="robots"[^>]*>\s*/g, "")
    .replace(/<meta name="application-name"[^>]*>\s*/g, "")
    .replace(/<meta property="og:locale"[^>]*>\s*/g, "")
    .replace(/<meta property="og:type"[^>]*>\s*/g, "")
    .replace(/<meta property="og:title"[^>]*>\s*/g, "")
    .replace(/<meta property="og:description"[^>]*>\s*/g, "")
    .replace(/<meta property="og:url"[^>]*>\s*/g, "")
    .replace(/<link rel="canonical"[^>]*>\s*/g, "")
    .replace(/<title>[\s\S]*?<\/title>\s*/g, "")
    .replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>\s*/g, "");
}

async function patchPage(page) {
  const filePath = path.join(DIST_DIR, page.file);
  let html = await readFile(filePath, "utf8");
  html = cleanHead(html);

  const headTags = buildHeadTags(page);
  html = html.replace(
    /(<meta name="viewport"[^>]*>\s*)/,
    `$1${headTags}\n`
  );

  await writeFile(filePath, html, "utf8");
}

await Promise.all(pages.map(patchPage));
