from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = DATA_DIR / "bscc.sqlite3"

DEFAULT_SETTINGS = {
    "price_per_b_file_cents": "1000",
    "preview_segment_limit": "3",
    "result_retention_days": "7",
    "customer_service_wechat": "customer_service_wechat",
    "customer_service_email": "support@example.com",
    "threshold_exact": "1.0",
    "threshold_rewrite": "0.82",
    "threshold_semantic": "0.68",
}
