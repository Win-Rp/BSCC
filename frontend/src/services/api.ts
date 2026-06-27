const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface ApiError {
  code: string;
  message: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: ApiError | null;
}

export interface TaskStatus {
  task_no: string;
  mode: "single" | "multi";
  status: string;
  unlock_status: "free" | "locked" | "unlocked";
  progress: number;
  message: string;
  error_message: string | null;
}

export interface SummaryResult {
  compare_result_id: number;
  b_file_id: number;
  b_file_name: string;
  total_similarity: number;
  exact_similarity: number;
  rewrite_similarity: number;
  semantic_similarity: number;
  format_similarity: number;
  metadata_similarity: number;
  keyword_hit_count: number;
  matched_sentence_count: number;
  matched_paragraph_count: number;
  exact_count: number;
  rewrite_count: number;
  semantic_count: number;
}

export interface TaskSummary {
  task_no: string;
  mode: "single" | "multi";
  status: string;
  unlock_status: string;
  a_file: { id: number; name: string } | null;
  results: SummaryResult[];
  payment_required: boolean;
  expires_at: string;
}

export interface PositionInfo {
  block_id: string;
  page: number;
  paragraph: number;
  sentence: number;
}

export interface MatchSegment {
  match_type: "exact" | "rewrite" | "semantic" | "keyword";
  similarity: number;
  reason?: string;
  a_text: string;
  b_text: string;
  a_position: PositionInfo;
  b_position: PositionInfo;
  a_char_count?: number;
}

export interface DocumentBlock {
  block_id: string;
  page: number;
  paragraph: number;
  sentence: number;
  text: string;
  char_count?: number;
}

export interface MetadataResult {
  field_name: string;
  a_value: string | null;
  b_value: string | null;
  similarity_type: "same" | "similar" | "different" | "missing";
  is_highlighted: boolean;
}

export interface FormatResult {
  item_name: string;
  a_value: string;
  b_value: string;
  similarity: number;
  description: string;
}

export interface KeywordHit {
  file_id: number;
  keyword: string;
  hit_text: string;
  position: PositionInfo & { start: number; end: number };
  context_before: string;
  context_after: string;
}

export interface CompareDetail {
  compare_result_id: number;
  a_document: { file_id: number; name: string; blocks: DocumentBlock[] };
  b_document: { file_id: number; name: string; blocks: DocumentBlock[] };
  matches: MatchSegment[];
  metadata_results: MetadataResult[];
  format_results: FormatResult[];
  keyword_hits: KeywordHit[];
}

export interface OrderInfo {
  order_no: string;
  task_no: string;
  amount_cents: number;
  b_file_count: number;
  qr_code_url: string | null;
  status: string;
}

export interface OrderStatus {
  order_no: string;
  task_no: string;
  status: string;
  unlock_status: string;
  paid_at: string | null;
}

export interface RecoverResult {
  task_no: string;
  order_no: string | null;
  mode: string;
  task_status: string;
  unlock_status: string;
  order_status: string | null;
  can_view_detail: boolean;
  expires_at: string;
}

export interface AdminOrderRow {
  order_no: string;
  task_no: string;
  status: string;
  amount_cents: number;
  b_file_count: number;
  contact: string;
  created_at: string;
  paid_at: string | null;
}

export interface AdminTaskRow {
  task_no: string;
  mode: string;
  status: string;
  unlock_status: string;
  b_file_count: number;
  progress: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  expires_at: string;
}

export interface AdminLogRow {
  id: number;
  action: string;
  target_type: string;
  target_id: string;
  detail_json: string | null;
  created_at: string;
  admin_username: string | null;
}

export interface SupportInfo {
  wechat: string | null;
  email: string | null;
}

export async function createTask(payload: { aFile: File; bFiles: File[]; keywords?: string }) {
  const form = new FormData();
  form.append("a_file", payload.aFile);
  payload.bFiles.forEach((file) => form.append("b_files", file));
  if (payload.keywords) {
    form.append("keywords", payload.keywords);
  }
  return request<TaskStatus>("/api/tasks", { method: "POST", body: form });
}

export function getTaskStatus(taskNo: string) {
  return request<TaskStatus>(`/api/tasks/${taskNo}/status`);
}

export function getTaskSummary(taskNo: string) {
  return request<TaskSummary>(`/api/tasks/${taskNo}/summary`);
}

export function getPreview(taskNo: string, compareResultId: number) {
  return request<{ compare_result_id: number; segments: MatchSegment[] }>(
    `/api/tasks/${taskNo}/results/${compareResultId}/preview`
  );
}

export function getDetail(taskNo: string, compareResultId: number) {
  return request<CompareDetail>(`/api/tasks/${taskNo}/results/${compareResultId}/detail`);
}

export function getOriginalFileAUrl(taskNo: string) {
  return `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskNo)}/file/a`;
}

export function getOriginalFileBUrl(taskNo: string, compareResultId: number) {
  return `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskNo)}/file/b/${compareResultId}`;
}

export function createOrder(taskNo: string, contact: string) {
  return request<OrderInfo>("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_no: taskNo, contact })
  });
}

export function getOrderStatus(orderNo: string) {
  return request<OrderStatus>(`/api/orders/${orderNo}/status`);
}

export function simulateAlipayNotify(orderNo: string) {
  return fetch(`${API_BASE_URL}/api/payments/alipay/notify?order_no=${encodeURIComponent(orderNo)}`, {
    method: "POST"
  }).then((response) => response.text());
}

export function recoverTask(payload: { task_no?: string; order_no?: string; contact?: string }) {
  return request<RecoverResult>("/api/recover", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export function adminLogin(username: string, password: string) {
  return request<{ token: string; username: string; display_name: string }>("/api/admin/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
}

export function getAdminOrders(token: string) {
  return request<{ items: AdminOrderRow[]; total: number }>("/api/admin/orders", {
    headers: authHeaders(token)
  });
}

export function getAdminTasks(token: string) {
  return request<{ items: AdminTaskRow[]; total: number }>("/api/admin/tasks", {
    headers: authHeaders(token)
  });
}

export function markOrderPaid(token: string, orderNo: string) {
  return request<OrderStatus>(`/api/admin/orders/${orderNo}/mark-paid`, {
    method: "POST",
    headers: authHeaders(token)
  });
}

export function retryTask(token: string, taskNo: string) {
  return request<void>(`/api/admin/tasks/${taskNo}/retry`, {
    method: "POST",
    headers: authHeaders(token)
  });
}

export function extendTask(token: string, taskNo: string) {
  return request<void>(`/api/admin/tasks/${taskNo}/extend`, {
    method: "POST",
    headers: authHeaders(token)
  });
}

export function deleteTaskData(token: string, taskNo: string) {
  return request<void>(`/api/admin/tasks/${taskNo}/data`, {
    method: "DELETE",
    headers: authHeaders(token)
  });
}

export function getAdminLogs(token: string) {
  return request<{ items: AdminLogRow[]; total: number }>("/api/admin/logs", {
    headers: authHeaders(token)
  });
}

export function getSystemSettings(token?: string) {
  return request<any>("/api/admin/settings", {
    headers: token ? authHeaders(token) : {}
  });
}

export function updateSystemSettings(token: string, data: any) {
  return request<any>("/api/admin/settings", {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });
}

export function getSupport() {
  return request<SupportInfo>("/api/support");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() as ApiResponse<T> : null;

  if (!response.ok || !payload?.success) {
    const message = payload?.error?.message ?? `请求失败：${response.status}`;
    throw new Error(message);
  }

  return payload.data;
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}
