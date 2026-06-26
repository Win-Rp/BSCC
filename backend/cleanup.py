import logging
import time
from pathlib import Path
from datetime import datetime

from app.database import db_session
from app.services.admin import delete_task_data
from app.utils.time import now_iso

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_cleanup():
    logging.info("Starting cleanup of expired tasks...")
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT task_no
            FROM tasks
            WHERE expires_at < ? AND status != 'deleted'
            """,
            (now_iso(),)
        ).fetchall()
        
    for row in rows:
        task_no = row["task_no"]
        try:
            # We pass admin_user_id=None (or a special system ID, but NULL is fine for system actions)
            # wait, the foreign key for admin_user_id allows NULL
            delete_task_data(task_no, admin_user_id=None)
            logging.info(f"Cleaned up expired task data for {task_no}")
        except Exception as e:
            logging.error(f"Failed to cleanup task {task_no}: {e}")
            
    logging.info(f"Cleanup completed. Processed {len(rows)} tasks.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Run in continuous loop mode")
    parser.add_argument("--interval", type=int, default=3600, help="Loop interval in seconds (default 1 hour)")
    args = parser.parse_args()

    if args.loop:
        logging.info(f"Running in loop mode, interval {args.interval}s")
        while True:
            run_cleanup()
            time.sleep(args.interval)
    else:
        run_cleanup()
