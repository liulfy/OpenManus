


import requests
import json

# url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
url = "https://ai.ctaigw.cn/v1/chat/completions"
URL = "http://132.254.211.161:30001/v1/chat/completions"


# 请求头，对应 curl 中的 -H 参数
# headers = {
#     "Content-Type": "application/json",
#     # "Authorization": "Bearer 4d70bef1-fd38-4b0d-9978-7ef7e7b079e8" # my own
#     "Authorization": "Bearer 2c3c4529-82ae-44fa-8ae0-66e2fea16cd8" # haobai
# }

headers = {
    "Authorization": "Bearer sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn",  # 把 sk-xxxxxxx 换成你真实的密钥
    "Content-Type": "application/json",
    "X-DashScope-Async": "enable"
}

def get_current_weather(location, unit="摄氏度"):
    # 实际调用天气查询 API 的逻辑
    # 此处为示例，返回模拟的天气数据
    return f"{location}今天天气晴朗，温度 25 {unit}。"



def query_doubao_with_tool(messages, tools, func):
    data = {
        "messages": messages,
        # "model": "doubao-seed-2-0-lite-260215",
        # "model": "doubao-seed-2-0-pro-260215",
        "model": "Doubao-Seed-2.0-Pro",
        "thinking": {  # enabled, auto, disabled
            "type": "disabled"
        },
        "tools": tools,
        "max_tokens": 100000,
        "caching": {"type": "enabled", "prefix": True}
    }
    while True:
        response = requests.post(
                url=url,
                headers=headers,
                json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
                timeout=30  # 设置超时时间，避免请求挂起
            )

        # 解析并打印响应结果
        result = response.json()
        choice = result['choices'][0]
        finish_reason = choice['finish_reason']
        if finish_reason != "tool_calls":
            answer = result["choices"][0]["message"]["content"]
            return answer
        this_message = choice['message']
        messages.append(this_message.copy())
        tool_calls = this_message['tool_calls']
        tool_call = tool_calls[0] # 只有一个工具
        # function_name = tool_call['function']['name']
        arguments = json.loads(tool_call['function']['arguments'])
        tool_result = func(**arguments)
        # 步骤 4：回填工具结果，并获取模型总结回复
        messages.append(
            {"role": "tool", "content": tool_result, "tool_call_id": tool_call['id']}
        )
        # print(f"finish run one circle in tool use")


# 请求体，对应 curl 中的 -d 参数
def query_doubao(query_clause, max_tokens = 150, tools = [], thinking = "disabled", reasoning_effort = 'medium'):
    data = {
        "messages": [
            {
                "content": query_clause,
                "role": "user"
            },
        ],
        # "model": "doubao-seed-2-0-lite-260215",
        # "model": "doubao-seed-2-0-pro-260215",
        "model": "Doubao-Seed-2.0-Pro",
        "thinking": { # enabled, auto, disabled
            "type": thinking
        },
        "tools": tools,
        "max_tokens": max_tokens,
        "caching": {"type": "enabled", "prefix": True}
    }
    if thinking == "enabled":
        data["reasoning_effort"] = reasoning_effort

    # 发送 POST 请求
    response = requests.post(
        url=url,
        headers=headers,
        json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
        timeout=3000  # 设置超时时间，避免请求挂起
    )

    # 解析并打印响应结果
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    return answer


def query_doubao_with_msgs(messages, max_tokens = 10000, temperature = 0.2):
    data = {
        "messages": messages,
        # "model": "doubao-seed-2-0-pro-260215",
        "model": "Doubao-Seed-2.0-Pro",
        "thinking": {
            "type": "disabled"
        },
        "max_tokens": max_tokens,
        "caching": {"type": "enabled", "prefix": True},
        "temperature": temperature,
    }

    # 发送 POST 请求
    response = requests.post(
        url=url,
        headers=headers,
        json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
        timeout=60  # 设置超时时间，避免请求挂起
    )
    # 解析并打印响应结果
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    return answer


import requests


def stream_doubao(query_clause, max_tokens=150, thinking="disabled", reasoning_effort='medium'):
    data = {
        "messages": [
            {
                "content": query_clause,
                "role": "user"
            },
        ],
        "model": "Doubao-Seed-2.0-Pro",
        "thinking": {
            "type": thinking
        },
        "max_tokens": max_tokens,
        "caching": {"enabled": True, "prefix": True},
        "stream": True  # 关键：开启流式输出
    }
    if thinking == "enabled":
        data["reasoning_effort"] = reasoning_effort

    # 发送流式 POST 请求
    response = requests.post(
        url=url,
        headers=headers,
        json=data,
        timeout=300,
        stream=True  # 关键：requests 开启流式接收
    )

    # 逐行解析 SSE 流式数据
    for line in response.iter_lines():
        if not line:
            continue

        # 解码并去掉 SSE 前缀 data:
        line = line.decode("utf-8").strip()
        if line.startswith("data: "):
            line = line[6:]  # 去掉 data: 前缀

            # 结束标志
            if line == "[DONE]":
                break

            # 解析JSON
            import json
            try:
                chunk = json.loads(line)
                # 获取流式返回的内容
                choices = chunk["choices"]
                if not choices:
                    continue
                delta = choices[0]["delta"]
                if "content" in delta:
                    content = delta["content"]
                    # print(content, end="", flush=True)  # 实时打印
                    yield content  # 生成器返回
            except json.JSONDecodeError:
                continue

def query_doubao_stream(query_clause, max_tokens=150, thinking="disabled", reasoning_effort='medium'):
    res = ''
    for content in stream_doubao(query_clause, max_tokens, thinking, reasoning_effort):
        res += content
    return res






