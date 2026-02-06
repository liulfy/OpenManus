from app.tool import BaseTool
from server.enhanced_server.global_mq import global_client_msg_dict, global_server_msg_dict, set_reply_permission


class AskHumanWithApi(BaseTool):
    """Add a tool to ask human for help."""

    name: str = "ask_human"
    description: str = "Use this tool to ask human for help."
    parameters: str = {
        "type": "object",
        "properties": {
            "inquire": {
                "type": "string",
                "description": "The question you want to ask human.",
            }
        },
        "required": ["inquire"],
    }
    session_id: str = ""

    async def execute(self, inquire: str) -> str:
        ## 改改，发一条信息给用户，让用户输入进来。这一句话需要输出给到客户端。
        """
        将这条信息下发到queue里面，然后从一个地方读取用户输入的信息。

        """
        client_show_clause = f"""Bot: {inquire}\n\nYou: """
        global_server_msg_dict.add_data(self.session_id, client_show_clause)
        client_queue = global_client_msg_dict.get(self.session_id)
        set_reply_permission(self.session_id, True)
        print(f"🔓 客户端[{self.session_id}] | 已开启应答权限（仅本次有效）")
        # 阻塞获取
        client_msg = client_queue.get(block=True, timeout=None)
        client_queue.task_done()
        return client_msg.strip() # todo 需要调整下格式什么的
