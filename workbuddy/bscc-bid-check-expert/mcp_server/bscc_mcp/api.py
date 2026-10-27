"""Calls the existing BSCC HTTP API without duplicating its business rules."""

from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from mcp.server.mcpserver.exceptions import ToolError

from bscc_mcp.config import Settings


class BSCCError(ToolError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


MIME_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}
TASK_NO = re.compile(r"^T[0-9A-Za-z]{1,64}$")
CREATE_UNKNOWN_MESSAGE = "任务可能已经创建；请先通过管理后台核查，再决定是否重新提交"


class BSCCClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.settings.api_base_url,
            timeout=httpx.Timeout(self.settings.timeout_seconds, connect=min(10, self.settings.timeout_seconds)),
            follow_redirects=False,
            trust_env=False,
            transport=self.transport,
        )

    @staticmethod
    def _task_path(task_no: str) -> str:
        if not TASK_NO.fullmatch(task_no):
            raise BSCCError("VALIDATION_ERROR", "任务号格式无效")
        return f"/api/tasks/{quote(task_no, safe='')}"

    def result_url(self, task_no: str, result_id: int | None = None) -> str:
        self._task_path(task_no)
        params: dict[str, str | int] = {"task": task_no}
        if result_id is not None:
            params["result"] = result_id
        return f"{self.settings.frontend_base_url}/results?{urlencode(params)}"

    def compare_url(self, task_no: str, result_id: int) -> str:
        self._task_path(task_no)
        return f"{self.settings.frontend_base_url}/compare?{urlencode({'task': task_no, 'result': result_id})}"

    async def _request(self, method: str, path: str, *, creation: bool = False, **kwargs: Any) -> dict[str, Any]:
        try:
            async with self._http() as client:
                response = await client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            if creation:
                raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE) from exc
            raise BSCCError("BACKEND_TIMEOUT", "连接查重服务超时，请稍后重试") from exc
        except httpx.RequestError as exc:
            if creation and not isinstance(exc, httpx.ConnectError):
                raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE) from exc
            raise BSCCError("BACKEND_UNAVAILABLE", "无法连接查重服务，请检查后端地址和服务状态") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            if creation:
                raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE) from exc
            raise BSCCError("INVALID_API_RESPONSE", "查重服务返回了无法识别的响应") from exc
        if not isinstance(payload, dict):
            if creation:
                raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE)
            raise BSCCError("INVALID_API_RESPONSE", "查重服务返回了无法识别的响应")
        if creation and (response.status_code >= 500 or response.is_redirect or (response.is_success and payload.get("success") is not True)):
            raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE)
        if not response.is_success or payload.get("success") is not True:
            error = payload.get("error")
            if isinstance(error, dict):
                code = str(error.get("code") or "BACKEND_ERROR")
                message = str(error.get("message") or "查重服务请求失败")
            else:
                code, message = "BACKEND_ERROR", f"查重服务请求失败（HTTP {response.status_code}）"
            raise BSCCError(code, message)
        data = payload.get("data")
        if not isinstance(data, dict):
            if creation:
                raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE)
            raise BSCCError("INVALID_API_RESPONSE", "查重服务响应缺少任务数据")
        return data

    def _resolve_files(self, a_file_path: str, b_file_paths: list[str]) -> list[Path]:
        if not self.settings.allowed_dirs:
            raise BSCCError("ALLOWED_DIRS_REQUIRED", "请先配置 BSCC_ALLOWED_DIRS，指定允许读取的文件目录")
        if not 1 <= len(b_file_paths) <= 10:
            raise BSCCError("VALIDATION_ERROR", "对比文件 B 必须为 1 至 10 份")
        paths: list[Path] = []
        total = 0
        for raw in [a_file_path, *b_file_paths]:
            candidate = Path(raw).expanduser()
            if not candidate.is_absolute():
                raise BSCCError("VALIDATION_ERROR", "请选择文件的绝对路径")
            try:
                path = candidate.resolve(strict=True)
                if not path.is_file():
                    raise OSError("not a regular file")
                size = path.stat().st_size
            except (OSError, ValueError, RuntimeError) as exc:
                raise BSCCError("FILE_NOT_FOUND", "文件不存在或无法读取，请检查所选路径") from exc
            if not any(path.is_relative_to(root) for root in self.settings.allowed_dirs):
                raise BSCCError("FILE_OUTSIDE_ALLOWED_DIRS", "文件不在允许读取的目录中")
            if path.suffix.lower() not in MIME_TYPES:
                raise BSCCError("UNSUPPORTED_FILE_TYPE", "仅支持 DOCX、可复制文本 PDF 和 UTF-8 TXT")
            if size > self.settings.max_file_bytes:
                raise BSCCError("FILE_TOO_LARGE", "文件超过 BSCC_MAX_FILE_BYTES 限制")
            total += size
            if total > self.settings.max_total_bytes:
                raise BSCCError("UPLOAD_TOO_LARGE", "文件总大小超过 BSCC_MAX_TOTAL_BYTES 限制")
            paths.append(path)
        return paths

    async def create(self, a_file_path: str, b_file_paths: list[str], keywords: list[str] | None) -> dict[str, Any]:
        paths = self._resolve_files(a_file_path, b_file_paths)
        try:
            with ExitStack() as stack:
                files = []
                for index, path in enumerate(paths):
                    handle = stack.enter_context(path.open("rb"))
                    files.append(("a_file" if index == 0 else "b_files", (path.name, handle, MIME_TYPES[path.suffix.lower()])))
                status = await self._request("POST", "/api/tasks", creation=True, files=files, data={"keywords": ",".join(keywords or [])})
        except OSError as exc:
            raise BSCCError("FILE_READ_FAILED", "无法读取所选文件，请检查文件权限") from exc
        task_no = status.get("task_no")
        if not isinstance(task_no, str) or not TASK_NO.fullmatch(task_no):
            raise BSCCError("CREATE_OUTCOME_UNKNOWN", CREATE_UNKNOWN_MESSAGE)
        result = {**status, "b_file_count": len(b_file_paths), "result_url": self.result_url(task_no)}
        try:
            summary = await self.summary(task_no)
            result["expires_at"] = summary.get("expires_at")
        except BSCCError:
            # The task already exists. Never hide its number or invite a duplicate submission.
            result["expires_at"] = None
            result["notice"] = "任务已创建；保留期限暂时无法查询，请稍后查询任务状态。"
        return result

    async def summary(self, task_no: str) -> dict[str, Any]:
        summary = await self._request("GET", f"{self._task_path(task_no)}/summary")
        expires_at = summary.get("expires_at")
        if not isinstance(expires_at, str) or not expires_at:
            raise BSCCError("INVALID_API_RESPONSE", "任务响应缺少保留期限")
        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                raise ValueError("missing timezone")
        except ValueError as exc:
            raise BSCCError("INVALID_API_RESPONSE", "任务保留期限格式无效") from exc
        if expiry <= datetime.now(timezone.utc):
            raise BSCCError("TASK_EXPIRED", "任务已超过保留期限，请重新发起查重")
        locked = bool(summary.get("payment_required")) or summary.get("unlock_status") == "locked"
        rows = summary.get("results") or []
        if not isinstance(rows, list):
            raise BSCCError("INVALID_API_RESPONSE", "查重结果格式无效")
        results = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("compare_result_id"), int):
                raise BSCCError("INVALID_API_RESPONSE", "查重结果缺少对比结果编号")
            result_id = row["compare_result_id"]
            results.append({
                **row,
                "result_url": self.result_url(task_no, result_id),
                "compare_url": None if locked else self.compare_url(task_no, result_id),
            })
        return {**summary, "results": results, "result_url": self.result_url(task_no)}

    async def status(self, task_no: str) -> dict[str, Any]:
        summary = await self.summary(task_no)
        status = await self._request("GET", f"{self._task_path(task_no)}/status")
        return {**status, "expires_at": summary.get("expires_at"), "result_url": self.result_url(task_no)}

    async def preview(self, task_no: str, result_id: int, limit: int, offset: int) -> dict[str, Any]:
        await self.summary(task_no)
        preview = await self._request("GET", f"{self._task_path(task_no)}/results/{result_id}/preview")
        segments = preview.get("segments")
        if not isinstance(segments, list):
            raise BSCCError("INVALID_API_RESPONSE", "预览片段格式无效")
        next_offset = offset + limit if offset + limit < len(segments) else None
        return {
            **preview,
            "segments": segments[offset:offset + limit],
            "pagination": {"offset": offset, "limit": limit, "total": len(segments), "next_offset": next_offset},
            "task_no": task_no,
            "result_url": self.result_url(task_no, result_id),
        }

    async def detail(self, task_no: str, result_id: int, limit: int, match_offset: int, keyword_offset: int) -> dict[str, Any]:
        await self.summary(task_no)
        try:
            detail = await self._request(
                "GET", f"{self._task_path(task_no)}/results/{result_id}/detail",
                params={"include_blocks": "false", "limit": limit, "match_offset": match_offset, "keyword_offset": keyword_offset},
            )
        except BSCCError as exc:
            if exc.code == "ORDER_NOT_PAID":
                raise BSCCError("ORDER_NOT_PAID", f"结果尚未解锁，请在结果页查看并按需解锁：{self.result_url(task_no, result_id)}") from exc
            raise
        return {**detail, "task_no": task_no, "result_url": self.result_url(task_no, result_id), "compare_url": self.compare_url(task_no, result_id)}
