


import requests
import json


url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# 请求头，对应 curl 中的 -H 参数
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 4d70bef1-fd38-4b0d-9978-7ef7e7b079e8"
}

# 请求体，对应 curl 中的 -d 参数
data = {
    "messages": [
        {
            "content": "天空为什么是蓝色的？",
            "role": "user"
        },
        {
            "content": "你好",
            "role": "system"
        }
    ],
    "model": "doubao-seed-2-0-lite-260215",
    "thinking": {
        "type": "disabled"
    }
}


# 发送 POST 请求
response = requests.post(
    url=url,
    headers=headers,
    json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
    timeout=30  # 设置超时时间，避免请求挂起
)

# 检查响应状态码
response.raise_for_status()

# 解析并打印响应结果
result = response.json()
print("请求成功！响应结果：")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 提取回答内容（可选）
if "choices" in result and len(result["choices"]) > 0:
    answer = result["choices"][0]["message"]["content"]
    print("\n提取到的回答内容：")
    print(answer)

