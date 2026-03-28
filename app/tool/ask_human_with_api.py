from app.tool import BaseTool
from server.enhanced_server.global_mq import (global_client_msg_dict, global_server_msg_dict, set_reply_permission,
                                              global_manus_obj_dict)
import json

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
        json_data = {"id":"","object":"","created":0,"model":"","choices":[{"delta": {"role":"assistant","content": inquire}}]}
        transfer_msg = f'event: fastAnswer\ndata: {json.dumps(json_data, ensure_ascii=False)}\n\nevent: answer\ndata: [DONE]\n\n'
        global_server_msg_dict.add_data(self.session_id, transfer_msg)
        # 阻塞获取
        client_queue = global_manus_obj_dict.get(self.session_id)
        client_msg = client_queue.get(block=True, timeout=None)
        client_queue.task_done()
        return client_msg.strip() # todo 需要调整下格式什么的

