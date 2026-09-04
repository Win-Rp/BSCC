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
  b_file_count: number;
  a_file: { id: number; name: string } | null;
  results: SummaryResult[];
  payment_required: boolean;
  expires_at: string;
}

export interface PromoPricingConfig {
  original_unit_price_cents: number;
  promo_unit_price_cents: number;
  effective_unit_price_cents: number;
  promo_enabled: boolean;
  promo_active: boolean;
  show_countdown: boolean;
  promo_note: string;
  promo_badge: string;
  promo_loss_aversion_text: string;
  promo_ends_at: string;
  server_now: string;
}

export interface PromoPricingSummary extends PromoPricingConfig {
  b_file_count: number;
  original_amount_cents: number;
  effective_amount_cents: number;
  savings_cents: number;
  discount_percent: number;
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
  payment_message?: string | null;
  status: string;
  pay_channel: "alipay" | "wechat";
  pricing: PromoPricingSummary;
}

export interface OrderStatus {
  order_no: string;
  task_no: string;
  status: string;
  unlock_status: string;
  paid_at: string | null;
  pay_channel: "alipay" | "wechat";
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

export interface AdminOverview {
  totals: {
    orders: number;
    orders_pending: number;
    orders_paid: number;
    tasks: number;
    tasks_processing: number;
    tasks_completed: number;
    tasks_failed: number;
    logs: number;
  };
  revenue: {
    paid_amount_cents: number;
    pending_amount_cents: number;
  };
  system: {
    site_base_url: string;
    home_tags_count: number;
    system_notice_enabled: boolean;
    result_retention_days: number;
  };
  payment: {
    alipay_enabled: boolean;
    alipay_configured: boolean;
    alipay_notify_url: string;
    wechat_enabled: boolean;
    wechat_configured: boolean;
    wechat_notify_url: string;
  };
  recent_orders: AdminOrderRow[];
  recent_tasks: AdminTaskRow[];
  recent_logs: AdminLogRow[];
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminListParams {
  page: number;
  page_size: number;
  status?: string;
  keyword?: string;
  created_from?: string;
  created_to?: string;
}

export interface AdminTaskBatchDeleteResult {
  requested_count: number;
  deleted_count: number;
  task_nos: string[];
}

export interface SupportInfo {
  wechat: string | null;
  email: string | null;
}

export interface PublicSiteConfig {
  site_title: string;
  home_tags: string[];
  system_notice: string;
  alipay_enabled: boolean;
  wechat_enabled: boolean;
  mp_qrcode_url?: string;
  promo: PromoPricingConfig;
}

export interface AdminSettings {
  price_per_b_file_cents: number;
  free_b_file_limit: number;
  promo_enabled: boolean;
  promo_price_per_b_file_cents: number;
  promo_ends_at: string;
  promo_note: string;
  promo_badge: string;
  promo_countdown_enabled: boolean;
  promo_loss_aversion_text: string;
  preview_segment_limit: number;
  result_retention_days: number;
  customer_service_wechat: string;
  customer_service_email: string;
  system_notice: string;
  site_base_url: string;
  site_title: string;
  home_tags: string[];
  threshold_exact: number;
  threshold_rewrite: number;
  threshold_semantic: number;
  alipay_enabled: boolean;
  alipay_gateway: string;
  alipay_app_id: string;
  alipay_notify_url: string;
  alipay_private_key: string;
  alipay_public_key: string;
  wechat_enabled: boolean;
  wechat_app_id: string;
  wechat_mch_id: string;
  wechat_api_v2_key: string;
  wechat_notify_url: string;
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

export function createOrder(taskNo: string, contact: string, payChannel: "alipay" | "wechat", locale?: string) {
  return request<OrderInfo>("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_no: taskNo, contact, pay_channel: payChannel, ...(locale ? { locale } : {}) })
  });
}

export function getOrderStatus(orderNo: string) {
  return request<OrderStatus>(`/api/orders/${orderNo}/status`);
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

export function changeAdminPassword(token: string, payload: {
  current_password: string;
  new_password: string;
  confirm_password: string;
}) {
  return request<{ force_relogin: boolean }>("/api/admin/change-password", {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

export function getAdminOrders(token: string, params: AdminListParams) {
  return request<PaginatedResult<AdminOrderRow>>(`/api/admin/orders?${new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size),
    ...(params.status ? { status: params.status } : {}),
    ...(params.keyword ? { keyword: params.keyword } : {}),
    ...(params.created_from ? { created_from: params.created_from } : {}),
    ...(params.created_to ? { created_to: params.created_to } : {})
  }).toString()}`, {
    headers: authHeaders(token)
  });
}

export function getAdminTasks(token: string, params: AdminListParams) {
  return request<PaginatedResult<AdminTaskRow>>(`/api/admin/tasks?${new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size),
    ...(params.status ? { status: params.status } : {}),
    ...(params.keyword ? { keyword: params.keyword } : {}),
    ...(params.created_from ? { created_from: params.created_from } : {}),
    ...(params.created_to ? { created_to: params.created_to } : {})
  }).toString()}`, {
    headers: authHeaders(token)
  });
}

export function getAdminOverview(token: string) {
  return request<AdminOverview>("/api/admin/overview", {
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

export function batchDeleteTaskData(token: string, taskNos: string[]) {
  return request<AdminTaskBatchDeleteResult>("/api/admin/tasks/data/batch-delete", {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ task_nos: taskNos })
  });
}

export function getAdminLogs(token: string, params: {
  page: number;
  page_size: number;
  keyword?: string;
}) {
  return request<PaginatedResult<AdminLogRow>>(`/api/admin/logs?${new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size),
    ...(params.keyword ? { keyword: params.keyword } : {})
  }).toString()}`, {
    headers: authHeaders(token)
  });
}

export function getSystemSettings(token?: string) {
  return request<AdminSettings>("/api/admin/settings", {
    headers: token ? authHeaders(token) : {}
  });
}

export function updateSystemSettings(token: string, data: AdminSettings) {
  return request<AdminSettings>("/api/admin/settings", {
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

export interface MiniTaskQrcode {
  data_url: string;
  reason: string;
}

export function getMiniTaskQrcode(taskNo: string, page: "progress" | "results") {
  return request<MiniTaskQrcode>(
    `/api/wechat/mini/qrcode?task_no=${encodeURIComponent(taskNo)}&page=${page}`
  );
}

export function getPublicSiteConfig(locale?: string) {
  const query = locale ? `?locale=${encodeURIComponent(locale)}` : "";
  return request<PublicSiteConfig>(`/api/public/site-config${query}`);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() as ApiResponse<T> : null;

  if (!response.ok || !payload?.success) {
    const message = payload?.error?.message ?? `Request failed: ${response.status}`;
    throw new Error(message);
  }

  return payload.data;
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}
