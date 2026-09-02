// 使用说明页内容：参照 Web 版说明文档，按小程序端重新组织
const DOC_CONTENT = {
  hero: {
    title: "标书查重 · 使用说明",
    description: "一套面向标书场景的智能查重与风险研判工具。上传主标书与多份对比标书，自动完成文本解析、重复检测与结果排行。",
    chips: ["1 对多查重", "免费预览", "扫码支付解锁", "任务找回"]
  },
  anchors: [
    { id: "quick-start", label: "快速上手" },
    { id: "workflow", label: "使用流程" },
    { id: "results", label: "结果解读" },
    { id: "payment", label: "支付解锁" },
    { id: "compare", label: "对比页" },
    { id: "recover", label: "任务找回" },
    { id: "faq", label: "常见问题" }
  ],
  quickStart: {
    title: "快速上手",
    items: [
      { title: "准备文件", text: "准备主标书 A 与 1 至 10 份对比标书 B，支持 DOCX、PDF 格式。" },
      { title: "上传发起", text: "在上传页选择 A 文件与多个 B 文件，可填写关键字辅助筛查，提交后自动开始查重。" },
      { title: "查看结果", text: "任务完成后可查看相似度排行、重复片段摘录与可视化指标，免费预览关键片段。" },
      { title: "解锁详情", text: "创建订单并按提示完成支付，页面会自动解锁完整对比详情。" }
    ]
  },
  workflow: {
    title: "使用流程",
    steps: [
      { index: "01", title: "上传主标书 A", description: "主标书作为基准文档参与对比，系统会将其与每一份 B 文件分别比对。" },
      { index: "02", title: "上传对比标书 B", description: "支持 1 至 10 份对比文件，系统自动生成 1 对多结果排行，越靠前相似度越高。" },
      { index: "03", title: "填写关键字（可选）", description: "输入关注的关键词，例如工期、履约、质保等，提交后在详情中展示命中位置。" },
      { index: "04", title: "提交并等待", description: "任务排队、解析、查重需要一定时间。可记录任务号稍后回来查看，系统会保留结果 7 天。" },
      { index: "05", title: "查看排行与预览", description: "结果页展示总相似度、完全重复、改写相似等指标，未支付前可免费预览片段。" },
      { index: "06", title: "解锁完整详情", description: "在订单页创建订单并完成支付，页面自动刷新解锁，进入对比页查看全部明细。" }
    ]
  },
  results: {
    title: "结果解读",
    items: [
      { title: "相似度排行", text: "结果列表按总相似度从高到低排列，并标注风险等级（高风险 / 中风险 / 低风险）。" },
      { title: "多维指标", text: "每个结果包含总相似度、完全重复、改写相似、语义相似、格式相似、元数据相似六类指标。" },
      { title: "免费预览", text: "未支付时可预览重复片段摘录，了解重复位置与内容，帮助判断是否需要解锁。" },
      { title: "打开原文", text: "支持直接打开 A 标书与当前 B 标书原文，便于人工核对。" }
    ],
    tips: [
      { title: "风险等级参考", text: "总相似度 80% 以上为高风险，50% 以上为中风险，其余为低风险。" },
      { title: "保留期限", text: "查重结果默认保留 7 天，请及时下载或记录任务号以便找回。" },
      { title: "结果仅供参考", text: "查重结果由算法自动生成，建议结合人工判断使用。" }
    ]
  },
  payment: {
    title: "支付与解锁",
    highlights: [
      { title: "免费预览不等于解锁", text: "未支付前可查看摘要与预览片段，完整命中明细与双栏原文需支付后解锁。", warn: true },
      { title: "按 B 文件数量计费", text: "费用按对比 B 文件份数实时计算，后台可配置原价与促销价，下单与展示同源。" }
    ],
    steps: [
      { title: "填写联系方式", text: "建议填写邮箱或手机号，便于按联系方式找回历史订单与结果。" },
      { title: "选择支付方式", text: "支持支付宝、微信两种通道，以站点实际启用情况为准。" },
      { title: "完成支付", text: "创建订单后按系统提示完成支付，如返回二维码可扫码继续。" },
      { title: "自动解锁", text: "支付成功后本页会自动刷新，任务解锁后可进入对比页查看完整详情。" }
    ]
  },
  compare: {
    title: "对比页",
    items: [
      { title: "命中片段", text: "按完全重复、改写相似、语义相似、关键字分类展示，可切换筛选。" },
      { title: "双栏原文", text: "A / B 文档左右对照展示，命中片段高亮定位，支持逐条查看上下文。" },
      { title: "格式与元数据", text: "可查看格式相似项（字数、段落数等结构对比）与元数据对比（标题、作者、日期等）。" }
    ]
  },
  recover: {
    title: "任务找回",
    description: "无需登录，凭任务号、订单号或联系方式即可恢复历史任务与结果，结果默认保留 7 天。",
    cards: [
      { title: "按任务号", text: "任务号在提交后即生成，例如 T202606250001，可在进度页、结果页复制保存。" },
      { title: "按订单号", text: "创建订单后可在订单页复制订单号，用于找回支付状态与解锁结果。" },
      { title: "按联系方式", text: "填写提交时使用的邮箱或手机号，可辅助校验并找回关联任务。" }
    ]
  },
  faq: [
    {
      q: "支持哪些文件格式？",
      a: "支持 DOCX、PDF。扫描版 PDF（纯图片无文字层）暂不支持解析，建议转为可编辑文本后再上传。"
    },
    {
      q: "一次可以上传几份对比文件？",
      a: "主标书 A 1 份，对比标书 B 建议 1 至 10 份。B 文件越多，费用越高，详情可参考订单页定价。"
    },
    {
      q: "查重需要多久？",
      a: "取决于文件大小与服务器负载，排队与解析需要一定时间。可记录任务号稍后回来查看，页面也支持自动轮询进度。"
    },
    {
      q: "未支付能看到哪些内容？",
      a: "未支付可免费预览重复片段摘录与总览指标，完整命中明细、双栏原文与格式/元数据对比需支付解锁。"
    },
    {
      q: "结果会保留多久？",
      a: "默认保留 7 天，到期后系统会自动清理。请及时下载或记录任务号、订单号以便找回。"
    },
    {
      q: "支付后多久解锁？",
      a: "支付成功后，订单页会自动轮询状态并解锁，通常几秒内生效。如长时间未更新可点击“手动刷新状态”。"
    },
    {
      q: "换了手机还能找回结果吗？",
      a: "可以。只要记得任务号、订单号或联系方式，即可在“恢复历史任务”页面找回历史结果。"
    }
  ]
};

Page({
  data: {
    content: DOC_CONTENT,
    activeAnchor: "quick-start",
    expandedFaq: -1,
    siteTitle: "标书查重"
  },

  onLoad() {
    const app = getApp();
    const siteConfig = app.globalData.siteConfig || {};
    this.setData({
      siteTitle: siteConfig.site_title || "标书查重"
    });
  },

  handleAnchorTap(event) {
    const id = event.currentTarget.dataset.id;
    this.setData({ activeAnchor: id });
    wx.pageScrollTo({
      selector: `#${id}`,
      duration: 300
    });
  },

  toggleFaq(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.setData({
      expandedFaq: this.data.expandedFaq === index ? -1 : index
    });
  },

  goUpload() {
    wx.navigateBack({
      delta: 1,
      fail() {
        wx.switchTab({ url: "/pages/upload/index" });
      }
    });
  }
});
