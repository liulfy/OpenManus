import multiprocessing
import sys
from io import StringIO
from typing import Dict

from app.tool.base import BaseTool


class VerifyUseProductsStatus(BaseTool):
    """A tool for verify user products status with timeout and safety restrictions."""

    name: str = "verify_user_products_status_execute"
    description: str = "Verify user products status according to user phone number."
    parameters: dict = {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "The user phone number.",
            },
            "product_list": {
                "type": "array",
                "description": "List of products pending verification.",
            },
        },
        "required": ["phone_number", "product_list"],
    }

    def _get_user_products_status(self, phone_number="15366188311"):

        user_products = [{
            "smsCodeMsg ": "您正在申请订购中国电信提供的代计费业务安全管家（方案编号：25JS110103），产品资费每月15元，此为连续包月业务，订购立即生效，退订次月生效。本业务有效期为24个月，如双方在有效期届满前无异议，有效期自动续展，每次续展2年。本业务无合约期限及违约责任。本次支付验证码为669344，验证码2分钟内有效，感谢使用！【中国电信】",
            "smsOrderSuccessMsg": "尊敬的用户：您于2026年1月10日在中国电信线上渠道成功办理了安全管家（方案编号：25JS110103），产品资费每月15元，订购立即生效，退订次月生效。本业务有效期为24个月，如双方在有效期届满前无异议，有效期自动续展，每次续展2年。本业务无合约期限及违约责任。如需退订请回复TD。使用咨询请致电4008078114【中国电信】",
            "codeSendTime": " 2026-01-10 13:14:06",
            "result": "成功",
            "codeMsgCallbackTime": " 2026-01-10 13:14:33",
            "codeMsgCallbackResult": " 669344",
            "orderSuccessTime": " 2026-01-10 13:14:35"
        },
            {
                "smsCodeMsg ": "您正在申请订购中国电信提供的代计费业务天翼云游戏（方案编号：25JS110101），产品资费每月12元，此为连续包月业务，订购立即生效，退订次月生效。本业务有效期为24个月，如双方在有效期届满前无异议，有效期自动续展，每次续展2年。本业务无合约期限及违约责任。本次支付验证码为669211，验证码2分钟内有效，感谢使用！【中国电信】",
                "smsOrderSuccessMsg": "尊敬的用户：您于2026年1月10日在中国电信线上渠道成功办理了天翼云游戏（方案编号：25JS110101），产品资费每月12元，订购立即生效，退订次月生效。本业务有效期为24个月，如双方在有效期届满前无异议，有效期自动续展，每次续展2年。本业务无合约期限及违约责任。如需退订请回复TD。使用咨询请致电4008078114【中国电信】",
                "codeSendTime": " 2026-01-10 13:14:04",
                "result": "成功",
                "codeMsgCallbackTime": "2026-01-10 13:14:23",
                "codeMsgCallbackResult": "669211",
                "orderSuccessTime": "2026-01-10 13:14:24"
            }
        ]
        return user_products

    def _run_verify(self, phone_number="15366188311", product_list=[]):
        self._get_user_products_status(phone_number)
        return True

    def _run_code(self, phone_number: str, product_list: list, result_dict: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            result_dict["observation"] = self._run_verify(phone_number, product_list)
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        phone_number: str,
        product_list: list,
        timeout: int = 5,
    ) -> Dict:
        """
        Verify user products status.

        Args:
            phone_number (str): The user phone number.
            product_list (list): List of products pending verification.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with products status and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            proc = multiprocessing.Process(
                target=self._run_code, args=(phone_number, product_list, result)
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
