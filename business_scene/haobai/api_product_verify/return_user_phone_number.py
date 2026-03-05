import multiprocessing
import sys
from io import StringIO
from typing import Dict

from app.tool.base import BaseTool


class ReturnUserPhoneNumberExecute(BaseTool):
    """A tool for return user phone numer with timeout and safety restrictions."""

    name: str = "return_user_phone_number_execute"
    description: str = "return user phone numer. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "The user phone numer.",
            },
        },
        "required": ["phone_number"],
    }

    def _run_code(self, phone_number: str, result_dict: dict):
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            result_dict["observation"] = phone_number
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        phone_number: str,
        timeout: int = 5,
    ) -> Dict:
        """
        Executes the provided Python code with a timeout.

        Args:
            phone_number (str): The Python code to execute.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            proc = multiprocessing.Process(
                target=self._run_code, args=(phone_number, result)
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
