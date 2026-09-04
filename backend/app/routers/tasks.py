import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from app.database import db_session
from app.services.storage import task_storage_dir

from app.schemas import RecoverRequest, WxLoginRequest
from app.services import tasks as task_service
from app.services import wechat_notify, wechat_mp
from app.services.parser import ERROR_MESSAGES
from app.utils.api import fail, ok


logger = logging.getLogger("bscc.tasks")

router = APIRouter(tags=["tasks"])


@router.post("/tasks")
async def create_task(
    background_tasks: BackgroundTasks,
    a_file: UploadFile = File(...),
    b_files: list[UploadFile] = File(...),
    keywords: str | None = Form(None),
    notify_openid: str | None = Form(None),
    notify_unionid: str | None = Form(None),
):
    try:
        return ok(await task_service.create_task(a_file, b_files, keywords, background_tasks, notify_openid, notify_unionid))
    except ValueError as exc:
        code, message = _split_error(str(exc))
        raise fail(code, message)


@router.post("/wx/login")
def wx_login(payload: WxLoginRequest):
    config = wechat_notify.get_notify_config()
    if not config["app_id"] or not config["app_secret"]:
        return ok({"openid": "", "unionid": "", "notify_enabled": False})
    try:
        session = wechat_notify.code2session(config["app_id"], config["app_secret"], payload.code)
    except ValueError as exc:
        raise fail("WX_LOGIN_FAILED", str(exc), 400)
    return ok({"openid": session["openid"], "unionid": session.get("unionid", ""), "notify_enabled": config["enabled"]})


@router.get("/wechat/mp/callback")
def wechat_mp_verify(
    signature: str = Query(""),
    timestamp: str = Query(""),
    nonce: str = Query(""),
    echostr: str = Query(""),
):
    config = wechat_mp.get_mp_config()
    if not wechat_mp.verify_signature(config["verify_token"], signature, timestamp, nonce):
        logger.warning("mp verify rejected: signature mismatch (check mp_verify_token)")
        return PlainTextResponse("forbidden", status_code=403)
    logger.info("mp verify ok: 服务号服务器配置校验通过")
    return PlainTextResponse(echostr)


@router.post("/wechat/mp/callback")
async def wechat_mp_callback(request: Request):
    config = wechat_mp.get_mp_config()
    params = request.query_params
    signature = params.get("signature", "")
    timestamp = params.get("timestamp", "")
    nonce = params.get("nonce", "")
    if not wechat_mp.verify_signature(config["verify_token"], signature, timestamp, nonce):
        logger.warning("mp callback rejected: signature verify failed (check mp_verify_token)")
        return PlainTextResponse("forbidden", status_code=403)
    body = (await request.body()).decode("utf-8", errors="ignore")
    logger.info("mp callback received len=%s body=%s", len(body), body[:300])
    try:
        event = wechat_mp.parse_event_xml(body)
    except Exception as exc:
        logger.warning("mp callback parse failed err=%s body=%s", exc, body[:300])
        # 明文模式异常也按 success 应答，避免微信重复推送
        return PlainTextResponse("success")
    msg_type = event.get("MsgType", "")
    logger.info(
        "mp callback parsed msgtype=%s event=%s from=%s unionid=%s",
        msg_type,
        event.get("Event", ""),
        event.get("FromUserName", ""),
        event.get("UnionID", ""),
    )
    if not msg_type:
        logger.warning(
            "mp callback msgtype empty: 若 body 含 Encrypt 节点，说明服务号后台"
            "「消息加解密方式」未选明文模式，后端无解密逻辑，事件将被丢弃"
        )
    try:
        return PlainTextResponse(wechat_mp.handle_callback_event(event))
    except Exception as exc:
        logger.warning("mp callback handle failed err=%s", exc)
        return PlainTextResponse("success")


@router.get("/wechat/mp/qrcode")
def wechat_mp_qrcode(openid: str = Query(""), task_no: str = Query("")):
    """生成带场景值的服务号关注二维码。

    场景值携带小程序 openid，用户扫码关注后回调事件的 EventKey 会把该值带回，
    后端据此直接建立 (小程序 openid, 服务号 openid) 绑定，无需依赖微信开放平台的
    unionid。返回 base64 data URL，小程序无需额外配置 downloadFile 合法域名。

    场景值来源优先级：显式 openid > 任务号对应的任务 notify_openid。
    """
    config = wechat_mp.get_mp_config()
    if not config["enabled"]:
        return ok({"data_url": "", "bound": False, "reason": "mp_disabled"})
    if not openid and task_no:
        with db_session() as conn:
            row = conn.execute(
                "SELECT notify_openid FROM tasks WHERE task_no = ?", (task_no,)
            ).fetchone()
        openid = (row["notify_openid"] or "") if row else ""
    if not openid:
        return ok({"data_url": "", "bound": False, "reason": "no_openid"})
    bound = wechat_mp.is_mini_bound(openid)
    data_url = wechat_mp.get_mp_qrcode_data_url(openid)
    if not data_url:
        return ok({"data_url": "", "bound": bound, "reason": "generate_failed"})
    return ok({"data_url": data_url, "bound": bound, "reason": ""})


@router.get("/wechat/mini/qrcode")
def wechat_mini_qrcode(task_no: str = Query(""), page: str = Query("results")):
    """生成带任务号场景值的小程序码（跨端接力）。

    BS 端展示该码，微信扫码直达该任务的进度页/结果页。
    page 取 progress | results，分别对应任务进行中与已完成场景。
    """
    if not task_no:
        return ok({"data_url": "", "reason": "no_task"})
    with db_session() as conn:
        row = conn.execute("SELECT task_no FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
    if not row:
        return ok({"data_url": "", "reason": "task_not_found"})
    data_url = wechat_notify.get_mini_task_qrcode_data_url(task_no, page)
    if not data_url:
        return ok({"data_url": "", "reason": "generate_failed"})
    return ok({"data_url": data_url, "reason": ""})


@router.get("/tasks/{task_no}/status")
def task_status(task_no: str):
    try:
        return ok(task_service.get_status(task_no))
    except ValueError:
        raise fail("TASK_NOT_FOUND", "任务不存在", 404)


@router.get("/tasks/{task_no}/summary")
def task_summary(task_no: str):
    try:
        return ok(task_service.get_summary(task_no))
    except ValueError:
        raise fail("TASK_NOT_FOUND", "任务不存在", 404)


@router.get("/tasks/{task_no}/results/{compare_result_id}/preview")
def result_preview(task_no: str, compare_result_id: int):
    try:
        return ok(task_service.get_preview(task_no, compare_result_id))
    except ValueError:
        raise fail("TASK_NOT_FOUND", "任务或结果不存在", 404)


@router.get("/tasks/{task_no}/results/{compare_result_id}/detail")
def result_detail(task_no: str, compare_result_id: int):
    try:
        return ok(task_service.get_detail(task_no, compare_result_id))
    except PermissionError:
        raise fail("ORDER_NOT_PAID", "订单未支付", 402)
    except ValueError:
        raise fail("TASK_NOT_FOUND", "任务或结果不存在", 404)


@router.post("/recover")
def recover(payload: RecoverRequest):
    try:
        return ok(task_service.recover(payload.task_no, payload.order_no, payload.contact))
    except ValueError as exc:
        code, message = _split_error(str(exc))
        raise fail(code, message, 404 if code.endswith("NOT_FOUND") else 400)


@router.get("/tasks/{task_no}/file/a")
def download_file_a(task_no: str):
    with db_session() as conn:
        task = conn.execute("SELECT id FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise fail("TASK_NOT_FOUND", "任务不存在", 404)
        file = conn.execute(
            "SELECT original_name, stored_name FROM task_files WHERE task_id = ? AND role = 'A' LIMIT 1",
            (task["id"],),
        ).fetchone()
        if not file:
            raise fail("FILE_NOT_FOUND", "文件不存在", 404)
        path = task_storage_dir(task_no) / "uploads" / "A" / file["stored_name"]
        if not path.exists():
            raise fail("FILE_NOT_FOUND", "文件不存在", 404)
        return FileResponse(path, filename=file["original_name"])


@router.get("/tasks/{task_no}/file/b/{result_id}")
def download_file_b(task_no: str, result_id: int):
    with db_session() as conn:
        task = conn.execute("SELECT id FROM tasks WHERE task_no = ?", (task_no,)).fetchone()
        if not task:
            raise fail("TASK_NOT_FOUND", "任务不存在", 404)
        result = conn.execute(
            "SELECT b_file_id FROM compare_results WHERE id = ? AND task_id = ?",
            (result_id, task["id"]),
        ).fetchone()
        if not result:
            raise fail("RESULT_NOT_FOUND", "结果不存在", 404)
        file = conn.execute(
            "SELECT original_name, stored_name FROM task_files WHERE id = ?",
            (result["b_file_id"],),
        ).fetchone()
        if not file:
            raise fail("FILE_NOT_FOUND", "文件不存在", 404)
        path = task_storage_dir(task_no) / "uploads" / "B" / file["stored_name"]
        if not path.exists():
            raise fail("FILE_NOT_FOUND", "文件不存在", 404)
        return FileResponse(path, filename=file["original_name"])

def _split_error(raw: str) -> tuple[str, str]:
    if ":" in raw:
        code, message = raw.split(":", 1)
        return code, message
    messages = {
        **ERROR_MESSAGES,
        "VALIDATION_ERROR": "请求参数错误",
        "TASK_NOT_FOUND": "任务不存在",
        "ORDER_NOT_PAID": "订单未支付",
    }
    return raw, messages.get(raw, raw)
