"""MCP server that gives an AI assistant the same view as the studio panel.

Tools read the running app through the debug bridge, the stack through compose
and the catalogues through the YAML files. Only the map layout and the entity
registry can be written, exactly like the panel. Development use only.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mcp.server import MCPServer

from .backend import tables as backend_tables
from .catalogues import summary
from .config import CATALOGUES, ROOT, Settings
from .device import BridgeUnavailable, DeviceBridge

COMPOSE = ["docker", "compose", "-f", "ops/compose.yaml", "--env-file", ".env"]


def build_server(settings: Settings) -> MCPServer:
    """Register the studio tools; every handler degrades to a readable error."""
    server = MCPServer(
        "diaryteller-studio",
        instructions=(
            "Local development tools for the Diaryteller app. Diary content is local to the "
            "device; never copy it to another system. Layout and registry edits are allowed."
        ),
    )
    bridge = DeviceBridge(settings.bridge_url)

    @server.tool(title="App state")
    async def app_state() -> str:
        """Return records, entities, events, links and map pins held by the app."""
        try:
            return json.dumps(await bridge.state(), ensure_ascii=False)[:20000]
        except BridgeUnavailable as error:
            return f"app offline: {error}. Run `make app` first."

    @server.tool(title="Move map node")
    async def move_map_node(entity_id: str, x: float, y: float) -> str:
        """Pin one entity on the map; coordinates are normalised to the ring (-1..1)."""
        try:
            await bridge.pin(entity_id, x, y)
            return f"{entity_id} pinned at ({x}, {y})"
        except BridgeUnavailable as error:
            return f"app offline: {error}"

    @server.tool(title="Reset map layout")
    async def reset_map_layout() -> str:
        """Drop every manual position, returning the map to its default ring."""
        try:
            await bridge.clear_pins()
            return "layout reset"
        except BridgeUnavailable as error:
            return f"app offline: {error}"

    @server.tool(title="Rename entity")
    async def rename_entity(entity_id: str, name: str) -> str:
        """Rename one registry entry; identity and links are preserved."""
        try:
            await bridge.update_entity(entity_id, {"name": name})
            return f"{entity_id} renamed to {name}"
        except BridgeUnavailable as error:
            return f"app offline: {error}"

    @server.tool(title="Stack status")
    def stack_status() -> str:
        """List the compose services and their health."""
        result = subprocess.run(  # noqa: S603 - fixed command
            [*COMPOSE, "ps", "--format", "{{.Name}} {{.State}} {{.Health}}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or result.stderr.strip()

    @server.tool(title="Backend tables")
    async def backend_tables_tool() -> str:
        """List the development database tables with row estimates."""
        return json.dumps(await backend_tables(settings.database_url))[:8000]

    @server.tool(title="Translation status")
    def translation_status() -> str:
        """Show the language catalogues and their missing keys."""
        return json.dumps(summary(Path(CATALOGUES)))[:8000]

    @server.tool(title="Run checks")
    def run_checks() -> str:
        """Run the repository check target and return its tail."""
        result = subprocess.run(  # noqa: S603 - fixed command
            ["make", "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        tail = (result.stdout + result.stderr).strip().splitlines()[-25:]
        return "\n".join(tail)

    return server


def main() -> None:
    """Serve the tools over stdio, which is how VS Code launches MCP servers."""
    build_server(Settings.load()).run("stdio")


if __name__ == "__main__":
    main()
