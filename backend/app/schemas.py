from pydantic import BaseModel, field_validator


class OrderCreate(BaseModel):
    task_no: str
    contact: str
    pay_channel: str | None = "alipay"
    locale: str | None = None


class RecoverRequest(BaseModel):
    task_no: str | None = None
    order_no: str | None = None
    contact: str | None = None


class WxLoginRequest(BaseModel):
    code: str


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class AdminTaskBatchDelete(BaseModel):
    task_nos: list[str]


class SettingsUpdate(BaseModel):
    price_per_b_file_cents: str | int | None = None
    free_b_file_limit: str | int | None = None
    promo_enabled: bool | None = None
    promo_price_per_b_file_cents: str | int | None = None
    promo_ends_at: str | None = None
    promo_note: str | None = None
    promo_badge: str | None = None
    promo_countdown_enabled: bool | None = None
    promo_loss_aversion_text: str | None = None
    preview_segment_limit: str | int | None = None
    result_retention_days: str | int | None = None
    customer_service_wechat: str | None = None
    customer_service_email: str | None = None
    system_notice: str | None = None
    site_base_url: str | None = None
    site_title: str | None = None
    home_tags: list[str] | None = None
    threshold_exact: str | float | int | None = None
    threshold_rewrite: str | float | int | None = None
    threshold_semantic: str | float | int | None = None
    alipay_enabled: bool | None = None
    alipay_gateway: str | None = None
    alipay_app_id: str | None = None
    alipay_notify_url: str | None = None
    alipay_private_key: str | None = None
    alipay_public_key: str | None = None
    wechat_enabled: bool | None = None
    wechat_app_id: str | None = None
    wechat_mch_id: str | None = None
    wechat_api_v2_key: str | None = None
    wechat_notify_url: str | None = None
    notify_enabled: bool | None = None
    notify_template_id: str | None = None
    wechat_app_secret: str | None = None
    wechat_mini_app_id: str | None = None

    @field_validator("free_b_file_limit")
    @classmethod
    def validate_free_b_file_limit(cls, value: str | int | None) -> int | None:
        if value is None:
            return None
        try:
            limit = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("免费 B 文件上限必须为 1 至 10") from exc
        if not 1 <= limit <= 10:
            raise ValueError("免费 B 文件上限必须为 1 至 10")
        return limit
