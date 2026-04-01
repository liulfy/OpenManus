from app.tool.base import BaseTool
import json
from server.enhanced_server.global_mq import (global_client_msg_dict, global_server_msg_dict, set_reply_permission,
                                              global_manus_obj_dict)

class TransferToRelevantDepartmentExecute(BaseTool):
    """A tool for transferring to relevant department with timeout and safety restrictions."""

    name: str = "transfer_to_relevant_department"
    description: str = "Transfer to relevant department due to department_number. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {
            "department_number": {
                "type": "string",
                "description": "The department number.",
            }
        },
        "required": ["department_number"],
    }
    session_id: str = ''

    async def execute(self, department_number):
        # todo 转接对应的部门，提示用户"已查询到对应科室，正在为您转接人工，请稍后"，并结束
        client_show_clause = f"""Bot: {department_number}\n\nYou: """
        designated_reply = 'event: fastAnswer\ndata: {"id":"","object":"","created":0,"model":"","choices":[{"delta": {"role":"assistant","content":"已查询到对应科室，正在为您转接人工，请稍后。"},"index":0,"finish_reason":null}]}\n\n'
        global_server_msg_dict.add_data(self.session_id, designated_reply)
        department_name = {"_departName": department_number}
        confirm = {"_departName": department_number, "_confirm":"True"}
        transfer_info = f'event: updateVariables\ndata: {json.dumps(department_name, ensure_ascii=False)}\n\nevent: updateVariables\ndata: {json.dumps(confirm, ensure_ascii=False)}\n\nevent: answer\ndata: [DONE]\n\n'
        global_server_msg_dict.add_data(self.session_id, transfer_info)
        return None
