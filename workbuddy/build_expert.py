"""Build a portable WorkBuddy expert from the current local MCP sources."""

from pathlib import Path
from shutil import copy2
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXPERT = ROOT / "workbuddy" / "bscc-bid-check-expert"
ARCHIVE = ROOT / "workbuddy" / "bscc-bid-check-expert.zip"
MCP_FILES = [
    "pyproject.toml", "uv.lock", "bscc_mcp/__init__.py", "bscc_mcp/__main__.py",
    "bscc_mcp/api.py", "bscc_mcp/config.py", "bscc_mcp/server.py",
]
EXPERT_FILES = [".codebuddy-plugin/plugin.json", ".mcp.json", "agents/bid-check-expert.md", "avatars/expert.png", "README.md"]


def main() -> None:
    for name in MCP_FILES:
        destination = EXPERT / "mcp_server" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(ROOT / "mcp_server" / name, destination)
    with ZipFile(ARCHIVE, "w", compression=ZIP_DEFLATED) as archive:
        for name in EXPERT_FILES + [f"mcp_server/{name}" for name in MCP_FILES]:
            archive.write(EXPERT / name, name)
    print(f"Created {ARCHIVE}")


if __name__ == "__main__":
    main()
