from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = DATA_DIR / "bscc.sqlite3"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + str(DB_PATH))

DEFAULT_SETTINGS = {
    "price_per_b_file_cents": "1000",
    "free_b_file_limit": "1",
    "promo_enabled": "false",
    "promo_price_per_b_file_cents": "100",
    "promo_ends_at": "",
    "promo_note": "限时活动，仅限当前批次查重任务",
    "promo_badge": "限时特惠",
    "promo_countdown_enabled": "true",
    "promo_loss_aversion_text": "错过后将恢复原价",
    "preview_segment_limit": "3",
    "result_retention_days": "7",
    "customer_service_wechat": "customer_service_wechat",
    "customer_service_email": "support@example.com",
    "system_notice": "",
    "site_base_url": "",
    "site_title": "标书查重系统",
    "home_tags": '["无需登陆","基础免费","不限页数","不限大小","开箱即用"]',
    "threshold_exact": "1.0",
    "threshold_rewrite": "0.82",
    "threshold_semantic": "0.68",
    "alipay_enabled": "false",
    "alipay_gateway": "",
    "alipay_app_id": "",
    "alipay_notify_url": "",
    "alipay_private_key": "",
    "alipay_public_key": "",
    "wechat_enabled": "false",
    "wechat_app_id": "",
    "wechat_mch_id": "",
    "wechat_api_v2_key": "",
    "wechat_notify_url": "",
}
