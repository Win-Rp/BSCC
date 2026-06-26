from pydantic import BaseModel


class OrderCreate(BaseModel):
    task_no: str
    contact: str


class RecoverRequest(BaseModel):
    task_no: str | None = None
    order_no: str | None = None
    contact: str | None = None


class AdminLogin(BaseModel):
    username: str
    password: str


class SettingsUpdate(BaseModel):
    price_per_b_file_cents: str | None = None
    preview_segment_limit: str | None = None
    result_retention_days: str | None = None
    customer_service_wechat: str | None = None
    customer_service_email: str | None = None
    threshold_exact: str | None = None
    threshold_rewrite: str | None = None
    threshold_semantic: str | None = None
