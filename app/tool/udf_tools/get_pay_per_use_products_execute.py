import multiprocessing
import sys
from io import StringIO
from typing import Dict

from app.tool.base import BaseTool


class GetPayPerUseProducts(BaseTool):
    """A tool for get list of pay-per-use products with timeout restrictions."""

    name: str = "get_pay_per_use_products_execute"
    description: str = "Get the list of pay-per-use products according to user phone number."
    parameters: dict = {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "The user phone number.",
            },
        },
        "required": ["phone_number"],
    }

    def _get_pay_per_use_products(self, phone_number="15366188311"):

        product_msg =  {
            "offerId": "911022384",
            "offerName": "安全管家增强包",
            "status": "在网",
            "orderTime": " 2026-01-10 13:14:35",
            "unsubscribeTime": "NULL",
            "employeeId": "VSOP",
            "source": "2000",
            "spName": "江苏号百信息服务有限公司空中卫士业务"
        }
        return [product_msg['offerName']]

    def _run_code(self, phone_number: str, result_dict: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            result_dict["observation"] = self._get_pay_per_use_products(phone_number)
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
        Get the list of pay-per-use products according to user phone number.

        Args:
            phone_number (str): The user phone number.
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
                target=self._run_code, args=(phone_number, result)
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
