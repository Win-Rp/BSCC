"""服务号用户运营链路单元测试（不依赖网络与真实微信凭据）。"""
import hashlib
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import app.services.wechat_mp as mp

passed = 0
failed = 0


def check(cond, msg):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + msg)
    passed += 1 if cond else 0
    failed += 0 if cond else 1


# ---------- verify_signature ----------
token = "mytoken"
timestamp = "1700000000"
nonce = "nonce123"
sig = hashlib.sha1("".join(sorted([token, timestamp, nonce])).encode("utf-8")).hexdigest()
check(mp.verify_signature(token, sig, timestamp, nonce) is True, "verify_signature 合法签名通过")
check(mp.verify_signature(token, "bad" + sig[3:], timestamp, nonce) is False, "verify_signature 非法签名拒绝")
check(mp.verify_signature("", sig, timestamp, nonce) is False, "verify_signature 空 token 拒绝")
check(mp.verify_signature(token, "", timestamp, nonce) is False, "verify_signature 空 signature 拒绝")

# ---------- parse_event_xml ----------
xml = """<xml>
<ToUserName><![CDATA[gh_abc]]></ToUserName>
<FromUserName><![CDATA[oMP_openid_1]]></FromUserName>
<CreateTime>1700000000</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[subscribe]]></Event>
<UnionID><![CDATA[union_123]]></UnionID>
</xml>"""
event = mp.parse_event_xml(xml)
check(event["MsgType"] == "event", "parse_event_xml 解析 MsgType")
check(event["FromUserName"] == "oMP_openid_1", "parse_event_xml 解析 FromUserName")
check(event["UnionID"] == "union_123", "parse_event_xml 解析 UnionID")
check(mp.parse_event_xml("<xml><MsgType><![CDATA[text]]></MsgType></xml>")["MsgType"] == "text", "parse_event_xml 解析普通消息类型")

# ---------- fake db ----------
state = {"followers": {}, "seq": 0}
executed_sql = {"list": []}


class FakeResult:
    def __init__(self, data):
        self._data = data

    def fetchall(self):
        return self._data

    def fetchone(self):
        return self._data[0] if self._data else None


class FakeConn:
    def execute(self, sql, params=()):
        executed_sql["list"].append((sql, params))
        if "FROM mp_followers WHERE mp_openid" in sql:
            openid = params[0]
            row = state["followers"].get(openid)
            return FakeResult([dict(row)] if row else [])
        if "FROM mp_followers WHERE union_id" in sql:
            for item in state["followers"].values():
                if item["union_id"] == params[0] and item["is_active"] == 1:
                    return FakeResult([dict(item)])
            return FakeResult([])
        if "FROM tasks" in sql:
            return FakeResult([dict(state.get("task_row") or {"notify_unionid": state.get("task_unionid")})])
        if "FROM settings" in sql:
            rows = [
                {"key": "mp_notify_enabled", "value": state.get("mp_notify_enabled", "true")},
                {"key": "mp_app_id", "value": state.get("mp_app_id", "wxmp123")},
                {"key": "mp_app_secret", "value": state.get("mp_app_secret", "secret")},
                {"key": "mp_verify_token", "value": state.get("mp_verify_token", "mytoken")},
                {"key": "mp_notify_template_id", "value": state.get("mp_notify_template_id", "TMPL1")},
                {"key": "wechat_mini_app_id", "value": state.get("wechat_mini_app_id", "wxmini1")},
                {"key": "wechat_app_id", "value": "wxpay1"},
            ]
            return FakeResult(rows)
        if "INSERT INTO mp_followers" in sql:
            state["seq"] += 1
            union_id, openid, active, _, _ = params
            state["followers"][openid] = {
                "id": state["seq"], "union_id": union_id, "mp_openid": openid,
                "is_active": active, "subscribed_at": "", "updated_at": "",
            }
            return FakeResult([])
        if "UPDATE mp_followers" in sql:
            union_id, active, _, rid = params
            for item in state["followers"].values():
                if item["id"] == rid:
                    item["union_id"] = union_id
                    item["is_active"] = active
            return FakeResult([])
        return FakeResult([])


mp.db_session = types.SimpleNamespace()
_mp_db = types.SimpleNamespace()


class _DbCtx:
    def __init__(self):
        self.conn = FakeConn()

    def __enter__(self):
        return self.conn

    def __exit__(self, *a):
        return False


mp.db_session = lambda: _DbCtx()

# ---------- upsert_follower ----------
mp.upsert_follower("union_123", "oMP_openid_1", active=True)
check(state["followers"]["oMP_openid_1"]["union_id"] == "union_123", "upsert_follower 新增粉丝写入 unionid")
check(state["followers"]["oMP_openid_1"]["is_active"] == 1, "upsert_follower 新增粉丝为活跃")

mp.upsert_follower("union_123", "oMP_openid_1", active=False)
check(state["followers"]["oMP_openid_1"]["is_active"] == 0, "upsert_follower 取关后置为不活跃")

mp.upsert_follower("", "oMP_openid_1", active=True)
check(state["followers"]["oMP_openid_1"]["union_id"] == "union_123", "upsert_follower 事件无 unionid 时保留旧值")

mp.upsert_follower("union_999", "oMP_openid_2", active=True)
check(len(state["followers"]) == 2, "upsert_follower 不同 openid 各存一条")

# ---------- handle_callback_event ----------
ret = mp.handle_callback_event(event)
check(ret == "success", "handle_callback_event 订阅事件返回 success")
check(state["followers"]["oMP_openid_1"]["is_active"] == 1, "handle_callback_event 订阅事件激活粉丝")

unsub_xml = """<xml>
<ToUserName><![CDATA[gh_abc]]></ToUserName>
<FromUserName><![CDATA[oMP_openid_1]]></FromUserName>
<CreateTime>1700000001</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[unsubscribe]]></Event>
</xml>"""
mp.handle_callback_event(mp.parse_event_xml(unsub_xml))
check(state["followers"]["oMP_openid_1"]["is_active"] == 0, "handle_callback_event 取关事件置为不活跃")

check(mp.handle_callback_event({"MsgType": "text"}) == "success", "handle_callback_event 非事件消息直接 success")
check(mp.handle_callback_event({"MsgType": "event", "Event": "CLICK", "FromUserName": ""}) == "success", "handle_callback_event 无 openid 容错")

# ---------- get_mp_config ----------
config = mp.get_mp_config()
check(config["enabled"] is True, "get_mp_config 配置齐全时启用")
check(config["app_id"] == "wxmp123", "get_mp_config 读取服务号 AppID")
check(config["mini_app_id"] == "wxmini1", "get_mp_config 跳转小程序优先用小程序 AppID")

state["mp_app_id"] = ""
check(mp.get_mp_config()["enabled"] is False, "get_mp_config 缺 AppID 时停用")

state["mp_app_id"] = "wxmp123"
state["mp_notify_enabled"] = "false"
check(mp.get_mp_config()["enabled"] is False, "get_mp_config 开关关闭时停用")
state["mp_notify_enabled"] = "true"

# ---------- _format_time ----------
check(mp._format_time("2026-09-03T10:25:00+08:00") == "2026-09-03 10:25", "_format_time ISO 带时区转分钟精度")
check(mp._format_time("2026-09-03T10:25:00") == "2026-09-03 10:25", "_format_time ISO 无时区转换")
check(mp._format_time("") == "", "_format_time 空值返回空串")
check(mp._format_time("not-a-time") == "not-a-time"[:16].replace("T", " "), "_format_time 非法值降级截断")

# ---------- 状态映射 ----------
check(mp.MP_STATUS_TEXT["completed"] == "查重完成", "状态映射 completed")
check(mp.MP_STATUS_TEXT["awaiting_payment"] == "查重完成", "状态映射 awaiting_payment 也为查重完成")
check(mp.MP_STATUS_TEXT["failed"] == "查重异常", "状态映射 failed")
check(mp.TASK_NAME_TEXT == "标书查重", "任务名称常量为模板枚举值")

# ---------- mp_notify_task_finished ----------
state["task_unionid"] = "union_123"
state["task_row"] = {
    "notify_unionid": "union_123",
    "created_at": "2026-09-03T10:00:00+08:00",
    "completed_at": "2026-09-03T10:25:00+08:00",
}

sent = {}


def fake_send(app_id, app_secret, template_id, mp_openid, task_no, start_time, end_time, status, mini_app_id="", page=""):
    sent.update(
        app_id=app_id, template_id=template_id, mp_openid=mp_openid,
        task_no=task_no, start_time=start_time, end_time=end_time,
        status=status, mini_app_id=mini_app_id, page=page,
    )
    return True


orig_send = mp.send_mp_template_message
mp.send_mp_template_message = fake_send

# 当前粉丝为取关状态，按 union 查不到活跃记录
check(mp.mp_notify_task_finished("T1", "completed") is False, "mp_notify 未关注（不活跃）时不发送")

# 重新关注后可发送
mp.upsert_follower("union_123", "oMP_openid_1", active=True)
check(mp.mp_notify_task_finished("T1", "completed") is True, "mp_notify 已关注用户成功发送")
check(sent["task_no"] == "T1" and sent["status"] == "查重完成", "mp_notify 携带工单编号与状态枚举")
check(sent["start_time"] == "2026-09-03 10:00" and sent["end_time"] == "2026-09-03 10:25", "mp_notify 开始/结束时间取任务字段")
check(sent["mini_app_id"] == "wxmini1", "mp_notify 跳转小程序 AppID 正确")
check(sent["page"] == "pages/results/index?taskNo=T1", "mp_notify 跳转页面携带任务号")

# 失败状态映射为「查重异常」
check(mp.mp_notify_task_finished("T5", "failed") is True, "mp_notify 失败任务发送成功")
check(sent["status"] == "查重异常", "mp_notify 失败任务状态为查重异常")

# 结束时间为空时回退当前时间（非空字符串）
state["task_row"] = {"notify_unionid": "union_123", "created_at": "2026-09-03T10:00:00+08:00", "completed_at": None}
check(mp.mp_notify_task_finished("T6", "completed") is True, "mp_notify 结束时间缺失时仍发送")
check(len(sent["end_time"]) == len("2026-09-03 10:25"), "mp_notify 结束时间回退为当前时间")

# 任务无 unionid
state["task_unionid"] = None
state["task_row"] = None
check(mp.mp_notify_task_finished("T2", "completed") is False, "mp_notify 任务无 unionid 时不发送")
state["task_unionid"] = "union_404"
check(mp.mp_notify_task_finished("T3", "completed") is False, "mp_notify 用户从未关注时不发送")

# 发送抛异常时静默失败
state["task_unionid"] = "union_123"
state["task_row"] = {"notify_unionid": "union_123", "created_at": "2026-09-03T10:00:00+08:00", "completed_at": "2026-09-03T10:25:00+08:00"}


def raise_send(*a, **k):
    raise RuntimeError("boom")


mp.send_mp_template_message = raise_send
check(mp.mp_notify_task_finished("T4", "completed") is False, "mp_notify 发送异常时返回 False 不抛出")
mp.send_mp_template_message = orig_send

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
