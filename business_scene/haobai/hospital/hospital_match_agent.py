
from app.agent.base_manus import BaseManus
from app.tool import Terminate, ToolCollection

from business_scene.haobai.hospital.hospital_match_execute import HospitalDepartmentMatchExecute
from business_scene.haobai.hospital.index_match_execute import DepartmentIndexMatchExecute
from business_scene.haobai.hospital.handling_escalation_to_live_agents_execute import HandlingEscalationToLiveAgentsExecute
from business_scene.haobai.hospital.transfer_to_live_agent_execute import TransferToLiveAgentExecute
from business_scene.haobai.hospital.transfer_to_relevant_department_execute import TransferToRelevantDepartmentExecute
from pydantic import Field
from business_scene.haobai.hospital.hospital_prompts import project_prompt


# 示例：自定义子类，调整available_tools
class HospitalManus(BaseManus):
    """自定义Manus子类，修改可用工具集合"""
    name: str = "HospitalManus"
    description: str = "A versatile agent that can solve various tasks using multiple tools including MCP-based tools"
    business_system_prompt: str = project_prompt

    # 覆盖默认的available_tools，只保留Python执行和终止工具
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            HospitalDepartmentMatchExecute(),
            DepartmentIndexMatchExecute(),
            HandlingEscalationToLiveAgentsExecute(),
            TransferToLiveAgentExecute(),
            TransferToRelevantDepartmentExecute(),
            # PythonExecute(),  # 执行python代码
            # BrowserUseTool(),  # 网页交互工具
            # StrReplaceEditor(),  # 支持沙箱功能的文件与目录操作工具
            Terminate(),
        )
    )

