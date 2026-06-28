from fastapi import APIRouter, Depends, BackgroundTasks, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import AdminLogin, AdminPasswordChange, AdminTaskBatchDelete, SettingsUpdate
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


@router.post("/change-password")
def change_password(payload: AdminPasswordChange, admin=Depends(_admin)):
    try:
        return ok(
            admin_service.change_password(
                admin["id"],
                payload.current_password,
                payload.new_password,
                payload.confirm_password,
            )
        )
    except PermissionError:
        raise fail("ADMIN_UNAUTHORIZED", "当前密码不正确", 401)
    except ValueError as exc:
        raise fail("VALIDATION_ERROR", str(exc), 400)


@router.get("/orders")
def orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    created_from: str | None = Query(None),
    created_to: str | None = Query(None),
    admin=Depends(_admin),
):
    return ok(
        admin_service.list_orders(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword,
            created_from=created_from,
            created_to=created_to,
        )
    )


@router.get("/tasks")
def tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    created_from: str | None = Query(None),
    created_to: str | None = Query(None),
    admin=Depends(_admin),
):
    return ok(
        admin_service.list_tasks(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword,
            created_from=created_from,
            created_to=created_to,
        )
    )


@router.get("/overview")
def overview(admin=Depends(_admin)):
    return ok(admin_service.get_overview())


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
        if str(exc) == "TASK_NOT_FOUND":
            raise fail("TASK_NOT_FOUND", "任务不存在", 404)
        raise fail("DELETE_TASK_FAILED", str(exc), 400)


@router.post("/tasks/data/batch-delete")
def batch_delete_task_data(payload: AdminTaskBatchDelete, admin=Depends(_admin)):
    try:
        return ok(admin_service.delete_task_data_batch(payload.task_nos, admin["id"]))
    except ValueError as exc:
        raise fail("VALIDATION_ERROR", str(exc), 400)


@router.get("/logs")
def logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    admin=Depends(_admin),
):
    return ok(admin_service.list_logs(page=page, page_size=page_size, keyword=keyword))


@router.get("/settings")
def settings(admin=Depends(_admin)):
    return ok(admin_service.get_settings())


@router.put("/settings")
def update_settings(payload: SettingsUpdate, admin=Depends(_admin)):
    return ok(admin_service.update_settings(payload.model_dump(), admin["id"]))
