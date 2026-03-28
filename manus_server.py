import asyncio
import traceback
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
from app.logger import logger
from starlette.responses import StreamingResponse
from business_scene.haobai.hospital.hospital_match_agent import HospitalManus

from server.enhanced_server.global_mq import (global_server_msg_dict, global_manus_obj_dict)


# 1. 初始化FastAPI服务（模拟OpenAI服务端）
app = FastAPI(title="OpenManus (OpenAI Compatible)")


# 2. 定义OpenAI风格的请求体模型（严格对齐规范）
class Message(BaseModel):
    role: str  # user/assistant/system
    content: str

def get_thread_by_name(target_name) -> Optional[threading.Thread]:
    for thread in threading.enumerate():
        if thread.name == target_name:
            return thread
    return None

class ChatCompletionRequest(BaseModel):
    chatId: str
    model: str  # 模型名称，如"openmanus-1.0"（映射到OpenManus的模型）
    messages: List[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

def run_agent(agent, client_msg):
    asyncio.run(async_run_agent(agent, client_msg))

async def async_run_agent(agent, client_msg):
    while not agent.stop_flag:
        await agent.run(client_msg)

# 3. 模拟OpenManus的核心对话逻辑（替换为你实际的OpenManus调用代码）
async def openmanus_chat(messages: List[Dict], id_mark: str) -> str:
    """
    你的OpenManus核心逻辑：接收消息列表，返回回复内容
    这里是模拟，实际需替换为OpenManus的调用代码
    """
    client_queue = global_manus_obj_dict.get(id_mark)

    # 发送用户的消息给智能体
    if not client_queue:
        # manus对象没有新建过，是新的对话
        logger.info(f'开始初始化Manus对象: {id_mark}')
        hospital_agent = await HospitalManus().create_with_session_id(id_mark)
        global_manus_obj_dict.initialize_queue(id_mark)
        global_server_msg_dict.initialize_queue(id_mark)
        logger.info(f'传递用户语音内容：{messages[0]['content']}，执行智能体')
        # asyncio.run(hospital_agent.run(messages[0]['content']))
        t = threading.Thread(name=f'CustomerThread-{id_mark}', target=run_agent, args=(hospital_agent, messages[0]['content'],), daemon=True)
        t.start()
    else:
        # 把用户本轮传入的数据送给ask_human工具
        # client_queue['from_human_msg'] = messages[0]['content']
        # global_manus_obj_dict.add_data(id_mark, client_queue)
        logger.info(f'传递用户语音内容：{messages[0]['content']}，执行智能体')
        global_manus_obj_dict.add_data(id_mark, messages[0]['content'])
    
    
    logger.info(f'开始阻塞获取智能体准备传递给用户的话。')
    server_queue = global_server_msg_dict.get(id_mark)
    while True:
        queue_msg = server_queue.get(block=True, timeout=None)
        logger.info(f'准备传递给用户的话是：{queue_msg}')
        yield queue_msg
        if '[DONE]' in queue_msg:
            break


    # logger.info(f'开始阻塞获取智能体准备传递给用户的话。')
    # 阻塞获取智能体返回的需要传递给用户的消息（队列有数据则立即处理）
    # global_server_msg_dict.print_session_id()
    # server_queue = global_server_msg_dict.get(id_mark)
    # queue_msg = server_queue.get(block=True, timeout=None)
    # logger.info(f'准备传递给用户的话是：{queue_msg}')
    # 调用OpenManus生成回复（示例）
    # return f"{queue_msg}"

# 弃用
# 4. 实现OpenAI风格的/chat/completions接口
@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    try:
        # 步骤1：校验请求（OpenAI规范要求）
        if not request.messages:
            raise HTTPException(status_code=400,
                                detail={"error": {"message": "messages不能为空", "type": "invalid_request_error"}})

        # 步骤2：转换请求参数为OpenManus能识别的格式
        openmanus_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 步骤3：调用OpenManus核心逻辑
        # assistant_content = openmanus_chat(openmanus_messages, request.temperature)
        to_human_msg = await openmanus_chat(openmanus_messages, request.chatId)

        # 步骤4：构造OpenAI风格的响应
        response_id = f"aikefu-{request.chatId}"  # 生成唯一ID
        timestamp = int(time.time())  # 时间戳（秒）

        return {
            "id": response_id,
            "object": "chat.completion",
            "created": timestamp,
            "model": request.model,  # 回显模型名称（可映射为OpenManus实际模型）
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": to_human_msg
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {  # 若OpenManus有令牌统计，替换为实际值；无则模拟
                "prompt_tokens": len("".join([msg.content for msg in request.messages])),
                "completion_tokens": len(openmanus_messages),
                "total_tokens": len("".join([msg.content for msg in request.messages])) + len(openmanus_messages)
            }
        }
    except Exception as e:
        # 步骤5：返回OpenAI风格的错误响应
        traceback.print_exc()
        print("-------------------------------------")
        print(e)
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": str(e), "type": "server_error", "param": None, "code": None}}
        )


async def event_generator(request):
    if not request.messages:
        raise HTTPException(status_code=400,
                            detail={"error": {"message": "messages不能为空", "type": "invalid_request_error"}})

    # 步骤2：转换请求参数为OpenManus能识别的格式
    openmanus_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # 步骤3：调用OpenManus核心逻辑
    to_human_msg_gen = openmanus_chat(openmanus_messages, request.chatId)

    async for msg in to_human_msg_gen:
        yield msg

        if '_confirm' in msg:
            current_thread = get_thread_by_name(f"CustomerThread-{request.chatId}")
            agent = current_thread._args[0]
            agent.stop_flag = True
            current_thread.join()
            global global_manus_obj_dict
            global_manus_obj_dict.cleanup(request.chatId)

@app.post("/v2/chat/completions")
async def create_chat_completion_stream(request: ChatCompletionRequest):
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream"  # SSE 标准类型
    )


def print_all_threads_every_10s():
    while True:
        try:
            logger.info("==================================================")
            logger.info(f"📌 当前运行中的全部线程 ")
            logger.info("==================================================")
            for t in threading.enumerate():
                logger.info(f"→ 线程名称：{t.name}")
            logger.info("==================================================\n")
        except Exception as e:
            pass
        
        # 每10秒打印一次
        time.sleep(10)

# 启动监控线程
monitor_thread = threading.Thread(
    target=print_all_threads_every_10s,
    name="ThreadMonitor",
    daemon=True
)
monitor_thread.start()

# 5. 启动服务（运行后可通过http://localhost:8000/v1/chat/completions调用）
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
