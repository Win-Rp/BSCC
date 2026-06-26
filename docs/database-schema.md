# 标书查重系统 V1 SQLite 数据库设计

## 1. 设计原则

V1 使用 SQLite，数据库设计以快速上线、低复杂度、方便 AI 生成代码为目标。

核心原则：

- 任务、文件、结果、订单分表存储。
- 原文文件和大体积高亮数据优先存放在本地文件系统，数据库保存路径和索引。
- 7 天后删除临时任务数据，仅保留订单基础记录。
- 所有状态字段使用明确枚举值，便于前后端和后台统一处理。

## 2. 表清单

- `admin_users`：管理员账号。
- `tasks`：查重任务。
- `task_files`：任务文件。
- `compare_results`：A 与每个 B 的查重汇总结果。
- `matched_segments`：重复句子/段落明细。
- `keyword_hits`：关键字命中明细。
- `metadata_results`：元数据对比结果。
- `format_results`：格式/结构对比结果。
- `orders`：支付订单。
- `settings`：系统配置。
- `operation_logs`：后台操作日志。

## 3. admin_users

管理员账号表。

```sql
CREATE TABLE admin_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  display_name TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_login_at TEXT
);
```

字段说明：

- `password_hash`：只保存密码哈希，不保存明文密码。
- `is_active`：1 启用，0 禁用。

## 4. tasks

查重任务主表。

```sql
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_no TEXT NOT NULL UNIQUE,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  unlock_status TEXT NOT NULL DEFAULT 'free',
  contact TEXT,
  keyword_text TEXT,
  b_file_count INTEGER NOT NULL DEFAULT 0,
  preview_limit INTEGER NOT NULL DEFAULT 3,
  storage_dir TEXT NOT NULL,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  expires_at TEXT NOT NULL,
  deleted_at TEXT
);
```

字段说明：

- `task_no`：前台展示和恢复使用的任务号。
- `mode`：`single` 表示 A vs B，`multi` 表示 1 对多。
- `status`：任务状态，见状态枚举。
- `unlock_status`：`free`、`locked`、`unlocked`。
- `contact`：付费功能必填，可为手机号、邮箱或微信号。
- `keyword_text`：用户原始输入的关键字。
- `storage_dir`：任务文件在本地文件系统中的目录。

任务状态枚举：

- `created`
- `uploaded`
- `queued`
- `parsing`
- `checking`
- `awaiting_payment`
- `completed`
- `failed`
- `expired`
- `deleted`

## 5. task_files

任务文件表。

```sql
CREATE TABLE task_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  original_name TEXT NOT NULL,
  stored_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_ext TEXT NOT NULL,
  mime_type TEXT,
  file_size INTEGER,
  parse_status TEXT NOT NULL DEFAULT 'pending',
  parsed_text_path TEXT,
  parsed_json_path TEXT,
  page_count INTEGER,
  word_count INTEGER,
  sentence_count INTEGER,
  paragraph_count INTEGER,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

字段说明：

- `role`：`A` 或 `B`。
- `parse_status`：`pending`、`success`、`failed`。
- `parsed_text_path`：解析后的纯文本路径。
- `parsed_json_path`：包含页码、段落、句子等结构化解析结果的 JSON 路径。

索引：

```sql
CREATE INDEX idx_task_files_task_id ON task_files(task_id);
CREATE INDEX idx_task_files_role ON task_files(role);
```

## 6. compare_results

A 与每个 B 的查重汇总结果。

```sql
CREATE TABLE compare_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER NOT NULL,
  a_file_id INTEGER NOT NULL,
  b_file_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  total_similarity REAL NOT NULL DEFAULT 0,
  exact_similarity REAL NOT NULL DEFAULT 0,
  rewrite_similarity REAL NOT NULL DEFAULT 0,
  semantic_similarity REAL NOT NULL DEFAULT 0,
  sentence_similarity REAL NOT NULL DEFAULT 0,
  paragraph_similarity REAL NOT NULL DEFAULT 0,
  format_similarity REAL NOT NULL DEFAULT 0,
  metadata_similarity REAL NOT NULL DEFAULT 0,
  keyword_hit_count INTEGER NOT NULL DEFAULT 0,
  matched_sentence_count INTEGER NOT NULL DEFAULT 0,
  matched_paragraph_count INTEGER NOT NULL DEFAULT 0,
  preview_json_path TEXT,
  detail_json_path TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(id),
  FOREIGN KEY (a_file_id) REFERENCES task_files(id),
  FOREIGN KEY (b_file_id) REFERENCES task_files(id)
);
```

字段说明：

- `total_similarity`：主重复率，按 A 文件重复/相似字数占比计算。
- `preview_json_path`：免费预览片段数据。
- `detail_json_path`：完整高亮对比数据。

索引：

```sql
CREATE INDEX idx_compare_results_task_id ON compare_results(task_id);
CREATE INDEX idx_compare_results_b_file_id ON compare_results(b_file_id);
CREATE INDEX idx_compare_results_total_similarity ON compare_results(total_similarity);
```

## 7. matched_segments

重复句子/段落明细表。

```sql
CREATE TABLE matched_segments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  compare_result_id INTEGER NOT NULL,
  match_type TEXT NOT NULL,
  similarity REAL NOT NULL,
  a_text TEXT NOT NULL,
  b_text TEXT NOT NULL,
  a_position_json TEXT NOT NULL,
  b_position_json TEXT NOT NULL,
  a_char_count INTEGER NOT NULL DEFAULT 0,
  is_preview INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY (compare_result_id) REFERENCES compare_results(id)
);
```

字段说明：

- `match_type`：`exact`、`rewrite`、`semantic`、`keyword`。
- `a_position_json` / `b_position_json`：保存页码、段落序号、句子序号、字符范围等定位信息。
- `is_preview`：1 表示可在未付费预览中展示。

索引：

```sql
CREATE INDEX idx_matched_segments_result_id ON matched_segments(compare_result_id);
CREATE INDEX idx_matched_segments_match_type ON matched_segments(match_type);
```

## 8. keyword_hits

关键字命中明细表。

```sql
CREATE TABLE keyword_hits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER NOT NULL,
  file_id INTEGER NOT NULL,
  keyword TEXT NOT NULL,
  hit_text TEXT NOT NULL,
  position_json TEXT NOT NULL,
  context_before TEXT,
  context_after TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(id),
  FOREIGN KEY (file_id) REFERENCES task_files(id)
);
```

索引：

```sql
CREATE INDEX idx_keyword_hits_task_id ON keyword_hits(task_id);
CREATE INDEX idx_keyword_hits_file_id ON keyword_hits(file_id);
CREATE INDEX idx_keyword_hits_keyword ON keyword_hits(keyword);
```

## 9. metadata_results

元数据对比结果表。

```sql
CREATE TABLE metadata_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  compare_result_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  a_value TEXT,
  b_value TEXT,
  similarity_type TEXT NOT NULL,
  is_highlighted INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY (compare_result_id) REFERENCES compare_results(id)
);
```

字段说明：

- `field_name`：作者、创建时间、修改时间、软件、模板来源等。
- `similarity_type`：`same`、`similar`、`different`、`missing`。

## 10. format_results

格式/结构对比结果表。

```sql
CREATE TABLE format_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  compare_result_id INTEGER NOT NULL,
  item_name TEXT NOT NULL,
  a_value TEXT,
  b_value TEXT,
  similarity REAL NOT NULL DEFAULT 0,
  description TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (compare_result_id) REFERENCES compare_results(id)
);
```

字段说明：

- `item_name`：标题层级、段落数量、页眉页脚、字体样式、目录结构等。

## 11. orders

支付订单表。

```sql
CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_no TEXT NOT NULL UNIQUE,
  task_id INTEGER NOT NULL,
  contact TEXT NOT NULL,
  status TEXT NOT NULL,
  b_file_count INTEGER NOT NULL,
  unit_price_cents INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL,
  pay_channel TEXT NOT NULL DEFAULT 'alipay',
  alipay_trade_no TEXT,
  qr_code_url TEXT,
  paid_at TEXT,
  closed_at TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

订单状态枚举：

- `created`
- `pending`
- `paid`
- `failed`
- `closed`
- `refunded`

索引：

```sql
CREATE INDEX idx_orders_task_id ON orders(task_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_contact ON orders(contact);
```

## 12. settings

系统配置表。

```sql
CREATE TABLE settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL,
  description TEXT,
  updated_at TEXT NOT NULL
);
```

建议初始化配置：

- `price_per_b_file_cents`：每份 B 文件单价，单位分。
- `preview_segment_limit`：每个 B 文件免费预览片段数量。
- `result_retention_days`：结果保留天数，默认 7。
- `customer_service_wechat`：客服微信。
- `customer_service_email`：客服邮箱。
- `threshold_exact`：完全重复阈值。
- `threshold_rewrite`：改写相似阈值。
- `threshold_semantic`：语义相似阈值。

## 13. operation_logs

后台操作日志表。

```sql
CREATE TABLE operation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_user_id INTEGER,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
);
```

记录的操作包括：

- 手动标记已支付。
- 重新发起查重。
- 延长结果保留时间。
- 删除任务数据。
- 修改单价。
- 修改客服信息。
- 修改查重阈值。

## 14. 文件系统目录建议

```text
storage/
  tasks/
    {task_no}/
      uploads/
        A/
        B/
      parsed/
      results/
      previews/
  logs/
```

数据库只保存文件路径，不直接存储原文二进制。

## 15. 清理策略

定时任务扫描 `tasks.expires_at`。

过期后：

- 删除 `storage/tasks/{task_no}` 目录。
- 清空或删除任务相关临时结果。
- 将任务状态更新为 `deleted`。
- 保留 `orders` 基础记录。
- 保留必要的订单字段和错误摘要。

