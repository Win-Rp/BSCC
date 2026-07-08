from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.schemas import OrderCreate
from app.services import orders as order_service
from app.services.alipay_service import check_notify_sign
from app.services.wechatpay_service import (
    check_notify_sign as check_wechat_notify_sign,
    notify_fail_xml,
    notify_success_xml,
    parse_xml,
)
from app.utils.api import fail, ok


router = APIRouter(tags=["orders"])


@router.post("/orders")
def create_order(payload: OrderCreate, request: Request):
    try:
        client_ip = request.client.host if request.client else "127.0.0.1"
        return ok(
            order_service.create_order(
                payload.task_no,
                payload.contact,
                payload.pay_channel or "alipay",
                client_ip,
                payload.locale,
            )
        )
    except ValueError as exc:
        code = str(exc)
        message_map = {
            "VALIDATION_ERROR": "订单创建失败",
            "TASK_NOT_FOUND": "任务不存在",
            "UNSUPPORTED_PAY_CHANNEL": "不支持的支付方式",
            "PAY_CHANNEL_DISABLED": "当前支付方式未启用，请先在后台完成配置",
        }
        raise fail(code, message_map.get(code, code), 400)


@router.get("/orders/{order_no}/status")
def order_status(order_no: str):
    try:
        return ok(order_service.get_order_status(order_no))
    except ValueError:
        raise fail("ORDER_NOT_FOUND", "订单不存在", 404)


@router.post("/payments/alipay/notify")
async def alipay_notify(request: Request):
    """
    接收支付宝异步通知
    """
    data = dict(await request.form())
    
    # 支持以前的前端 mock (只有 order_no)
    if "order_no" in data and len(data) == 1:
        try:
            order_service.mark_order_paid(data["order_no"])
        except ValueError:
            return "fail"
        return "success"
        
    # 真实的支付宝通知处理
    try:
        # 1. 验证签名
        if not check_notify_sign(data):
            print("支付宝异步通知验签失败")
            return "fail"
            
        # 2. 获取订单号和交易状态
        out_trade_no = data.get("out_trade_no")
        trade_status = data.get("trade_status")
        
        # 3. 处理业务逻辑
        if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            # 注意：此处应做幂等处理，mark_order_paid 内部若已经是 paid 不会报错即可
            order_service.mark_order_paid(out_trade_no)
            
        return "success"
    except Exception as e:
        print(f"处理支付宝通知时发生错误: {e}")
        return "fail"


@router.post("/payments/wechat/notify")
async def wechat_notify(request: Request):
    try:
        payload = (await request.body()).decode("utf-8")
        if not payload.strip():
            return Response(content=notify_fail_xml("EMPTY_BODY"), media_type="application/xml")

        data = parse_xml(payload)
        if not check_wechat_notify_sign(data):
            print("微信支付异步通知验签失败")
            return Response(content=notify_fail_xml("SIGNERROR"), media_type="application/xml")

        if data.get("return_code") == "SUCCESS" and data.get("result_code") == "SUCCESS":
            order_no = data.get("out_trade_no", "")
            if order_no:
                order_service.mark_order_paid(order_no)
        return Response(content=notify_success_xml(), media_type="application/xml")
    except Exception as exc:
        print(f"处理微信支付通知时发生错误: {exc}")
        return Response(content=notify_fail_xml("FAIL"), media_type="application/xml")
