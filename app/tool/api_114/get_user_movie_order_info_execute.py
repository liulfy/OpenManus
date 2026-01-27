



import multiprocessing
import sys
from io import StringIO
from typing import Dict

import json
import requests

from app.tool.base import BaseTool


class GetUseMovieOrderInfo(BaseTool):
    """A tool for get list of user movie order info with timeout restrictions."""

    name: str = "get_user_movie_order_info_execute"
    description: str = "Get the list of user movie order info according to user phone number."
    parameters: dict = {
        "type": "object",
        "properties": {
            "user_query": {
                "type": "string",
                "description": "The user query .",
            },
        },
        "required": ["phone_number"],
    }

    def _get_movie_info(self, user_query="13800138000"):
        url = "http://openapi.telecomjs.com:80/eop/zntpt/Agent_Chat_API_AIPlatform/chat-messages"

        headers = {
            # "Authorization": "Bearer {api_key}",
            "Authorization": "Bearer app-YOEwvlE9fC1htGQwSjH2KrQx",
            "X-APP-ID": "b04064cb05d94396b126027b08a8675c",
            "X-APP-KEY": "41fbb09ec1a4490b9009b4037f6ecb53",
            "Content-Type": "application/json"
        }

        payload = {
            "user": "admin",
            "mode": "blocking",
            "query": "1",
            "input_data": {
                "user_query": user_query,
                "knowledge_base_name": "号百_114",
                "rag_authorization": "ragflow-QzZjljOTA0OGM3YjExZjA4ODhiNWFkMG",
                "recall_num": "4"}
        }
        response = requests.post(url=url, headers=headers, json=payload, timeout=180)
        json_code = json.loads(response.text)
        return [json_code['answer']]

    def _run_code(self, user_query: str, result_dict: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            result_dict["observation"] = self._get_movie_info(user_query)
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        user_query: str,
        timeout: int = 5,
    ) -> Dict:
        """
        Get the list of pay-per-use products according to user phone number.

        Args:
            user_query (str): The user query statement.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            # if isinstance(__builtins__, dict):
            #     safe_globals = {"__builtins__": __builtins__}
            # else:
            #     safe_globals = {"__builtins__": __builtins__.__dict__.copy()}
            proc = multiprocessing.Process(
                target=self._run_code, args=(user_query, result)
            # target = self._run_code, args = (phone_number, result, safe_globals)
            )
            proc.start()
            proc.join(timeout)

            # timeout process
            if proc.is_alive():
                proc.terminate()
                proc.join(1)
                return {
                    "observation": f"Execution timeout after {timeout} seconds",
                    "success": False,
                }
            return dict(result)







"""
该接口对电话号码必须完全匹配，对于文本（电影名，影院）可以分词匹配
"""



