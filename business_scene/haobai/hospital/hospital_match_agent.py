
from app.agent.base_manus import BaseManus
from app.tool import Terminate, ToolCollection
from app.tool.ask_human_with_api import AskHumanWithApi
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from business_scene.haobai.hospital.hospital_match_execute import HospitalDepartmentMatchExecute
from pydantic import Field


# 示例：自定义子类，调整available_tools
class HospitalManus(BaseManus):
    """自定义Manus子类，修改可用工具集合"""
    name: str = "HospitalManus"
    description: str = "A versatile agent that can solve various tasks using multiple tools including MCP-based tools"

    # 覆盖默认的available_tools，只保留Python执行和终止工具
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            HospitalDepartmentMatchExecute(),
            AskHumanWithApi(),
            PythonExecute(),  # 执行python代码
            BrowserUseTool(),  # 网页交互工具
            StrReplaceEditor(),  # 支持沙箱功能的文件与目录操作工具
            Terminate(),
        )
    )