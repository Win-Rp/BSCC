from fastapi import APIRouter

from app.database import db_session
from app.utils.api import ok


router = APIRouter(tags=["support"])


@router.get("/support")
def support():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT key, value FROM settings WHERE key IN ('customer_service_wechat', 'customer_service_email')"
        ).fetchall()
        settings = {row["key"]: row["value"] for row in rows}
    return ok(
        {
            "wechat": settings.get("customer_service_wechat"),
            "email": settings.get("customer_service_email"),
        }
    )
