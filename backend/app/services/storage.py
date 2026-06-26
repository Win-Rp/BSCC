from pathlib import Path

from fastapi import UploadFile

from app.config import STORAGE_DIR


SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


def task_storage_dir(task_no: str) -> Path:
    return STORAGE_DIR / "tasks" / task_no


async def save_upload(task_no: str, role: str, upload: UploadFile, index: int = 0) -> tuple[Path, int]:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError("UNSUPPORTED_FILE_TYPE")
    safe_name = f"{role.lower()}-{index}{ext}" if role == "B" else f"a{ext}"
    directory = task_storage_dir(task_no) / "uploads" / role
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / safe_name
    content = await upload.read()
    path.write_bytes(content)
    return path, len(content)
