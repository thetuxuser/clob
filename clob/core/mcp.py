"""MCP (Model Context Protocol) client management."""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if TYPE_CHECKING:
    from .runtime import Runtime


class MCPManager:
    """Manages connections to MCP servers and tool discovery."""

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.sessions: dict[str, ClientSession] = {}
        self._exit_stacks: list[AsyncExitStack] = []

    async def connect_stdio(self, name: str, command: str, args: list[str]) -> None:
        """Connect to an MCP server via stdio."""
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,
        )

        stack = AsyncExitStack()
        self._exit_stacks.append(stack)

        read, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))

        await session.initialize()
        self.sessions[name] = session

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all tools across all connected MCP servers."""
        all_tools = []
        for name, session in self.sessions.items():
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                all_tools.append({
                    "server": name,
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                })
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on a specific MCP server."""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"MCP server '{server_name}' not found")

        return await session.call_tool(tool_name, arguments)

    async def close_all(self) -> None:
        """Close all MCP server connections."""
        for stack in self._exit_stacks:
            await stack.aclose()
        self.sessions.clear()
        self._exit_stacks.clear()
