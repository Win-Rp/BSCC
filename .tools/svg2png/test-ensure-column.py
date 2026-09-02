"""_ensure_column MySQL 分支单测（不依赖真实 MySQL）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import app.database as db

passed = 0
failed = 0


def check(cond, msg):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + msg)
    passed += 1 if cond else 0
    failed += 0 if cond else 1


class FakeCursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class FakeMySQLConn:
    """模拟 MySQLConnection 包装层：记录 SQL，按已有列返回 information_schema 结果。"""

    def __init__(self, existing_columns):
        self.existing = set(existing_columns)
        self.statements = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if "information_schema" in sql:
            column = params[2]
            row = {"cnt": 1 if column in self.existing else 0}
            return FakeCursor(row)
        return None


original_url = db.DATABASE_URL
db.DATABASE_URL = "mysql://user:pass@localhost:3306/bscc_prod"

try:
    # 列缺失 → 应 ALTER，且 TEXT 定义转为 VARCHAR(255)
    conn = FakeMySQLConn(existing_columns=["id", "task_no"])
    db._ensure_column(conn, "tasks", "notify_openid", "TEXT")
    alters = [s for s in conn.statements if "ALTER TABLE" in s[0]]
    check(len(alters) == 1, "MySQL 缺列时执行 ALTER TABLE")
    check(alters[0][0] == "ALTER TABLE tasks ADD COLUMN notify_openid VARCHAR(255)", "TEXT 定义转换为 VARCHAR(255)")

    # 带默认值定义：TEXT NOT NULL DEFAULT 'alipay' → VARCHAR(255) NOT NULL DEFAULT 'alipay'
    conn2 = FakeMySQLConn(existing_columns=[])
    db._ensure_column(conn2, "orders", "pay_channel", "TEXT NOT NULL DEFAULT 'alipay'")
    alters2 = [s for s in conn2.statements if "ALTER TABLE" in s[0]]
    check(
        alters2 and alters2[0][0] == "ALTER TABLE orders ADD COLUMN pay_channel VARCHAR(255) NOT NULL DEFAULT 'alipay'",
        "带 DEFAULT 的 TEXT 定义正确转换",
    )

    # 列已存在 → 不 ALTER
    conn3 = FakeMySQLConn(existing_columns=["notify_openid"])
    db._ensure_column(conn3, "tasks", "notify_openid", "TEXT")
    alters3 = [s for s in conn3.statements if "ALTER TABLE" in s[0]]
    check(len(alters3) == 0, "MySQL 列已存在时不重复 ALTER")

    # information_schema 查询携带库名/表名/列名参数
    info = [s for s in conn.statements if "information_schema" in s[0]][0]
    check(info[1] == ("bscc_prod", "tasks", "notify_openid"), "information_schema 查询参数正确")
finally:
    db.DATABASE_URL = original_url

# ---------- sqlite 分支回归 ----------
import sqlite3

sqlite_conn = sqlite3.connect(":memory:")
sqlite_conn.row_factory = sqlite3.Row
sqlite_conn.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, task_no TEXT)")
db._ensure_column(sqlite_conn, "tasks", "notify_openid", "TEXT")
cols = {r["name"] for r in sqlite_conn.execute("PRAGMA table_info(tasks)").fetchall()}
check("notify_openid" in cols, "sqlite 分支仍正常补列")
db._ensure_column(sqlite_conn, "tasks", "notify_openid", "TEXT")
cols2 = [r["name"] for r in sqlite_conn.execute("PRAGMA table_info(tasks)").fetchall()]
check(cols2.count("notify_openid") == 1, "sqlite 分支不重复补列")

print(f"\n共 {passed} 项断言，失败 {failed} 项")
sys.exit(1 if failed else 0)
