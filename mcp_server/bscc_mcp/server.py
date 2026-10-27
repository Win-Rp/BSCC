"""Local stdio MCP server for creating and reviewing BSCC tasks."""

from typing import Annotated, Any
import sys

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from bscc_mcp.api import BSCCClient
from bscc_mcp.config import Settings


TaskNo = Annotated[str, Field(min_length=2, max_length=65, description="BSCC 任务号，例如 T20261027120000ABCD")]
ResultId = Annotated[int, Field(gt=0, description="摘要中返回的 compare_result_id")]
PageSize = Annotated[int, Field(ge=1, le=100, description="每类片段最多返回的数量，默认 20，最大 100")]
Offset = Annotated[int, Field(ge=0, description="从 0 开始的分页偏移量")]


def create_server(settings: Settings | None = None, client: BSCCClient | None = None) -> MCPServer:
    settings = settings or Settings.from_env()
    api = client or BSCCClient(settings)
    server = MCPServer(
        "BSCC 标书查重",
        version="0.1.0",
        instructions=(
            "创建任务会把用户选择的文件上传到 BSCC，并按站点配置保留。"
            "只使用用户明确选择的文件；创建后返回结果页地址，通过状态工具查询进度。"
            "详情受现有付费解锁规则限制，完整片段按页读取。"
        ),
    )

    @server.tool(
        title="创建标书查重任务",
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        structured_output=True,
    )
    async def create_similarity_check(
        a_file_path: Annotated[str, Field(min_length=1, description="本机主标书 A 的绝对路径，必须位于允许目录")],
        b_file_paths: Annotated[list[str], Field(min_length=1, max_length=10, description="本机对比标书 B 的绝对路径，1 至 10 份")],
        keywords: Annotated[list[str] | None, Field(max_length=100, description="可选关键字列表")] = None,
    ) -> dict[str, Any]:
        """上传用户明确选择的 DOCX、可复制文本 PDF 或 UTF-8 TXT 并创建查重任务。

        文件会发送到配置的 BSCC 后端并按站点保留规则保存。此操作会创建任务，
        请勿在上传超时后自动重复提交；返回的 result_url 可立即打开进度和结果页。
        """
        return await api.create(a_file_path, b_file_paths, keywords)

    @server.tool(title="查询查重进度", annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True), structured_output=True)
    async def get_check_status(task_no: TaskNo) -> dict[str, Any]:
        """查询指定任务的状态、进度、失败原因、保留期限和结果页地址。"""
        return await api.status(task_no)

    @server.tool(title="获取查重摘要", annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True), structured_output=True)
    async def get_check_summary(task_no: TaskNo) -> dict[str, Any]:
        """获取任务的相似度排行、解锁状态、结果页和可查看的对比页地址。"""
        return await api.summary(task_no)

    @server.tool(title="获取重复片段预览", annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True), structured_output=True)
    async def get_comparison_preview(
        task_no: TaskNo,
        compare_result_id: ResultId,
        limit: PageSize = 20,
        offset: Offset = 0,
    ) -> dict[str, Any]:
        """分页获取指定 B 文件的免费重复片段预览；可查看范围遵守站点配置。"""
        return await api.preview(task_no, compare_result_id, limit, offset)

    @server.tool(title="获取对比详情", annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True), structured_output=True)
    async def get_comparison_detail(
        task_no: TaskNo,
        compare_result_id: ResultId,
        limit: PageSize = 20,
        match_offset: Offset = 0,
        keyword_offset: Offset = 0,
    ) -> dict[str, Any]:
        """分页获取已解锁或免费的重复片段、关键字命中及格式和元数据对比。

        根据返回的 pagination.matches.next_offset 和 pagination.keyword_hits.next_offset
        分别读取后续页；未解锁任务返回 ORDER_NOT_PAID 和结果页地址。
        """
        return await api.detail(task_no, compare_result_id, limit, match_offset, keyword_offset)

    return server


def main() -> None:
    try:
        server = create_server()
    except (OSError, ValueError) as exc:
        print(f"BSCC MCP 配置错误：{exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    server.run(transport="stdio")
