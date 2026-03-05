
from typing import Dict, List, Optional, Type, TypeVar
from abc import ABC

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.tool import Terminate, ToolCollection
from app.tool.ask_human_with_api import AskHumanWithApi
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor


class BaseManus(ToolCallAgent, ABC):
    """基础通用Agent基类，支持本地和MCP工具，子类可自定义available_tools"""

    name: str = "BaseManus"
    description: str = "A base versatile agent that can solve various tasks using multiple tools including MCP-based tools"

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT
    business_system_prompt: str = ""

    max_observe: int = 10000
    max_steps: int = 20

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # 核心修改：将available_tools设为可配置，默认保留原工具集合
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),  # 执行python代码
            BrowserUseTool(),  # 网页交互工具
            StrReplaceEditor(),  # 支持沙箱功能的文件与目录操作工具
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command
    _initialized: bool = False

    @model_validator(mode="after")
    def initialize_helper(self) -> "BaseManus":
        """Initialize basic components synchronously."""
        self.browser_context_helper = BrowserContextHelper(self)
        return self

    @classmethod
    async def create(cls, **kwargs):
        """Factory method to create and properly initialize a BaseManus instance."""
        # 允许通过kwargs覆盖available_tools
        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance

    @classmethod
    async def create_with_session_id(cls, session_id, **kwargs):
        """Factory method to create and properly initialize a BaseManus instance with session id."""
        # 允许通过kwargs覆盖available_tools
        instance = cls(** kwargs)
        instance.session_id = session_id
        ask_human_with_api = AskHumanWithApi()
        ask_human_with_api.session_id = instance.session_id
        instance.available_tools.add_tool(ask_human_with_api)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        print(f"instance id is {instance.session_id}")
        return instance

    async def initialize_mcp_servers(self) -> None:
        """Initialize connections to configured MCP servers."""
        for server_id, server_config in config.mcp_config.servers.items():
            try:
                if server_config.type == "sse":
                    if server_config.url:
                        await self.connect_mcp_server(server_config.url, server_id)
                        logger.info(
                            f"Connected to MCP server {server_id} at {server_config.url}"
                        )
                elif server_config.type == "stdio":
                    if server_config.command:
                        await self.connect_mcp_server(
                            server_config.command,
                            server_id,
                            use_stdio=True,
                            stdio_args=server_config.args,
                        )
                        logger.info(
                            f"Connected to MCP server {server_id} using command {server_config.command}"
                        )
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_id}: {e}")

    async def connect_mcp_server(
        self,
        server_url: str,
        server_id: str = "",
        use_stdio: bool = False,
        stdio_args: List[str] = None,
    ) -> None:
        """Connect to an MCP server and add its tools."""
        if use_stdio:
            await self.mcp_clients.connect_stdio(
                server_url, stdio_args or [], server_id
            )
            self.connected_servers[server_id or server_url] = server_url
        else:
            await self.mcp_clients.connect_sse(server_url, server_id)
            self.connected_servers[server_id or server_url] = server_url

        # Update available tools with only the new tools from this server
        new_tools = [
            tool for tool in self.mcp_clients.tools if tool.server_id == server_id
        ]
        self.available_tools.add_tools(*new_tools)

    async def disconnect_mcp_server(self, server_id: str = "") -> None:
        """Disconnect from an MCP server and remove its tools."""
        await self.mcp_clients.disconnect(server_id)
        if server_id:
            self.connected_servers.pop(server_id, None)
        else:
            self.connected_servers.clear()

        # Rebuild available tools without the disconnected server's tools
        base_tools = [
            tool
            for tool in self.available_tools.tools
            if not isinstance(tool, MCPClientTool)
        ]
        self.available_tools = ToolCollection(*base_tools)
        self.available_tools.add_tools(*self.mcp_clients.tools)

    async def cleanup(self):
        """Clean up BaseManus agent resources."""
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
        # Disconnect from all MCP servers only if we were initialized
        if self._initialized:
            await self.disconnect_mcp_server()
            self._initialized = False

    # 实际执行的function
    async def think(self) -> bool:
        """Process current state and decide next actions with appropriate context."""
        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        result = await super().think()

        # Restore original prompt
        self.next_step_prompt = original_prompt

        return result

    async def run(self, request: Optional[str] = None) -> str:
        if request:
            request = self.business_system_prompt + request
        return await super().run(request)



# 示例2：扩展默认工具（不覆盖，而是在创建实例时添加）
async def create_extended_manus():
    # 创建BaseManus实例，额外添加自定义工具
    custom_tools = ToolCollection(
        PythonExecute(),
        BrowserUseTool(),
        StrReplaceEditor(),
        Terminate(),
        # 新增自定义工具
        # CustomTool(),
    )
    manus = await BaseManus.create(available_tools=custom_tools)
    return manus


# 示例3：通过create_with_session_id创建并调整工具
async def create_custom_session_manus(session_id):
    # 先创建默认工具集合，再移除不需要的工具
    base_tools = ToolCollection(
        PythonExecute(),
        Terminate(),
    )
    manus = await BaseManus.create_with_session_id(
        session_id=session_id,
        available_tools=base_tools
    )
    # 动态添加工具
    manus.available_tools.add_tool(BrowserUseTool())
    return manus

