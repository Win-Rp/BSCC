import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import DATA_DIR, DB_PATH, DATABASE_URL, DEFAULT_SETTINGS
from app.utils.security import hash_password
from app.utils.time import now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS admin_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  display_name TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
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
  progress INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  expires_at TEXT NOT NULL,
  deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS task_files (
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

CREATE TABLE IF NOT EXISTS compare_results (
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

CREATE TABLE IF NOT EXISTS matched_segments (
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

CREATE TABLE IF NOT EXISTS keyword_hits (
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

CREATE TABLE IF NOT EXISTS metadata_results (
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

CREATE TABLE IF NOT EXISTS format_results (
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

CREATE TABLE IF NOT EXISTS orders (
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

CREATE TABLE IF NOT EXISTS settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL,
  description TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_user_id INTEGER,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
);

CREATE INDEX IF NOT EXISTS idx_task_files_task_id ON task_files(task_id);
CREATE INDEX IF NOT EXISTS idx_task_files_role ON task_files(role);
CREATE INDEX IF NOT EXISTS idx_compare_results_task_id ON compare_results(task_id);
CREATE INDEX IF NOT EXISTS idx_compare_results_b_file_id ON compare_results(b_file_id);
CREATE INDEX IF NOT EXISTS idx_compare_results_total_similarity ON compare_results(total_similarity);
CREATE INDEX IF NOT EXISTS idx_matched_segments_result_id ON matched_segments(compare_result_id);
CREATE INDEX IF NOT EXISTS idx_matched_segments_match_type ON matched_segments(match_type);
CREATE INDEX IF NOT EXISTS idx_keyword_hits_task_id ON keyword_hits(task_id);
CREATE INDEX IF NOT EXISTS idx_keyword_hits_file_id ON keyword_hits(file_id);
CREATE INDEX IF NOT EXISTS idx_keyword_hits_keyword ON keyword_hits(keyword);
CREATE INDEX IF NOT EXISTS idx_orders_task_id ON orders(task_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_contact ON orders(contact);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
"""


class MySQLConnection:
    """Small DB-API compatibility wrapper, keeping existing service SQL unchanged."""
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor

    def execute(self, sql, params=()):
        # KEY is reserved by MySQL but is an existing application column name.
        sql = re.sub(r"(?i)(\bsettings\s*\(\s*)key\b", r"\1`key`", sql)
        sql = re.sub(r"(?i)(\b(?:select|where|order\s+by)\s+)key\b", r"\1`key`", sql)
        sql = re.sub(r"(?i)(\bon\s+conflict\s*\(\s*)key\b", r"\1`key`", sql)
        sql = sql.replace("?", "%s")
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def commit(self): self.connection.commit()
    def rollback(self): self.connection.rollback()
    def close(self): self.connection.close()

    def executescript(self, script):
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    self.execute(statement)
                except Exception as exc:
                    # MySQL has no CREATE INDEX IF NOT EXISTS. Re-running startup
                    # should tolerate an index that was created previously.
                    if getattr(exc, "args", [None])[0] != 1061:
                        raise


def connect():
    if DATABASE_URL.startswith("mysql"):
        import pymysql
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        conn = pymysql.connect(host=parsed.hostname or "localhost", port=parsed.port or 3306,
                               user=parsed.username, password=parsed.password or "",
                               database=parsed.path.lstrip("/"), charset="utf8mb4",
                               cursorclass=pymysql.cursors.DictCursor, autocommit=False)
        return MySQLConnection(conn)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def mysql_schema() -> str:
    schema = (SCHEMA.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT PRIMARY KEY AUTO_INCREMENT")
              .replace("TEXT", "VARCHAR(255)")
              .replace("REAL", "DOUBLE")
              .replace("INTEGER", "BIGINT")
              .replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX"))
    # SQLite TEXT has no length limit. Keep content-bearing fields as LONGTEXT;
    # indexed identifiers remain VARCHAR(255) for MySQL index compatibility.
    long_columns = {
        "keyword_text", "error_message", "parsed_text_path", "parsed_json_path",
        "preview_json_path", "detail_json_path", "a_text", "b_text",
        "a_position_json", "b_position_json", "context_before", "context_after",
        "detail_json", "description", "value",
    }
    for column in long_columns:
        schema = re.sub(rf"(?m)^(\s+{column}) VARCHAR\(255\)", rf"\1 LONGTEXT", schema)
    schema = re.sub(r"(?m)^(\s*)key VARCHAR\(255\)", r"\1`key` VARCHAR(255)", schema)
    return schema


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db_session() as conn:
        schema = SCHEMA
        if DATABASE_URL.startswith("mysql"):
            schema = mysql_schema()
        conn.executescript(schema)
        _ensure_column(conn, "orders", "pay_channel", "TEXT NOT NULL DEFAULT 'alipay'")
        _ensure_column(conn, "orders", "alipay_trade_no", "TEXT")
        _ensure_column(conn, "tasks", "notify_openid", "TEXT")
        _ensure_column(conn, "tasks", "notify_authorized_at", "TEXT")
        _ensure_column(conn, "tasks", "notify_sent_at", "TEXT")
        for key, value in DEFAULT_SETTINGS.items():
            if DATABASE_URL.startswith("mysql"):
                conn.execute("INSERT IGNORE INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                             (key, value, None, now_iso()))
            else:
                conn.execute("INSERT INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(key) DO NOTHING",
                             (key, value, None, now_iso()))
        admin_sql = ("INSERT IGNORE INTO admin_users (username, password_hash, display_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)"
                     if DATABASE_URL.startswith("mysql") else
                     "INSERT INTO admin_users (username, password_hash, display_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(username) DO NOTHING")
        conn.execute(admin_sql, ("admin", hash_password("admin123"), "管理员", now_iso(), now_iso()))


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
    if DATABASE_URL.startswith("mysql"):
        return
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
