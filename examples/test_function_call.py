



def get_current_weather(location, unit="摄氏度"):
    # 实际调用天气查询 API 的逻辑
    # 此处为示例，返回模拟的天气数据
    return f"{location}今天天气晴朗，温度 25 {unit}。"


tool = {
  "type": "function",
  "function": {
    "name": "get_current_weather",
    "description": "获取指定地点的天气信息，支持摄氏度和华氏度两种单位",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "地点的位置信息，例如北京、上海"
        },
        "unit": {
          "type": "string",
          "enum": ["摄氏度", "华氏度"],
          "description": "温度单位，可选值为摄氏度或华氏度"
        }
      },
      "required": ["location"]
    }
  }
}

import requests
import json

url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# 请求头，对应 curl 中的 -H 参数
headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer 4d70bef1-fd38-4b0d-9978-7ef7e7b079e8" # my own
    "Authorization": "Bearer 2c3c4529-82ae-44fa-8ae0-66e2fea16cd8" # haobai
}

prompt = "北京今天的天气如何？"

data = {
    "messages": [
        {
            "content": prompt,
            "role": "user"
        },
    ],
    "model": "doubao-seed-2-0-lite-260215",
    # "model": "doubao-seed-2-0-pro-260215",
    "thinking": {
        "type": "disabled"
    },
    "tools": [tool],
    "max_tokens": 150
}

messages = data['messages']

while True:
    # 步骤2: 发起模型请求，由于模型在收到工具执行结果后仍然可能有函数调用意愿，因此需要多次请求
    response = requests.post(
        url=url,
        headers=headers,
        json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
        timeout=30  # 设置超时时间，避免请求挂起
    )
    result = response.json()
    # if completion.choices[0].finish_reason != "tool_calls":
    if result['choices'][0]['finish_reason'] != 'tool_calls':
        # 模型最终总结，没有调用工具意愿
        break
    messages.append(result['choices'][0]['message'])
    tool_calls = result['choices'][0]['message']['tool_calls']
    for tool_call in tool_calls:
        tool_name = tool_call['function']['name']
        if tool_name == "get_current_weather":
            # 步骤 3：调用外部工具
            args = json.loads(tool_call['function']['arguments'])
            tool_result = get_current_weather(**args)
            # 步骤 4：回填工具结果，并获取模型总结回复
            messages.append(
                {"role": "tool", "content": tool_result, "tool_call_id": tool_call['id']}
            )


# return
result['choices'][0]['message']['content']