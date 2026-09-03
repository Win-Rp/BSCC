"""订阅消息通知链路单元测试（不依赖网络与真实微信凭据）。"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import app.services.wechat_notify as wn

orig_send_subscribe_message = wn.send_subscribe_message

passed = 0
failed = 0


def check(cond, msg):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + msg)
    passed += 1 if cond else 0
    failed += 0 if cond else 1


# ---------- get_notify_config：从 settings 读取 ----------
captured_sql = {}


class FakeRow(dict):
    def __init__(self, data):
        super().__init__(data)

    def __getitem__(self, key):
        return dict.get(self, key)


def fake_db_session(rows=None, task_rows=None):
    settings_rows = rows or []
    task_rows = task_rows or []

    class FakeResult:
        def __init__(self, data):
            self._data = data

        def fetchall(self):
            return self._data

        def fetchone(self):
            return self._data[0] if self._data else None

    def factory():
        class FakeConn:
            def execute(self, sql, params=()):
                captured_sql["last"] = sql
                if "FROM tasks" in sql:
                    return FakeResult(task_rows)
                return FakeResult(settings_rows)

        class Ctx:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, *a):
                return False

        return Ctx()

    return factory


rows = [
    FakeRow({"key": "notify_enabled", "value": "true"}),
    FakeRow({"key": "wechat_app_id", "value": "wx123"}),
    FakeRow({"key": "wechat_app_secret", "value": "secret456"}),
    FakeRow({"key": "notify_template_id", "value": "0EWR6EdE5PZwTy3op4CIwxMH950vcLvBdPT5tBD1jkA"}),
]
wn.db_session = fake_db_session(rows)
config = wn.get_notify_config()
check(config["enabled"] is True, "配置齐全时 notify enabled")
check(config["app_id"] == "wx123" and config["app_secret"] == "secret456", "app_id/secret 读取正确")
check(config["template_id"] == "0EWR6EdE5PZwTy3op4CIwxMH950vcLvBdPT5tBD1jkA", "模板 ID 读取正确")

rows_disabled = [
    FakeRow({"key": "notify_enabled", "value": "false"}),
    FakeRow({"key": "wechat_app_id", "value": "wx123"}),
    FakeRow({"key": "wechat_app_secret", "value": "secret456"}),
    FakeRow({"key": "notify_template_id", "value": "tpl"}),
]
wn.db_session = fake_db_session(rows_disabled)
check(wn.get_notify_config()["enabled"] is False, "notify_enabled=false 时关闭")

# 小程序专用 AppID：优先使用，未配置时回退支付 AppID
rows_mini = [
    FakeRow({"key": "notify_enabled", "value": "true"}),
    FakeRow({"key": "wechat_app_id", "value": "wxPAY"}),
    FakeRow({"key": "wechat_mini_app_id", "value": "wxMINI"}),
    FakeRow({"key": "wechat_app_secret", "value": "secret456"}),
    FakeRow({"key": "notify_template_id", "value": "tpl"}),
]
wn.db_session = fake_db_session(rows_mini)
check(wn.get_notify_config()["app_id"] == "wxMINI", "优先使用小程序专用 AppID")

rows_nomini = [
    FakeRow({"key": "notify_enabled", "value": "true"}),
    FakeRow({"key": "wechat_app_id", "value": "wxPAY"}),
    FakeRow({"key": "wechat_app_secret", "value": "secret456"}),
    FakeRow({"key": "notify_template_id", "value": "tpl"}),
]
wn.db_session = fake_db_session(rows_nomini)
check(wn.get_notify_config()["app_id"] == "wxPAY", "未配置小程序 AppID 时回退支付 AppID")

rows_partial = [
    FakeRow({"key": "notify_enabled", "value": "true"}),
    FakeRow({"key": "wechat_app_id", "value": "wx123"}),
    FakeRow({"key": "wechat_app_secret", "value": ""}),
    FakeRow({"key": "notify_template_id", "value": "tpl"}),
]
wn.db_session = fake_db_session(rows_partial)
check(wn.get_notify_config()["enabled"] is False, "缺少 app_secret 时自动禁用")

# ---------- notify_task_finished：无 openid / 未启用 时不发送 ----------
# 屏蔽服务号优先链路，专注验证小程序订阅消息兜底
import app.services.wechat_mp as wmp_module

wmp_module.mp_notify_task_finished = lambda task_no, status_key: False

wn.db_session = fake_db_session(rows)
sent_calls = []


SEND_ARG_NAMES = ["app_id", "app_secret", "template_id", "openid", "service_no", "service_result", "page"]


def fake_send(*args, **kwargs):
    call = dict(zip(SEND_ARG_NAMES, args))
    call.update(kwargs)
    sent_calls.append(call)
    return True


wn.send_subscribe_message = fake_send
task_with_openid = [FakeRow({"notify_openid": "oABC", "notify_authorized_at": "2026-01-01"})]
wn.db_session = fake_db_session(rows, task_rows=task_with_openid)
check(wn.notify_task_finished("T1", "completed") is True, "有 openid 时调用推送")
check(len(sent_calls) == 1 and sent_calls[0]["openid"] == "oABC", "推送使用任务绑定的 openid")
check(sent_calls[0]["service_no"] == "T1" and sent_calls[0]["service_result"] == "查重完成", "推送内容正确")
check(sent_calls[0]["page"] == "pages/results/index?taskNo=T1", "通知跳转直达结果页并携带任务号")

check(wn.notify_task_finished("T5", "failed") is True, "失败任务同样触发兜底推送")
check(sent_calls[-1]["service_result"] == "查重异常", "失败状态映射为查重异常")
check(wn.notify_task_finished("T6", "awaiting_payment") is True, "待解锁任务触发兜底推送")
check(sent_calls[-1]["service_result"] == "完成待解锁", "待解锁状态映射为完成待解锁")

wn.db_session = fake_db_session(rows, task_rows=[FakeRow({"notify_openid": None, "notify_authorized_at": None})])
check(wn.notify_task_finished("T2", "completed") is False, "任务未绑定 openid 时不推送")

wn.db_session = fake_db_session(rows_disabled, task_rows=task_with_openid)
check(wn.notify_task_finished("T3", "completed") is False, "功能未启用时不推送")

# 推送抛异常不影响主流程
def bad_send(**kwargs):
    raise RuntimeError("network down")


wn.send_subscribe_message = bad_send
wn.db_session = fake_db_session(rows, task_rows=task_with_openid)
check(wn.notify_task_finished("T4", "completed") is False, "推送异常时静默返回 False")

# ---------- send_subscribe_message：报文格式 ----------
class FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


captured_http = []


class FakeClient:
    def __init__(self, timeout=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, json=None):
        captured_http.append(("POST", url, json))
        return FakeResp({"errcode": 0, "errmsg": "ok"})

    def get(self, url, params=None):
        captured_http.append(("GET", url, params))
        return FakeResp({"access_token": "TOKEN123", "expires_in": 7200})


wn.httpx.Client = FakeClient
wn.send_subscribe_message = orig_send_subscribe_message
wn._fields_cache = {}
wn._token_cache = {"access_token": "", "expires_at": 0.0}
result = wn.send_subscribe_message("wx123", "secret", "TPL", "oXYZ", "T20260902102534B281", "查重完成")
check(result is True, "订阅消息发送成功")
url = captured_http[-1][1]
check("TOKEN123" in url, "请求携带 access_token")
payload = captured_http[-1][2]
check(payload["touser"] == "oXYZ" and payload["template_id"] == "TPL", "touser/template_id 正确")
check(payload["page"] == "pages/results/index", "点击通知直达结果页")
check(payload["data"]["character_string1"]["value"] == "T20260902102534B281", "服务编号=任务号")
check(payload["data"]["phrase2"]["value"] == "查重完成", "服务结果=完成状态（截断到 5 字）")

# token 缓存：第二次调用不再请求 token
captured_http.clear()
wn.send_subscribe_message("wx123", "secret", "TPL", "oXYZ", "T1", "ok")
token_requests = [c for c in captured_http if c[0] == "GET"]
check(len(token_requests) == 0, "access_token 缓存生效（未重复获取）")

# 微信返回错误码
class FakeRespErr(FakeResp):
    def json(self):
        return {"errcode": 43101, "errmsg": "user refuse"}


class FakeClientErr(FakeClient):
    def post(self, url, json=None):
        return FakeRespErr({})


wn.httpx.Client = FakeClientErr
wn._token_cache = {"access_token": "TOKEN123", "expires_at": 1e12}
check(wn.send_subscribe_message("wx123", "secret", "TPL", "oXYZ", "T1", "ok") is False, "用户未订阅(errcode 43101)返回 False 不抛错")

# ---------- 模板字段自动探测（gettemplate 接口） ----------
wn._fields_cache = {}
wn._token_cache = {"access_token": "TOKEN123", "expires_at": 1e12}


class FakeClientTpl(FakeClient):
    def get(self, url, params=None):
        captured_http.append(("GET", url, params))
        if "newtmpl/gettemplate" in url:
            return FakeResp(
                {
                    "errcode": 0,
                    "data": [
                        {"priTmplId": "OTHER", "content": "x{{thing1.DATA}}"},
                        {"priTmplId": "TPLX", "content": "服务编号{{character_string1.DATA}}\n服务结果{{thing2.DATA}}"},
                    ],
                }
            )
        return FakeResp({"access_token": "TOKEN123", "expires_in": 7200})


wn.httpx.Client = FakeClientTpl
captured_http.clear()
check(wn.send_subscribe_message("wx123", "secret", "TPLX", "oXYZ", "B" * 40, "查重完成，请查看结果") is True, "字段探测后发送成功")
payload = captured_http[-1][2]
check(set(payload["data"].keys()) == {"character_string1", "thing2"}, "gettemplate 探测出真实字段名")
check(payload["data"]["character_string1"]["value"] == "B" * 32, "character_string 按类型截断到 32 字")
check(payload["data"]["thing2"]["value"] == "查重完成，请查看结果", "thing 字段 20 字内保留原文")

captured_http.clear()
wn.send_subscribe_message("wx123", "secret", "TPLX", "oXYZ", "T1", "ok")
tpl_gets = [c for c in captured_http if c[0] == "GET"]
check(len(tpl_gets) == 0, "字段名探测结果缓存生效（不再重复探测）")

# ---------- _clip：截断与尾部标点清理 ----------
check(wn._clip("查重完成，请查看结果", 5) == "查重完成", "截断后去除尾部标点")
check(wn._clip("ABCDEFGH", 5) == "ABCDE", "普通文本按上限截断")
check(wn._clip("，。", 1) == "，", "截断后仅剩标点时回退原截断")
check(wn._clip("  查重完成  ", 20) == "查重完成", "首尾空白被清理")

# ---------- code2session ----------
captured_http.clear()


class FakeClientLogin(FakeClient):
    def get(self, url, params=None):
        captured_http.append(("GET", url, params))
        return FakeResp({"openid": "oLOGIN", "session_key": "sk"})


wn.httpx.Client = FakeClientLogin
session = wn.code2session("wx123", "secret", "CODE_X")
check(session["openid"] == "oLOGIN", "code2session 成功返回 openid")


class FakeClientLoginErr(FakeClient):
    def get(self, url, params=None):
        return FakeResp({"errcode": 40029, "errmsg": "invalid code"})


wn.httpx.Client = FakeClientLoginErr
try:
    wn.code2session("wx123", "secret", "BAD")
    check(False, "无效 code 应抛错")
except ValueError as exc:
    check("WX_CODE2SESSION_FAILED" in str(exc), "无效 code 抛出 WX_CODE2SESSION_FAILED")

print(f"\n共 {passed} 项断言，失败 {failed} 项")
sys.exit(1 if failed else 0)
