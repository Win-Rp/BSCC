# 标书查重系统 V1 API 规格

## 1. 通用约定

后端建议使用 FastAPI，接口统一返回 JSON。

基础返回格式：

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

错误返回格式：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "任务不存在"
  }
}
```

时间字段统一使用 ISO 8601 字符串。

## 2. 错误码建议

- `VALIDATION_ERROR`：请求参数错误。
- `UPLOAD_FAILED`：文件上传失败。
- `UNSUPPORTED_FILE_TYPE`：文件类型不支持。
- `PARSE_FAILED`：文件解析失败。
- `SCAN_PDF_NOT_SUPPORTED`：扫描件 PDF 暂不支持。
- `TASK_NOT_FOUND`：任务不存在。
- `TASK_EXPIRED`：任务已过期。
- `TASK_DELETED`：任务数据已删除。
- `ORDER_NOT_FOUND`：订单不存在。
- `ORDER_NOT_PAID`：订单未支付。
- `PAYMENT_FAILED`：支付失败。
- `ADMIN_UNAUTHORIZED`：后台未登录。
- `INTERNAL_ERROR`：系统内部错误。

## 3. 前台接口

### 3.1 创建查重任务

```http
POST /api/tasks
Content-Type: multipart/form-data
```

请求字段：

- `a_file`：主标书 A，必填。
- `b_files`：对比标书 B，1 至 10 个，必填。
- `keywords`：关键字文本，可选，支持逗号或换行。

系统规则：

- 1 个 B 文件时，任务模式为 `single`。
- 2 至 10 个 B 文件时，任务模式为 `multi`。
- 创建后立即进入队列。

返回：

```json
{
  "success": true,
  "data": {
    "task_no": "T202606250001",
    "mode": "multi",
    "status": "queued",
    "b_file_count": 3,
    "expires_at": "2026-07-02T10:00:00+08:00"
  },
  "error": null
}
```

### 3.2 查询任务状态

```http
GET /api/tasks/{task_no}/status
```

返回：

```json
{
  "success": true,
  "data": {
    "task_no": "T202606250001",
    "mode": "multi",
    "status": "checking",
    "unlock_status": "locked",
    "progress": 60,
    "message": "正在查重",
    "error_message": null
  },
  "error": null
}
```

### 3.3 获取结果汇总

```http
GET /api/tasks/{task_no}/summary
```

返回：

```json
{
  "success": true,
  "data": {
    "task_no": "T202606250001",
    "mode": "multi",
    "status": "awaiting_payment",
    "unlock_status": "locked",
    "a_file": {
      "id": 1,
      "name": "A标书.docx"
    },
    "results": [
      {
        "compare_result_id": 11,
        "b_file_id": 2,
        "b_file_name": "B1标书.docx",
        "total_similarity": 0.72,
        "exact_similarity": 0.31,
        "rewrite_similarity": 0.25,
        "semantic_similarity": 0.16,
        "format_similarity": 0.80,
        "metadata_similarity": 0.50,
        "keyword_hit_count": 8,
        "matched_sentence_count": 120,
        "matched_paragraph_count": 28
      }
    ],
    "payment_required": true,
    "expires_at": "2026-07-02T10:00:00+08:00"
  },
  "error": null
}
```

### 3.4 获取免费预览片段

```http
GET /api/tasks/{task_no}/results/{compare_result_id}/preview
```

返回：

```json
{
  "success": true,
  "data": {
    "compare_result_id": 11,
    "segments": [
      {
        "match_type": "exact",
        "similarity": 1.0,
        "a_text": "本项目技术方案采用...",
        "b_text": "本项目技术方案采用...",
        "a_position": {
          "page": 3,
          "paragraph": 12,
          "sentence": 2
        },
        "b_position": {
          "page": 4,
          "paragraph": 15,
          "sentence": 1
        }
      }
    ]
  },
  "error": null
}
```

### 3.5 获取完整文档对比数据

```http
GET /api/tasks/{task_no}/results/{compare_result_id}/detail
```

访问规则：

- B 文件数不超过后台 `free_b_file_limit` 时免费访问。
- 超过该上限的任务需支付成功后访问；该权限在创建任务时确定，后续修改配置不影响已有任务。

返回：

```json
{
  "success": true,
  "data": {
    "compare_result_id": 11,
    "a_document": {
      "file_id": 1,
      "name": "A标书.docx",
      "blocks": []
    },
    "b_document": {
      "file_id": 2,
      "name": "B1标书.docx",
      "blocks": []
    },
    "matches": [
      {
        "id": 1001,
        "match_type": "rewrite",
        "similarity": 0.86,
        "a_position": {
          "block_id": "a-p12-s2",
          "page": 3
        },
        "b_position": {
          "block_id": "b-p15-s1",
          "page": 4
        }
      }
    ],
    "metadata_results": [],
    "format_results": [],
    "keyword_hits": []
  },
  "error": null
}
```

### 3.6 创建支付订单

```http
POST /api/orders
Content-Type: application/json
```

请求：

```json
{
  "task_no": "T202606250001",
  "contact": "user@example.com"
}
```

返回：

```json
{
  "success": true,
  "data": {
    "order_no": "O202606250001",
    "task_no": "T202606250001",
    "amount_cents": 3000,
    "b_file_count": 3,
    "qr_code_url": "https://example.com/alipay/qrcode",
    "status": "pending"
  },
  "error": null
}
```

### 3.7 查询支付状态

```http
GET /api/orders/{order_no}/status
```

返回：

```json
{
  "success": true,
  "data": {
    "order_no": "O202606250001",
    "task_no": "T202606250001",
    "status": "paid",
    "unlock_status": "unlocked",
    "paid_at": "2026-06-25T10:10:00+08:00"
  },
  "error": null
}
```

### 3.8 支付宝回调

```http
POST /api/payments/alipay/notify
```

说明：

- 接收支付宝异步通知。
- 后端必须验签。
- 验签成功后更新订单状态。
- 支付成功后解锁任务。

返回：

```text
success
```

### 3.9 恢复任务或订单

```http
POST /api/recover
Content-Type: application/json
```

请求：

```json
{
  "task_no": "T202606250001",
  "order_no": "O202606250001",
  "contact": "user@example.com"
}
```

规则：

- 支持只传任务号。
- 支持只传订单号。
- 支持联系方式 + 任务号。
- 支持联系方式 + 订单号。

返回：

```json
{
  "success": true,
  "data": {
    "task_no": "T202606250001",
    "order_no": "O202606250001",
    "mode": "multi",
    "task_status": "completed",
    "unlock_status": "unlocked",
    "order_status": "paid",
    "can_view_detail": true,
    "expires_at": "2026-07-02T10:00:00+08:00"
  },
  "error": null
}
```

### 3.10 获取客服信息

```http
GET /api/support
```

返回：

```json
{
  "success": true,
  "data": {
    "wechat": "customer_service_wechat",
    "email": "support@example.com"
  },
  "error": null
}
```

## 4. 后台接口

### 4.1 管理员登录

```http
POST /api/admin/login
Content-Type: application/json
```

请求：

```json
{
  "username": "admin",
  "password": "password"
}
```

返回：

```json
{
  "success": true,
  "data": {
    "token": "jwt-token",
    "username": "admin",
    "display_name": "管理员"
  },
  "error": null
}
```

### 4.2 订单列表

```http
GET /api/admin/orders
Authorization: Bearer {token}
```

查询参数：

- `order_no`
- `task_no`
- `status`
- `contact`
- `created_from`
- `created_to`
- `page`
- `page_size`

返回字段：

- 订单号。
- 任务号。
- 支付状态。
- 支付金额。
- B 文件数量。
- 用户联系方式。
- 创建时间。
- 支付时间。

### 4.3 订单详情

```http
GET /api/admin/orders/{order_no}
Authorization: Bearer {token}
```

返回字段：

- 订单号。
- 任务号。
- 支付状态。
- 支付金额。
- B 文件数量。
- 用户联系方式。
- 查重状态。
- 错误信息。
- 创建时间。
- 支付时间。
- 过期时间。
- 文件名列表。

### 4.4 手动标记订单已支付

```http
POST /api/admin/orders/{order_no}/mark-paid
Authorization: Bearer {token}
```

系统动作：

- 将订单状态更新为 `paid`。
- 将关联任务解锁。
- 记录后台操作日志。

### 4.5 任务列表

```http
GET /api/admin/tasks
Authorization: Bearer {token}
```

查询参数：

- `task_no`
- `status`
- `mode`
- `created_from`
- `created_to`
- `page`
- `page_size`

### 4.6 任务详情

```http
GET /api/admin/tasks/{task_no}
Authorization: Bearer {token}
```

返回字段：

- 任务号。
- 模式。
- 状态。
- 解锁状态。
- 文件列表。
- 结果摘要。
- 错误信息。
- 创建时间。
- 完成时间。
- 过期时间。

### 4.7 重新发起查重

```http
POST /api/admin/tasks/{task_no}/rerun
Authorization: Bearer {token}
```

系统动作：

- 校验任务文件是否仍存在。
- 将任务重新加入队列。
- 记录后台操作日志。

### 4.8 延长结果保留时间

```http
POST /api/admin/tasks/{task_no}/extend
Authorization: Bearer {token}
Content-Type: application/json
```

请求：

```json
{
  "days": 7
}
```

### 4.9 手动删除任务数据

```http
POST /api/admin/tasks/{task_no}/delete-data
Authorization: Bearer {token}
```

系统动作：

- 删除任务临时文件。
- 将任务状态更新为 `deleted`。
- 保留订单基础记录。
- 记录后台操作日志。

### 4.10 获取系统配置

```http
GET /api/admin/settings
Authorization: Bearer {token}
```

### 4.11 更新系统配置

```http
PUT /api/admin/settings
Authorization: Bearer {token}
Content-Type: application/json
```

请求：

```json
{
  "price_per_b_file_cents": "1000",
  "free_b_file_limit": "1",
  "preview_segment_limit": "3",
  "result_retention_days": "7",
  "customer_service_wechat": "customer_service_wechat",
  "customer_service_email": "support@example.com",
  "threshold_exact": "1.0",
  "threshold_rewrite": "0.8",
  "threshold_semantic": "0.7"
}
```

### 4.12 后台操作日志

```http
GET /api/admin/operation-logs
Authorization: Bearer {token}
```

查询参数：

- `action`
- `target_type`
- `target_id`
- `created_from`
- `created_to`
- `page`
- `page_size`

## 5. 实时状态建议

V1 可以先使用前端轮询：

- 任务状态：每 2 至 5 秒请求 `/api/tasks/{task_no}/status`。
- 支付状态：每 2 至 5 秒请求 `/api/orders/{order_no}/status`。

后续版本可升级为 WebSocket 或 Server-Sent Events。
