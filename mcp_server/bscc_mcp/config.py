"""Configuration for the local MCP adapter."""

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit


def _base_url(value: str, name: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError(f"{name} 的端口无效") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{name} 必须是没有凭据、查询参数或片段的 HTTP(S) 地址")
    if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(f"{name} 的非本机地址必须使用 HTTPS")
    return value


def _positive_int(name: str, default: int) -> int:
    value = int(os.environ.get(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} 必须是正整数")
    return value


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    frontend_base_url: str
    allowed_dirs: tuple[Path, ...]
    max_file_bytes: int
    max_total_bytes: int
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        roots = []
        for item in os.environ.get("BSCC_ALLOWED_DIRS", "").split(os.pathsep):
            if not item.strip():
                continue
            root = Path(item.strip()).expanduser()
            if not root.is_absolute():
                raise ValueError("BSCC_ALLOWED_DIRS 必须使用绝对目录路径")
            try:
                root = root.resolve(strict=True)
            except OSError as exc:
                raise ValueError("BSCC_ALLOWED_DIRS 包含不存在或无法访问的目录") from exc
            if not root.is_dir():
                raise ValueError("BSCC_ALLOWED_DIRS 必须指向目录")
            roots.append(root)
        return cls(
            api_base_url=_base_url(
                os.environ.get("BSCC_API_BASE_URL", "http://127.0.0.1:8000"), "BSCC_API_BASE_URL"
            ),
            frontend_base_url=_base_url(
                os.environ.get("BSCC_FRONTEND_BASE_URL", "http://127.0.0.1:5173"), "BSCC_FRONTEND_BASE_URL"
            ),
            allowed_dirs=tuple(roots),
            max_file_bytes=_positive_int("BSCC_MAX_FILE_BYTES", 200 * 1024 * 1024),
            max_total_bytes=_positive_int("BSCC_MAX_TOTAL_BYTES", 1024 * 1024 * 1024),
            timeout_seconds=_positive_int("BSCC_TIMEOUT_SECONDS", 120),
        )
