"""诊断微信小程序 / 服务号的 AppID 与 AppSecret 是否配对。

用法（在后端容器内执行）：

    docker exec bscc-backend python scripts/diagnose_wechat.py

原理
----
code2session 依赖一次性 code（5 分钟有效且只能用一次），难以抓取复现。
改用 client_credential 获取 access_token 的接口来验证 (appid, secret)
配对关系：该接口不需要 code，可随时执行。

- 返回 access_token  -> 配对正确
- errcode 40125      -> secret 与该 appid 不匹配（secret 错、或拿错账号的 secret）
- errcode 40013      -> appid 不存在

脚本只回显密钥的前 4 位与后 4 位，不打印完整值。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # noqa: E402

from app.database import db_session  # noqa: E402

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"

# 统一使用 ? 占位符：SQLite 原生支持；MySQL 经 MySQLConnection.execute()
# 内部 sql.replace("?", "%s") 自动转换，故同一套 SQL 在两种后端均可执行
SETTINGS_KEYS = (
    "notify_enabled", "wechat_app_id", "wechat_mini_app_id",
    "wechat_app_secret", "notify_template_id",
    "mp_app_id", "mp_app_secret", "mp_notify_template_id",
)
SETTINGS_SQL = "SELECT key, value FROM settings WHERE key IN ({})".format(
    ",".join("?" * len(SETTINGS_KEYS))
)

# 微信 AppSecret 固定 32 位
SECRET_LEN = 32


def mask(value: str) -> str:
    """密钥脱敏，只保留首尾各 4 位，并标注长度以便发现截断或脏值。"""
    if not value:
        return "(空)"
    if len(value) <= 8:
        return "*" * len(value) + f"  [len={len(value)}]"
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}  [len={len(value)}]"


def load_settings() -> dict:
    with db_session() as conn:
        rows = conn.execute(SETTINGS_SQL, SETTINGS_KEYS).fetchall()
    return {row["key"]: (row["value"] or "") for row in rows}


def probe(app_id: str, app_secret: str) -> tuple[str, str]:
    """用 client_credential 验证 appid 与 secret 是否配对。"""
    if not app_id or not app_secret:
        return "SKIP", "AppID 或 AppSecret 为空"
    try:
        resp = httpx.get(
            TOKEN_URL,
            params={"grant_type": "client_credential", "appid": app_id, "secret": app_secret},
            timeout=10,
        )
        data = resp.json()
    except Exception as exc:  # 网络层异常，不影响其它组合的验证
        return "ERROR", f"请求失败: {exc}"
    if data.get("access_token"):
        return "OK", "配对正确"
    return "FAIL", f"{data.get('errcode')}: {data.get('errmsg')}"


def report(label: str, app_id_key: str, app_id: str, secret_key: str, secret: str) -> None:
    status, detail = probe(app_id, secret)
    print(f"\n[{label}]  ->  {status}")
    print(f"  {app_id_key} = {app_id or '(空)'}")
    print(f"  {secret_key} = {mask(secret)}")
    print(f"  结果: {detail}")
    if secret and len(secret) != SECRET_LEN and status != "OK":
        print(f"  !! AppSecret 长度 {len(secret)}，微信固定为 {SECRET_LEN} 位，"
              f"疑似被截断或填入了非密钥内容")


def main() -> int:
    s = load_settings()

    print("=" * 68)
    print("微信配置诊断")
    print("=" * 68)
    print(f"notify_enabled      = {s.get('notify_enabled', '(空)')}")
    print(f"notify_template_id  = {s.get('notify_template_id', '(空)')}")
    print(f"mp_notify_template_id = {s.get('mp_notify_template_id', '(空)')}")

    # 复现 wechat_notify.get_notify_config() 的取值逻辑
    mini_app_id = s.get("wechat_mini_app_id") or s.get("wechat_app_id", "")
    mini_secret = s.get("wechat_app_secret", "")

    report(
        "① 小程序订阅通道（/api/wx/login 实际使用）",
        "wechat_mini_app_id (回落 wechat_app_id)", mini_app_id,
        "wechat_app_secret", mini_secret,
    )

    # 排查是否把服务号的 secret 混用到了小程序配置
    pay_app_id = s.get("wechat_app_id", "")
    if pay_app_id and pay_app_id != mini_app_id:
        report(
            "② 支付 AppID + wechat_app_secret（排查密钥混用）",
            "wechat_app_id", pay_app_id,
            "wechat_app_secret", mini_secret,
        )

    mp_app_id = s.get("mp_app_id", "")
    report(
        "③ 服务号模板通道",
        "mp_app_id", mp_app_id,
        "mp_app_secret", s.get("mp_app_secret", ""),
    )

    print("\n" + "=" * 68)
    print("判定：只有 ① 为 OK，订阅通知才能换到 openid。")
    print("若 ① 报 40125，说明 wechat_app_secret 不是该小程序 AppID 的密钥，")
    print("需到 mp.weixin.qq.com -> 设置与开发 -> 开发管理 -> 开发设置 重置后回填。")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
