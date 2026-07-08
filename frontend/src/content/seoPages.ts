import type { RouteSeoMeta } from "@/utils/seo";
import { localizeDeep } from "@/composables/useAppI18n";

export type SeoPageKey =
  | "home"
  | "free-landing"
  | "check-landing"
  | "compliance-landing"
  | "engineering-solution"
  | "business-solution"
  | "guide-biaoshu-chachong"
  | "guide-biaoshu-check"
  | "guide-similarity-risk";

type CardItem = {
  title: string;
  text: string;
};

type StepItem = {
  title: string;
  text: string;
};

type FaqItem = {
  question: string;
  answer: string;
};

type RelatedItem = {
  title: string;
  text: string;
  to: string;
};

type TextSection = {
  title: string;
  paragraphs: string[];
};

export interface SeoPageDefinition {
  seo: RouteSeoMeta;
  eyebrow: string;
  h1: string;
  intro: string;
  chips: string[];
  primaryCta: { label: string; to: string };
  secondaryCta?: { label: string; to: string };
  cardSection?: { title: string; columns?: 2 | 3 | 4; items: CardItem[] };
  textSections?: TextSection[];
  stepSection?: { title: string; items: StepItem[] };
  faqSection?: { title: string; items: FaqItem[] };
  relatedSection?: { title: string; items: RelatedItem[] };
}

const softwareSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "标书查重系统",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: "https://biaoshu.mxitx.com/",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "CNY",
    description: "支持基础免费查重与结果预览"
  }
};

export const seoPages: Record<SeoPageKey, SeoPageDefinition> = {
  home: {
    seo: {
      title: "{siteTitle}_投标文件相似度检测_围标风险排查平台",
      description:
        "提供标书查重、投标文件检查、围标风险排查、改写相似识别与原文证据对比，支持 DOCX 与可复制文本 PDF，适合工程企业与乙方商务团队快速复核投标文件。",
      keywords: [
        "标书查重",
        "投标文件查重",
        "标书检查",
        "标书合规",
        "围标风险排查",
        "标书相似度检测"
      ],
      jsonLd: [
        softwareSchema,
        {
          "@context": "https://schema.org",
          "@type": "Organization",
          name: "标书查重系统",
          url: "https://biaoshu.mxitx.com/"
        }
      ]
    },
    eyebrow: "Bid SEO Home",
    h1: "标书查重与投标文件风险检查平台",
    intro:
      "面向工程企业和乙方销售/商务团队，支持标书查重、标书检查、围标风险排查、关键字命中与原文证据复核。先上传文档获得结果预览，再按需进入深度比对与支付解锁。",
    chips: ["支持 DOCX / PDF", "多文档 1 对多", "基础免费预览", "任务号 7 天找回"],
    primaryCta: { label: "立即开始查重", to: "/upload" },
    secondaryCta: { label: "查看使用文档", to: "/docs" },
    cardSection: {
      title: "系统能帮助你检查什么",
      columns: 4,
      items: [
        { title: "重复内容排查", text: "识别完全重复、改写相似和语义接近内容，帮助快速锁定高风险段落。" },
        { title: "标书检查辅助", text: "结合关键字命中、格式相似项和元数据对比，辅助完成投标文件复核。" },
        { title: "围标风险提示", text: "通过多文档 1 对多比对，快速筛出相似度高、需优先复核的对比文件。" },
        { title: "原文证据对比", text: "结果页与对比页联动展示命中片段和原文高亮，便于团队协同确认。" }
      ]
    },
    textSections: [
      {
        title: "为什么这个站点更适合标书场景",
        paragraphs: [
          "相比通用查重工具，标书查重更强调多份投标文件之间的相似性、结构接近度、关键字风险和原文证据链。当前系统围绕 A 文件与多份 B 文件的投标比对流程设计，适合真实招投标场景中的预提交自查和团队复核。",
          "对于工程企业和乙方商务团队而言，重点并不只是看一个相似度数字，更需要知道哪些文件最值得优先复核、哪些片段存在高风险、以及哪些证据可以快速反馈给撰写人员修改。"
        ]
      },
      {
        title: "适合哪些团队使用",
        paragraphs: [
          "工程企业可以在最终投标前，对技术标、商务标、历史版本或外部参考文件进行快速比对，提前发现潜在相似风险。",
          "乙方销售和商务团队可以把它作为标书检查辅助工具，在汇总多个版本、代理稿或合作方材料时，用更短时间完成首轮复核。"
        ]
      }
    ],
    stepSection: {
      title: "如何完成一次标书查重",
      items: [
        { title: "上传文档", text: "上传 1 份主标书 A 和 1-10 份对比标书 B，必要时补充关键字。" },
        { title: "等待分析", text: "系统自动创建任务并处理文档，处理中可先保存任务号以便稍后找回。" },
        { title: "查看总览", text: "先看相似度排行、风险摘要、重复片段预览，再决定优先复核哪些文件。" },
        { title: "进入证据对比", text: "打开对比页查看原文证据，高风险任务可按需解锁完整详情。" }
      ]
    },
    faqSection: {
      title: "首页常见问题",
      items: [
        {
          question: "标书查重和普通文章查重有什么区别？",
          answer: "标书查重更关注多文档比对、围标风险、结构相似性和原文证据，而不仅仅是文本重复率。"
        },
        {
          question: "免费标书查重可以看到什么？",
          answer: "当前站点支持基础免费预览，可先查看总体结果、风险摘要和部分重复片段，再决定是否进入完整详情。"
        },
        {
          question: "哪些文件格式可以上传？",
          answer: "支持 DOCX 与可复制文本 PDF。若 PDF 本身无法选中文本，解析效果可能会受到影响。"
        }
      ]
    },
    relatedSection: {
      title: "继续浏览相关页面",
      items: [
        { title: "免费标书查重", text: "查看免费模式下能获得哪些结果与预览。", to: "/free" },
        { title: "标书检查工具", text: "了解标书检查在实际复核中的适用方式。", to: "/check" },
        { title: "标书合规辅助", text: "查看如何用相似性与关键字命中辅助合规复核。", to: "/compliance" }
      ]
    }
  },
  "free-landing": {
    seo: {
      title: "免费标书查重入口_DOCX/PDF 标书检测与结果预览_{siteTitle}",
      description:
        "免费标书查重入口，支持 DOCX 与可复制文本 PDF 上传，可先查看投标文件相似度排行、风险摘要与重复片段预览，适合工程企业和商务团队做首轮复核。",
      keywords: ["免费标书查重", "免费投标文件查重", "标书免费检测", "投标文件相似度预览"],
      jsonLd: softwareSchema
    },
    eyebrow: "Free Check",
    h1: "免费标书查重与结果预览",
    intro:
      "如果你当前处于首轮排查阶段，可以直接从免费标书查重入口开始。系统支持免费上传、免费分析和结果预览，先帮助你判断是否存在明显相似风险，再决定是否进入更细的复核流程。",
    chips: ["免费上传分析", "支持 DOCX / PDF", "先看预览再决策", "适合首轮筛查"],
    primaryCta: { label: "进入免费查重", to: "/upload" },
    secondaryCta: { label: "查看结果说明", to: "/docs#results" },
    cardSection: {
      title: "免费模式下可以获得什么",
      columns: 3,
      items: [
        { title: "相似度排行", text: "快速看到多份 B 文件中哪些文件与主标书更接近，优先锁定高风险对象。" },
        { title: "风险摘要", text: "从完全重复、改写相似和语义接近角度快速了解当前任务的总体情况。" },
        { title: "重复片段预览", text: "先看代表性的命中片段，帮助判断是否值得继续展开深度复核。" }
      ]
    },
    textSections: [
      {
        title: "为什么要强调免费预览",
        paragraphs: [
          "很多团队在正式提交投标文件前，最先需要的是一个低门槛、快速反馈的首轮检查，而不是一上来就进入复杂的人工复核。免费标书查重页面就是为了帮助你先确认整体风险水平。",
          "对于多份标书比对任务，免费预览可以帮助你更快判断哪些文件最值得继续深挖，从而节省商务团队和工程团队的复核时间。"
        ]
      }
    ],
    stepSection: {
      title: "建议使用方式",
      items: [
        { title: "先做首轮筛查", text: "用免费结果先判断风险级别，不必在所有文件上平均分配时间。" },
        { title: "锁定高风险文件", text: "根据相似度排行和片段预览，把精力集中到最值得复核的文档。" },
        { title: "需要时再解锁", text: "若发现明显风险，再进入完整详情和原文证据对比流程。" }
      ]
    },
    faqSection: {
      title: "免费查重常见问题",
      items: [
        {
          question: "免费标书查重是不是完全免费？",
          answer: "当前站点支持基础免费查重和结果预览，完整详情会根据任务模式按需解锁。"
        },
        {
          question: "免费模式适合什么阶段？",
          answer: "适合投标前的首轮筛查、版本汇总后的初步复核，以及判断是否需要进一步深度检查。"
        }
      ]
    },
    relatedSection: {
      title: "相关页面",
      items: [
        { title: "标书检查工具", text: "查看标书检查更适合哪些复核任务。", to: "/check" },
        { title: "工程企业场景", text: "查看工程企业如何使用标书查重。", to: "/solutions/engineering" },
        { title: "什么是标书查重", text: "阅读基础概念指南。", to: "/guides/biaoshu-chachong" }
      ]
    }
  },
  "check-landing": {
    seo: {
      title: "标书检查工具_快速排查重复内容与风险表述_{siteTitle}",
      description:
        "标书检查工具不仅看重复内容，还结合关键字命中、格式相似项、元数据和原文证据对比，适合工程企业与乙方商务团队在投标前做快速复核。",
      keywords: ["标书检查", "投标文件检查", "标书风险检查", "标书复核工具"],
      jsonLd: softwareSchema
    },
    eyebrow: "Bid Check",
    h1: "标书检查工具",
    intro:
      "标书检查不是单看一个重复率数字，而是围绕内容相似性、风险表述、关键字命中、文件结构和原文证据展开的一整套复核过程。当前站点更适合作为团队的标书检查辅助工具，帮助你把复核流程拆得更快、更清晰。",
    chips: ["重复内容检查", "关键字命中", "格式相似项", "原文证据复核"],
    primaryCta: { label: "开始标书检查", to: "/upload" },
    secondaryCta: { label: "查看使用文档", to: "/docs" },
    cardSection: {
      title: "标书检查的重点模块",
      columns: 4,
      items: [
        { title: "文本相似性", text: "定位完全重复、改写相似和语义接近片段，帮助判断是否需要修改正文。" },
        { title: "关键字检查", text: "输入敏感词、风险词和重点条款，辅助检查指定表达是否命中。" },
        { title: "格式与结构", text: "通过句子数量、段落数量等结构指标，辅助发现两份文档是否过于接近。" },
        { title: "原文证据", text: "进入对比页逐段查看 A、B 原文，便于给撰写人员明确反馈。" }
      ]
    },
    textSections: [
      {
        title: "为什么工程团队和商务团队都需要标书检查",
        paragraphs: [
          "工程团队更关心技术内容是否与历史稿、模板稿或合作方稿件存在明显接近；商务团队则更关心整个投标包的交付节奏，希望快速知道哪些版本最值得优先复核。",
          "把标书检查工具嵌入交付前流程，可以降低盲目人工通读的时间成本，让复核更有针对性。"
        ]
      }
    ],
    stepSection: {
      title: "推荐复核顺序",
      items: [
        { title: "先看总览", text: "先用结果总览筛出高风险文件，不在低风险文档上过早投入时间。" },
        { title: "再看关键片段", text: "通过重复片段预览判断问题大致集中在哪些部分。" },
        { title: "最后看原文证据", text: "进入对比页做定点复核，把问题明确反馈给对应撰写人。" }
      ]
    },
    faqSection: {
      title: "标书检查常见问题",
      items: [
        {
          question: "标书检查是不是等于标书查重？",
          answer: "标书查重是标书检查的重要组成部分，但标书检查还会关注关键字、结构、元数据和原文证据。"
        },
        {
          question: "标书检查适合在哪个时间点做？",
          answer: "最适合在投标定稿前、汇总多个版本后，以及提交前的最后一轮复核时使用。"
        }
      ]
    },
    relatedSection: {
      title: "继续浏览",
      items: [
        { title: "标书合规辅助", text: "查看合规复核相关页面。", to: "/compliance" },
        { title: "商务团队场景", text: "查看乙方商务团队如何使用。", to: "/solutions/business-team" },
        { title: "标书检查看什么", text: "阅读检查重点指南。", to: "/guides/biaoshu-check" }
      ]
    }
  },
  "compliance-landing": {
    seo: {
      title: "标书合规检查辅助工具_排查相似内容与高风险表达_{siteTitle}",
      description:
        "标书合规检查辅助工具，结合标书查重、关键字命中、结构相似性和原文证据对比，帮助团队在投标前开展更有针对性的合规复核。",
      keywords: ["标书合规", "标书合规检查", "投标文件合规", "标书审查辅助"],
      jsonLd: softwareSchema
    },
    eyebrow: "Compliance Support",
    h1: "标书合规检查辅助",
    intro:
      "标书合规本身需要结合项目要求、法律法规和内部流程判断，系统不能代替人工审查，但可以通过相似度、关键字、结构和原文证据，为投标前复核提供更高效的辅助信息。",
    chips: ["相似内容辅助排查", "关键字命中提醒", "结构接近度辅助判断", "适合投标前复核"],
    primaryCta: { label: "开始合规辅助检查", to: "/upload" },
    secondaryCta: { label: "阅读使用说明", to: "/docs" },
    cardSection: {
      title: "哪些信息对合规复核更有帮助",
      columns: 3,
      items: [
        { title: "高相似片段", text: "帮助判断是否存在需要重点修改或进一步人工确认的内容段落。" },
        { title: "敏感关键字", text: "可提前录入重点条款、限制性表达和高风险词，查看命中情况。" },
        { title: "证据链对比", text: "在对比页查看原文高亮，减少只凭感觉做判断的模糊性。" }
      ]
    },
    textSections: [
      {
        title: "如何正确理解标书合规页面",
        paragraphs: [
          "这一页强调的是“合规检查辅助”，而不是替代法律、审计或项目复核流程。它更适合做投标前的信息补充和证据收集，帮助团队更快进入重点问题。",
          "对于需要严格控制表述一致性和相似风险的项目，提前结合关键字命中与原文对比做复核，通常比单纯通读更高效。"
        ]
      }
    ],
    stepSection: {
      title: "合规复核建议流程",
      items: [
        { title: "定义重点词", text: "先录入项目中最需要关注的条款词、限制词和风险表达。" },
        { title: "查看风险摘要", text: "先从总体结果判断哪些 B 文件与主标书最接近。" },
        { title: "逐段复核证据", text: "对于命中片段和高相似段落，进入原文对比做最终人工确认。" }
      ]
    },
    faqSection: {
      title: "合规辅助常见问题",
      items: [
        {
          question: "这个页面能直接证明标书是否合规吗？",
          answer: "不能。它提供的是相似性、关键字命中和原文证据等辅助信息，最终仍需团队结合具体要求人工判断。"
        },
        {
          question: "为什么还需要原文对比？",
          answer: "合规复核往往不能只看摘要，需要回到命中片段和上下文，才能更准确地判断风险。"
        }
      ]
    },
    relatedSection: {
      title: "相关页面",
      items: [
        { title: "标书检查工具", text: "查看通用复核工具页。", to: "/check" },
        { title: "工程企业方案", text: "查看工程企业场景说明。", to: "/solutions/engineering" },
        { title: "高相似度怎么办", text: "阅读风险处理指南。", to: "/guides/similarity-risk" }
      ]
    }
  },
  "engineering-solution": {
    seo: {
      title: "工程企业标书查重方案_投标文件相似度与围标风险排查_{siteTitle}",
      description:
        "面向工程企业的标书查重方案，适合在技术标、商务标和历史版本汇总后进行相似度排查、关键字检查和原文证据复核，降低投标前风险。",
      keywords: ["工程企业标书查重", "工程标书检查", "投标文件相似度排查", "围标风险检测"],
      jsonLd: softwareSchema
    },
    eyebrow: "Engineering Solution",
    h1: "面向工程企业的标书查重方案",
    intro:
      "工程企业的标书往往版本多、参与人多、素材来源复杂。当前系统支持多文档 1 对多比对，适合工程企业在提交前集中检查技术标、商务标和历史版本材料，快速找出最需要优先复核的文档。",
    chips: ["适合版本汇总前后", "支持 1 对多比对", "技术标/商务标均可用", "适合提交前自查"],
    primaryCta: { label: "进入工程标书查重", to: "/upload" },
    secondaryCta: { label: "查看结果解读", to: "/docs#results" },
    cardSection: {
      title: "工程企业常见使用场景",
      columns: 3,
      items: [
        { title: "历史版本对比", text: "对技术标和历史稿做快速比对，判断是否存在需要重新改写的接近段落。" },
        { title: "多团队协作稿复核", text: "当多人协作提交材料时，快速发现不同来源内容是否过于接近。" },
        { title: "投标前终审辅助", text: "在最终提交前做一次集中排查，为项目经理和审核人提供问题证据。" }
      ]
    },
    textSections: [
      {
        title: "为什么工程企业需要更快的首轮筛查",
        paragraphs: [
          "工程项目往往交付节奏紧、版本变更频繁，如果把所有复核压力都放在最后一轮人工通读上，成本会非常高。先用标书查重系统把高风险文档筛出来，再做定点复核，效率更高。",
          "对于内容量较大的技术标，系统给出的原文证据和相似片段预览，也更方便项目经理在短时间内判断优先级。"
        ]
      }
    ],
    stepSection: {
      title: "工程企业推荐流程",
      items: [
        { title: "整理主标书与参考稿", text: "将最终版本作为 A 文件，历史稿或参考稿作为 B 文件上传。" },
        { title: "输入重点词", text: "把高风险条款、敏感表述或项目重点词加入关键字检查。" },
        { title: "按风险排序复核", text: "根据结果页先处理高风险文档，再进入原文证据核验。" }
      ]
    },
    faqSection: {
      title: "工程企业场景问题",
      items: [
        {
          question: "技术标和商务标都能使用吗？",
          answer: "可以。只要文档可被系统正常解析，就可以用于相似性排查和关键字检查。"
        },
        {
          question: "适合多人协作后的终审吗？",
          answer: "很适合。多人协作最容易带来版本混杂和表述接近问题，系统能帮助你快速筛出重点复核对象。"
        }
      ]
    },
    relatedSection: {
      title: "相关页面",
      items: [
        { title: "免费标书查重", text: "适合工程团队先做首轮预览。", to: "/free" },
        { title: "标书合规辅助", text: "查看如何结合合规复核使用。", to: "/compliance" },
        { title: "高相似度怎么办", text: "阅读处理建议指南。", to: "/guides/similarity-risk" }
      ]
    }
  },
  "business-solution": {
    seo: {
      title: "乙方销售与商务团队标书检查工具_投标文件快速复核_{siteTitle}",
      description:
        "面向乙方销售和商务团队的标书检查工具，适合在汇总多个版本、代理稿和合作方资料后，快速完成标书查重、风险筛查和原文证据复核。",
      keywords: ["商务团队标书检查", "乙方投标文件检查", "商务标书查重", "投标文件复核"],
      jsonLd: softwareSchema
    },
    eyebrow: "Business Team",
    h1: "面向乙方销售与商务团队的标书检查工具",
    intro:
      "商务团队最需要的是快节奏、高确定性的复核方式。当前系统可以帮助销售和商务团队在汇总多版本材料后，快速看清哪些文档最接近、哪些表述最需要修改，以及哪些证据可以直接反馈给撰写人员。",
    chips: ["适合交付前复核", "多版本快速筛查", "结果更适合团队协作", "支持任务号找回"],
    primaryCta: { label: "开始商务标书检查", to: "/upload" },
    secondaryCta: { label: "查看工具说明", to: "/docs" },
    cardSection: {
      title: "商务团队更关注哪些能力",
      columns: 3,
      items: [
        { title: "快速看懂结果", text: "先看相似度排行和风险摘要，减少在低风险文档上的无效投入。" },
        { title: "能直接反馈修改", text: "对比页可展示原文证据，便于把问题清晰传递给撰写人或合作方。" },
        { title: "支持多文件并行复核", text: "适合处理代理稿、合作方稿和历史版本一起比对的常见场景。" }
      ]
    },
    textSections: [
      {
        title: "为什么商务团队更适合先看摘要再看细节",
        paragraphs: [
          "商务团队通常时间更紧，很多时候并不需要先逐段通读，而是要先知道风险最高的文件是谁、问题大概集中在哪里。当前系统的结果页正适合做这件事。",
          "等高风险文件被锁定之后，再把原文证据交给对应负责人处理，整体效率会明显高于全量人工排查。"
        ]
      }
    ],
    stepSection: {
      title: "商务团队使用建议",
      items: [
        { title: "先统一材料", text: "把主稿作为 A 文件，代理稿、合作方稿和参考稿作为 B 文件。" },
        { title: "先用结果页排优先级", text: "根据相似度、风险摘要和预览片段确定处理顺序。" },
        { title: "再把证据回传", text: "通过原文对比页面将问题更精确地反馈给相关负责人。" }
      ]
    },
    faqSection: {
      title: "商务团队常见问题",
      items: [
        {
          question: "商务团队不懂技术内容也能看懂结果吗？",
          answer: "可以。结果页会先给出相似度排行和风险摘要，便于非技术角色先做优先级判断。"
        },
        {
          question: "能不能作为交付前的最后一道检查？",
          answer: "可以，它非常适合做提交前的快速复核和重点排查。"
        }
      ]
    },
    relatedSection: {
      title: "相关页面",
      items: [
        { title: "标书检查工具", text: "查看通用标书检查介绍。", to: "/check" },
        { title: "免费标书查重", text: "先从免费预览开始。", to: "/free" },
        { title: "标书检查看什么", text: "阅读检查重点指南。", to: "/guides/biaoshu-check" }
      ]
    }
  },
  "guide-biaoshu-chachong": {
    seo: {
      title: "标书查重是什么意思_投标文件查重怎么用_{siteTitle}",
      description:
        "了解标书查重是什么意思、适合哪些场景、和普通文章查重有什么区别，以及工程企业和商务团队如何使用标书查重系统完成首轮筛查与证据复核。",
      keywords: ["标书查重是什么意思", "投标文件查重", "标书查重怎么用"],
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: "标书查重是什么意思",
        about: ["标书查重", "投标文件查重"]
      }
    },
    eyebrow: "Guide",
    h1: "标书查重是什么意思",
    intro:
      "标书查重，指的是对主标书与一份或多份投标文件进行相似度比对，帮助团队排查重复内容、改写痕迹、语义接近和潜在围标风险。它通常用于工程企业或商务团队在投标前的自查与复核。",
    chips: ["适合新用户理解", "区分普通查重", "适合工程/商务场景"],
    primaryCta: { label: "直接开始查重", to: "/upload" },
    secondaryCta: { label: "返回首页", to: "/" },
    textSections: [
      {
        title: "标书查重和普通查重有什么区别",
        paragraphs: [
          "普通文章查重更多面向学术或通用文本重复检测，而标书查重更强调投标文件之间的相似关系、结构接近度、关键字命中和原文证据链。",
          "在真实业务里，大家关心的不只是一个数字，而是具体哪些文件最像、哪些段落问题最大、哪些内容需要优先修改。"
        ]
      },
      {
        title: "哪些场景最适合用标书查重",
        paragraphs: [
          "当团队需要比较历史版本、代理稿、合作方稿或多份参考文件时，标书查重是最适合的首轮筛查工具。",
          "对于工程企业和乙方商务团队，标书查重尤其适合在投标定稿前、提交前和版本汇总后使用。"
        ]
      }
    ],
    faqSection: {
      title: "概念相关问题",
      items: [
        {
          question: "标书查重只看重复率吗？",
          answer: "不是。更重要的是相似片段、风险摘要、关键字命中和原文证据。"
        },
        {
          question: "多份文件比对和单份比对有区别吗？",
          answer: "有。多份比对更适合筛查高风险文件，单份比对更适合做细致复核。"
        }
      ]
    },
    relatedSection: {
      title: "继续阅读",
      items: [
        { title: "免费标书查重", text: "从免费预览开始体验。", to: "/free" },
        { title: "标书检查工具", text: "查看更完整的检查说明。", to: "/check" },
        { title: "高相似度怎么办", text: "阅读处理建议。", to: "/guides/similarity-risk" }
      ]
    }
  },
  "guide-biaoshu-check": {
    seo: {
      title: "标书检查一般检查什么_投标文件复核重点_{siteTitle}",
      description:
        "了解标书检查一般检查什么，包括重复内容、改写相似、关键字命中、结构相似项和原文证据，适合工程企业与商务团队建立高效复核流程。",
      keywords: ["标书检查一般检查什么", "投标文件检查重点", "标书复核"],
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: "标书检查一般检查什么",
        about: ["标书检查", "投标文件复核"]
      }
    },
    eyebrow: "Guide",
    h1: "标书检查一般检查什么",
    intro:
      "如果把标书检查理解成一个正式复核动作，那么通常至少要看重复内容、改写相似、关键字命中、结构接近度和原文证据。不同团队的关注重点不同，但这几类信息几乎都值得纳入投标前检查清单。",
    chips: ["复核重点拆解", "适合建立检查清单", "工程与商务通用"],
    primaryCta: { label: "开始标书检查", to: "/upload" },
    secondaryCta: { label: "查看文档中心", to: "/docs" },
    cardSection: {
      title: "建议重点检查的五类信息",
      columns: 3,
      items: [
        { title: "完全重复", text: "优先处理高度一致的正文片段，这是最直观的风险点。" },
        { title: "改写相似与语义接近", text: "有些内容虽然做了改写，但核心结构和语义仍旧接近。" },
        { title: "关键字命中", text: "将高风险词和重点条款加入检查，有助于提升复核针对性。" },
        { title: "格式结构相似", text: "句子数、段落数等结构指标过于接近时，也值得回到原文复核。" },
        { title: "元数据与证据链", text: "配合元数据和原文高亮，可以更快说明问题发生在哪里。" }
      ]
    },
    faqSection: {
      title: "检查清单相关问题",
      items: [
        {
          question: "商务团队和工程团队的检查重点一样吗？",
          answer: "不完全一样，但都建议先看高风险摘要，再根据职责进入原文复核。"
        },
        {
          question: "检查一定要逐段通读吗？",
          answer: "不一定。先用系统筛出重点，再做定点复核，通常更高效。"
        }
      ]
    },
    relatedSection: {
      title: "继续阅读",
      items: [
        { title: "标书检查工具", text: "查看工具页。", to: "/check" },
        { title: "商务团队场景", text: "查看场景页。", to: "/solutions/business-team" },
        { title: "标书查重是什么", text: "阅读基础概念。", to: "/guides/biaoshu-chachong" }
      ]
    }
  },
  "guide-similarity-risk": {
    seo: {
      title: "投标文件相似度高怎么办_标书高风险处理建议_{siteTitle}",
      description:
        "当投标文件相似度高时，如何通过结果总览、关键字命中和原文证据定位高风险内容，并组织工程团队或商务团队高效修改与复核。",
      keywords: ["投标文件相似度高怎么办", "标书高风险怎么处理", "围标风险排查"],
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: "投标文件相似度高怎么办",
        about: ["投标文件相似度", "标书风险处理"]
      }
    },
    eyebrow: "Guide",
    h1: "投标文件相似度高怎么办",
    intro:
      "当你在结果页看到高相似度，不必立刻慌张。更合理的做法是先看哪些文件最接近、哪些片段最集中，再回到原文证据做人工确认，最后把问题拆给对应撰写人处理。",
    chips: ["适合处理高风险任务", "先摘要后证据", "适合团队协作修改"],
    primaryCta: { label: "上传文件排查", to: "/upload" },
    secondaryCta: { label: "查看结果页说明", to: "/docs#results" },
    stepSection: {
      title: "高相似度任务的处理顺序",
      items: [
        { title: "先看排名", text: "先确认是哪几份文件相似度最高，避免平均分配复核时间。" },
        { title: "再看片段", text: "观察问题是集中在局部章节，还是分散在多个部分。" },
        { title: "回到原文", text: "通过对比页查看上下文，确认哪些内容必须修改。" },
        { title: "分发整改", text: "把命中片段和证据反馈给相关撰写人员，缩短沟通成本。" }
      ]
    },
    textSections: [
      {
        title: "为什么不能只看一个相似度数字",
        paragraphs: [
          "相似度高不一定代表所有内容都需要推翻重写，真正重要的是看高风险集中在什么位置、是否是关键章节、以及能否通过证据快速定位问题。",
          "因此，系统中的相似度排行、风险摘要和原文证据页需要结合起来使用，才能形成更可执行的处理方案。"
        ]
      }
    ],
    faqSection: {
      title: "高风险处理问题",
      items: [
        {
          question: "看到高相似度后第一步应该做什么？",
          answer: "先看结果总览锁定高风险文件，而不是立刻逐段通读所有文档。"
        },
        {
          question: "是否一定要全部重写？",
          answer: "不一定，通常要结合原文证据判断具体问题位置，再决定局部修改还是整体调整。"
        }
      ]
    },
    relatedSection: {
      title: "继续阅读",
      items: [
        { title: "工程企业方案", text: "查看工程企业处理方式。", to: "/solutions/engineering" },
        { title: "标书合规辅助", text: "查看合规复核页面。", to: "/compliance" },
        { title: "使用文档", text: "查看完整操作说明。", to: "/docs" }
      ]
    }
  }
};

export function getSeoPage(key: string) {
  return localizeDeep(seoPages[key as SeoPageKey] || seoPages.home);
}
