

import multiprocessing
import sys
from io import StringIO
from typing import Dict

from app.tool.base import BaseTool
from business_scene.haobai.hospital.hospital_prompts import candidate_wording
import random


class HandlingEscalationToLiveAgentsExecute(BaseTool):
    """A tool for match the corresponding hospital department according to user's query with timeout and safety restrictions."""

    name: str = "handling_escalation_to_live_agents_execute"
    description: str = "处理用户直接转人工的情况. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def _run_code(self, result_dict: dict):
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            result_dict["observation"] = random.choice(candidate_wording['转人工'])
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        timeout: int = 5,
    ) -> Dict:
        """
        Executes the provided Python code with a timeout.

        Args:
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            proc = multiprocessing.Process(
                target=self._run_code, args=(result, )
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

