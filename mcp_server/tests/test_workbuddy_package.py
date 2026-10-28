"""Validate the distributable and run its MCP adapter against the real backend."""

import asyncio
import json
from pathlib import Path
import shutil
from zipfile import ZipFile

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from PIL import Image
import pytest

ARCHIVE = Path(__file__).resolve().parents[2] / "workbuddy" / "bscc-bid-check-expert.zip"


def test_expert_archive_manifest(tmp_path: Path):
    with ZipFile(ARCHIVE) as archive:
        names = set(archive.namelist())
        assert {".codebuddy-plugin/plugin.json", ".mcp.json", "agents/bid-check-expert.md", "avatars/expert.png", "README.md", "mcp_server/uv.lock"} <= names
        assert not any(".venv/" in name or "__pycache__/" in name for name in names)
        manifest = json.loads(archive.read(".codebuddy-plugin/plugin.json"))
        server = json.loads(archive.read(".mcp.json"))["mcpServers"]["bscc"]
        assert server["env"]["BSCC_API_BASE_URL"] == "https://biaoshu.mxitx.com"
        assert server["env"]["BSCC_FRONTEND_BASE_URL"] == "https://biaoshu.mxitx.com"
        assert manifest["defaultInitPrompt"] == manifest["quickPrompts"][0]
        assert len(manifest["quickPrompts"]) == len(manifest["tags"]) == 3
        assert 40 <= len(manifest["displayDescription"]["zh"]) <= 50
        assert manifest["agents"] == [f"./agents/{manifest['agentName']}.md"]
        avatar = archive.read(manifest["avatar"])
        assert len(avatar) < 500_000
        archive.extract(manifest["avatar"], tmp_path)
        with Image.open(tmp_path / manifest["avatar"]) as image:
            assert image.size == (512, 512)


async def test_packaged_stdio_with_backend(backend, tmp_path: Path):
    uv = shutil.which("uv")
    if not uv:
        pytest.skip("uv is required to launch the packaged expert")
    plugin_root = tmp_path / "installed-expert"
    with ZipFile(ARCHIVE) as archive:
        archive.extractall(plugin_root)
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    documents = tmp_path / "documents"
    documents.mkdir()
    a_path, b_path = documents / "a.txt", documents / "b.txt"
    content = "\n\n".join(f"第{i}章 项目采用统一数据平台并提供运维支持。" for i in range(1, 16))
    a_path.write_text(content, encoding="utf-8")
    b_path.write_text(content, encoding="utf-8")

    config = json.loads((plugin_root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["bscc"]
    def expand(value: str) -> str:
        return (value.replace("${CODEBUDDY_PLUGIN_ROOT}", str(plugin_root))
                .replace("${CODEBUDDY_PLUGIN_DATA}", str(plugin_data))
                .replace("${user_config.allowed_dirs}", str(documents)))
    env = {key: expand(value) for key, value in config["env"].items()}
    env.update({"BSCC_API_BASE_URL": backend["url"], "PYTHONUTF8": "1"})
    parameters = StdioServerParameters(command=uv, args=[expand(arg) for arg in config["args"]], env=env)
    async with Client(parameters, read_timeout_seconds=120) as client:
        assert {tool.name for tool in (await client.list_tools()).tools} == {
            "create_similarity_check", "get_check_status", "get_check_summary",
            "get_comparison_preview", "get_comparison_detail",
        }
        result = await client.call_tool("create_similarity_check", {"a_file_path": str(a_path), "b_file_paths": [str(b_path)]})
        assert not result.is_error, result.content
        created = result.structured_content
        assert created["result_url"] == f"https://biaoshu.mxitx.com/results?task={created['task_no']}"
        for _ in range(100):
            result = await client.call_tool("get_check_status", {"task_no": created["task_no"]})
            assert not result.is_error, result.content
            status = result.structured_content["status"]
            if status in {"completed", "failed", "awaiting_payment"}:
                break
            await asyncio.sleep(0.2)
        assert status == "completed"
        summary = await client.call_tool("get_check_summary", {"task_no": created["task_no"]})
        assert not summary.is_error, summary.content
        assert summary.structured_content["results"][0]["compare_url"]
