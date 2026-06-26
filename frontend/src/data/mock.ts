export interface FileRow {
  role: "A" | "B";
  name: string;
  size: string;
  status: string;
}

export interface RankRow {
  id: number;
  name: string;
  score: number;
  level: string;
  levelType: "success" | "warning" | "danger" | "info";
  color: string;
}

export interface OrderRow {
  orderNo: string;
  taskNo: string;
  amount: string;
  status: string;
  type: "success" | "warning" | "danger" | "info";
}

export const topMetrics = [
  { label: "今日平均重复率", value: "42.8%", hint: "较昨日 -6.2%" },
  { label: "已处理文件", value: "96", hint: "18 个任务" },
  { label: "平均等待", value: "2.4 min", hint: "队列健康" },
  { label: "支付解锁率", value: "63%", hint: "批量任务" }
];

export const files: FileRow[] = [
  { role: "A", name: "A标书-智慧园区技术方案.docx", size: "12.4 MB", status: "已选择" },
  { role: "B", name: "B1-智慧园区投标文件.pdf", size: "9.1 MB", status: "已选择" },
  { role: "B", name: "B2-商务响应文件.docx", size: "6.8 MB", status: "已选择" },
  { role: "B", name: "B3-技术部分终稿.docx", size: "14.2 MB", status: "已选择" }
];

export const rankRows: RankRow[] = [
  { id: 11, name: "B1-智慧园区投标文件.pdf", score: 72, level: "高风险", levelType: "danger", color: "#fb7185" },
  { id: 12, name: "B3-技术部分终稿.docx", score: 58, level: "中风险", levelType: "warning", color: "#fbbf24" },
  { id: 13, name: "B2-商务响应文件.docx", score: 24, level: "低风险", levelType: "success", color: "#22c55e" }
];

export const metaItems = [
  { label: "作者", value: "相同：Admin" },
  { label: "创建时间", value: "相近：2026-06-20" },
  { label: "软件", value: "Microsoft Word 16" },
  { label: "标题层级", value: "高度一致" }
];

export const keywordHits = [
  { text: "围标", count: 2, type: "danger" },
  { text: "串标", count: 1, type: "danger" },
  { text: "独家授权", count: 3, type: "warning" },
  { text: "同一模板", count: 4, type: "info" }
];

export const orders: OrderRow[] = [
  { orderNo: "O202606250001", taskNo: "T202606250001", amount: "¥30.00", status: "待支付", type: "warning" },
  { orderNo: "O202606250002", taskNo: "T202606250002", amount: "¥50.00", status: "已支付", type: "success" },
  { orderNo: "-", taskNo: "T202606250003", amount: "-", status: "解析失败", type: "danger" }
];
