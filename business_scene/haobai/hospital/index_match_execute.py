import multiprocessing
import sys
from io import StringIO
from typing import Dict

from app.tool.base import BaseTool
from business_scene.haobai.hospital.index_match_tool import query_result


class DepartmentIndexMatchExecute(BaseTool):
    """A tool for match the corresponding department index according to user's query with timeout and safety restrictions."""

    name: str = "department_index_match_execute"
    description: str = "根据输入匹配对应的科室编码. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {
            "user_query": {
                "type": "string",
                "description": "The user query.",
            },
        },
        "required": ["user_query"],
    }

    def _run_code(self, user_query: str, result_dict: dict):
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            result_dict["observation"] = query_result(user_query)
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
        Executes the provided Python code with a timeout.

        Args:
            user_query (str): The user's query.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            proc = multiprocessing.Process(
                target=self._run_code, args=(user_query, result)
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
