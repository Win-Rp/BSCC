from datetime import datetime, timedelta, timezone


TZ = timezone(timedelta(hours=8))


def now() -> datetime:
    return datetime.now(TZ)


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def days_from_now_iso(days: int) -> str:
    return (now() + timedelta(days=days)).isoformat(timespec="seconds")
