"""将 backend/data/bscc.sqlite3 导入 DATABASE_URL 指向的 MySQL。"""
import os
import re
import sqlite3
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql

from app.database import mysql_schema


def main():
    sqlite_path = os.getenv("SQLITE_PATH", "data/bscc.sqlite3")
    target = os.getenv("DATABASE_URL", "mysql://bscc:bscc-change-me@127.0.0.1:3306/bscc")
    parsed = urlparse(target)
    mysql = pymysql.connect(host=parsed.hostname, port=parsed.port or 3306,
                            user=parsed.username, password=parsed.password,
                            database=parsed.path.lstrip("/"), charset="utf8mb4")
    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    with mysql.cursor() as cur:
        schema = mysql_schema()
        for statement in schema.split(";"):
            if statement.strip():
                try:
                    cur.execute(statement)
                except pymysql.err.OperationalError as exc:
                    if exc.args[0] != 1061:
                        raise
        # The database may have been initialized by an earlier image with
        # VARCHAR(255); widen content fields before re-importing source data.
        long_text_columns = {
            "tasks": ("keyword_text", "error_message"),
            "task_files": ("error_message",),
            "compare_results": ("preview_json_path", "detail_json_path", "error_message"),
            "matched_segments": ("a_text", "b_text", "a_position_json", "b_position_json"),
            "keyword_hits": ("hit_text", "position_json", "context_before", "context_after"),
            "metadata_results": ("a_value", "b_value"),
            "format_results": ("a_value", "b_value", "description"),
            "settings": ("value",),
            "operation_logs": ("detail_json",),
        }
        for table, columns in long_text_columns.items():
            for column in columns:
                cur.execute(f"ALTER TABLE `{table}` MODIFY COLUMN `{column}` LONGTEXT NULL")
        tables = [row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            columns = [row[1] for row in source.execute(f"PRAGMA table_info({table})")]
            rows = source.execute(f"SELECT {', '.join(columns)} FROM {table}").fetchall()
            if not rows:
                continue
            # settings is seeded by application startup, so its auto IDs are
            # not stable. Use its unique key instead of importing the SQLite id.
            insert_columns = [c for c in columns if not (table == "settings" and c == "id")]
            value_indexes = [columns.index(c) for c in insert_columns]
            marks = ",".join(["%s"] * len(columns))
            marks = ",".join(["%s"] * len(insert_columns))
            names = ",".join(f"`{name}`" for name in insert_columns)
            assignments = ",".join(f"`{name}`=VALUES(`{name}`)" for name in insert_columns if name not in {"key"})
            sql = f"INSERT INTO `{table}` ({names}) VALUES ({marks})"
            if assignments:
                sql += f" ON DUPLICATE KEY UPDATE {assignments}"
            cur.executemany(sql, [tuple(row[index] for index in value_indexes) for row in rows])
    mysql.commit()
    print(f"迁移完成：{len(tables)} 张表")


if __name__ == "__main__":
    main()
