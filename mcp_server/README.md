# BSCC 本地 MCP 服务

本服务使用 stdio 接入 MCP 客户端，通过现有 BSCC HTTP API 创建和查询查重任务。需要先启动 BSCC 后端；网页链接指向单独运行的前端。服务不会启动后端或前端，也不会直接访问数据库。

## 安装

需要 Python 3.11 正式版或更高版本。推荐使用 [uv](https://docs.astral.sh/uv/) 创建独立环境，避免与后端的 FastAPI 依赖冲突：

```powershell
cd <仓库目录>\mcp_server
uv sync --python 3.12 --no-dev
```

也可以使用 `python -m venv .venv` 后，在该环境中执行 `python -m pip install .`。后端和前端启动方法见[项目 README](../README.md#快速启动)。

## 配置 Codex

将以下示例加入 Codex 的 `~/.codex/config.toml`，把占位路径改为实际的绝对路径。使用 TOML 单引号可避免 Windows 路径反斜杠转义：

```toml
[mcp_servers.bscc]
command = '<仓库绝对路径>\mcp_server\.venv\Scripts\python.exe'
args = ['-m', 'bscc_mcp']
cwd = '<仓库绝对路径>\mcp_server'
startup_timeout_sec = 30
tool_timeout_sec = 600

[mcp_servers.bscc.env]
BSCC_API_BASE_URL = 'http://127.0.0.1:8000'
BSCC_FRONTEND_BASE_URL = 'http://127.0.0.1:5173'
BSCC_ALLOWED_DIRS = 'D:\标书文件'
```

在 macOS/Linux 上，将 `command` 改为 `<仓库绝对路径>/mcp_server/.venv/bin/python`，并使用对应的绝对目录。Codex 的 stdio 配置字段见[官方 MCP 配置说明](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。保存配置后按客户端的方式重新加载 MCP 服务，再检查 `bscc` 工具列表。

`BSCC_ALLOWED_DIRS` 必须明确指定已存在的本机绝对目录；Windows 多个目录用 `;` 分隔，macOS/Linux 用 `:` 分隔。创建任务时必须提供位于这些目录内的绝对文件路径。未配置时，查询工具仍可用，创建工具会返回 `ALLOWED_DIRS_REQUIRED`。

| 环境变量 | 默认值 | 用途 |
| --- | --- | --- |
| `BSCC_API_BASE_URL` | `http://127.0.0.1:8000` | 后端 API 地址 |
| `BSCC_FRONTEND_BASE_URL` | `http://127.0.0.1:5173` | 生成结果页和对比页链接的前端地址 |
| `BSCC_ALLOWED_DIRS` | 空 | 允许 MCP 读取文件的目录 |
| `BSCC_MAX_FILE_BYTES` | `209715200` | 单文件上限，默认 200 MiB |
| `BSCC_MAX_TOTAL_BYTES` | `1073741824` | 一次任务文件总大小上限，默认 1 GiB |
| `BSCC_TIMEOUT_SECONDS` | `120` | HTTP 连接及读写超时；连接超时最多 10 秒 |

非本机的 API 和前端地址必须使用 HTTPS。部署到正式站点时，`BSCC_FRONTEND_BASE_URL` 应填写用户实际访问的前端域名；生成的链接不会自动推断部署地址。

## 工具

| 工具 | 参数与返回 |
| --- | --- |
| `create_similarity_check` | `a_file_path`、`b_file_paths`（1–10 份）、可选 `keywords`；返回任务状态、`task_no`、`b_file_count`、`expires_at` 和 `result_url`。 |
| `get_check_status` | `task_no`；返回进度、失败原因、保留期限和 `result_url`。 |
| `get_check_summary` | `task_no`；返回排行、解锁状态和各结果链接。未解锁时 `compare_url` 为 `null`，可从 `result_url` 打开结果页。 |
| `get_comparison_preview` | `task_no`、`compare_result_id`，可选 `limit`、`offset`；返回站点允许的免费预览片段及结果页链接。 |
| `get_comparison_detail` | `task_no`、`compare_result_id`，可选 `limit`（1–100，默认 20）、`match_offset`、`keyword_offset`；返回分页片段、关键字命中和对比页链接。 |

任务创建后 `result_url` 可立即打开，结果页会显示处理状态。查重完成后，摘要中的 `compare_url` 可以打开对应 B 文件的对比界面。所有 URL 使用现有前端的 `task` 和 `result` 查询参数。

创建任务的结构化结果示例：

```json
{
  "task_no": "T20261027120000ABCD",
  "status": "queued",
  "b_file_count": 1,
  "expires_at": "2026-11-03T12:00:00+08:00",
  "result_url": "http://127.0.0.1:5173/results?task=T20261027120000ABCD"
}
```

支持 DOCX、带文字层的 PDF，以及 UTF-8 编码 TXT（含 BOM）。上传会将用户指定的文件发送到配置的后端，并按站点规则保存；查询内容可能包含标书正文，请让客户端用户明确选择文件和使用范围。MCP 层会依据后端返回的 `expires_at` 拒绝读取过期任务。MCP 不删除原文件；当前后端尚未实现按保留期限自动清理，需要由运营维护处理。

详情仍由现有后端校验付费状态。未解锁时工具返回 `ORDER_NOT_PAID` 和结果页链接，用户可在网页中按现有流程解锁。创建任务不是幂等操作；上传中断或服务器异常时工具返回 `CREATE_OUTCOME_UNKNOWN`，此时先通过管理后台核查，再决定是否重试。

当前结果页链接含任务号，现有前台任务接口没有用户归属认证。仅将链接交给任务使用者；对外多用户服务需要先完成[远程接入设计](../docs/mcp-remote-design.md)。

## 测试

开发环境安装测试依赖后运行：

```powershell
cd <仓库目录>\mcp_server
uv sync --python 3.12
$env:BSCC_TEST_BACKEND_PYTHON = '<已安装 backend/requirements.txt 的 Python 绝对路径>'
uv run --no-sync pytest -q
```

端到端测试会启动一个临时后端，使用临时 SQLite 数据库和存储目录。若未设置 `BSCC_TEST_BACKEND_PYTHON`，纯适配层测试仍会运行，真实后端联调测试会跳过。

网页链接检查还需要安装前端依赖，并设置 `BSCC_TEST_BROWSER_NODE`（Node 可执行文件）、`BSCC_TEST_PLAYWRIGHT`（Playwright 的 `index.js`）和 `BSCC_TEST_BROWSER`（Chrome 或兼容 Chromium 的可执行文件）。提供这些路径后，测试会临时启动 Vite，实际打开 MCP 返回的结果页与对比页；未配置时该项跳过。
