from fastapi import APIRouter

from app.schemas import OrderCreate
from app.services import orders as order_service
from app.utils.api import fail, ok


router = APIRouter(tags=["orders"])


@router.post("/orders")
def create_order(payload: OrderCreate):
    try:
        return ok(order_service.create_order(payload.task_no, payload.contact))
    except ValueError as exc:
        code = str(exc)
        raise fail(code, "订单创建失败" if code == "VALIDATION_ERROR" else "任务不存在", 400)


@router.get("/orders/{order_no}/status")
def order_status(order_no: str):
    try:
        return ok(order_service.get_order_status(order_no))
    except ValueError:
        raise fail("ORDER_NOT_FOUND", "订单不存在", 404)


@router.post("/payments/alipay/notify")
def alipay_notify(order_no: str):
    try:
        order_service.mark_order_paid(order_no)
    except ValueError:
        return "fail"
    return "success"
