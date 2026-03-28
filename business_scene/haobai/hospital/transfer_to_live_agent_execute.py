from app.tool.base import BaseTool


class TransferToLiveAgentExecute(BaseTool):
    """A tool for transferring to live agent with timeout and safety restrictions."""

    name: str = "transfer_to_live_agent"
    description: str = "Transfer to live agent. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }


    async def execute(self):
        # todo 提示转人工，并结束
        return None
