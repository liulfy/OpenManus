
import asyncio

from app.agent.manus_back.manus import Manus
from app.logger import logger



# todo 也可以起始的时候，加入用户的请求。
async def main(user_prompt):

    # Create and initialize Manus agent
    agent = await Manus.create()
    try:
        if not user_prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        return await agent.run(user_prompt)
        # logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


if __name__ == "__main__":
    user_prompt = """与人类确认手机号码是否正确。如果人类返回手机号不正确，则要求人类输入正确的手机号。你最终将正确的手机号返回。人类输入的手机号为：15301582562"""
    res = asyncio.run(main(user_prompt))
    print(f"success run agent and the result is {res}")

"""
https://www.doubao.com/thread/w28f46f20250feda0
"""