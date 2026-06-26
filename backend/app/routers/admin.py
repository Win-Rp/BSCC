from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import AdminLogin, SettingsUpdate
from app.services import admin as admin_service
from app.services import orders as order_service
from app.utils.api import fail, ok


router = APIRouter(tags=["admin"])
bearer = HTTPBearer()


def _admin(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        return admin_service.require_admin(credentials.credentials)
    except PermissionError:
        raise fail("ADMIN_UNAUTHORIZED", "后台未登录", 401)


@router.post("/login")
def login(payload: AdminLogin):
    try:
        return ok(admin_service.login(payload.username, payload.password))
    except PermissionError:
        raise fail("ADMIN_UNAUTHORIZED", "后台未登录", 401)


@router.get("/orders")
def orders(admin=Depends(_admin)):
    return ok(admin_service.list_orders())


@router.get("/tasks")
def tasks(admin=Depends(_admin)):
    return ok(admin_service.list_tasks())


@router.post("/orders/{order_no}/mark-paid")
def mark_paid(order_no: str, admin=Depends(_admin)):
    try:
        return ok(order_service.mark_order_paid(order_no, admin["id"]))
    except ValueError:
        raise fail("ORDER_NOT_FOUND", "订单不存在", 404)


@router.post("/tasks/{task_no}/retry")
def retry_task(task_no: str, background_tasks: BackgroundTasks, admin=Depends(_admin)):
    try:
        admin_service.retry_task(task_no, admin["id"], background_tasks)
        return ok()
    except ValueError as exc:
        raise fail("TASK_NOT_FOUND", str(exc), 404)


@router.post("/tasks/{task_no}/extend")
def extend_task(task_no: str, admin=Depends(_admin)):
    try:
        admin_service.extend_task(task_no, admin["id"])
        return ok()
    except ValueError as exc:
        raise fail("TASK_NOT_FOUND", str(exc), 404)


@router.delete("/tasks/{task_no}/data")
def delete_task_data(task_no: str, admin=Depends(_admin)):
    try:
        admin_service.delete_task_data(task_no, admin["id"])
        return ok()
    except ValueError as exc:
        raise fail("TASK_NOT_FOUND", str(exc), 404)


@router.get("/logs")
def logs(admin=Depends(_admin)):
    return ok(admin_service.list_logs())


@router.get("/settings")
def settings(admin=Depends(_admin)):
    return ok(admin_service.get_settings())


@router.put("/settings")
def update_settings(payload: SettingsUpdate, admin=Depends(_admin)):
    return ok(admin_service.update_settings(payload.model_dump(), admin["id"]))
