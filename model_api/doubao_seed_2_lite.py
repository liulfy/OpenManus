


import requests


url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# 请求头，对应 curl 中的 -H 参数
headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer 4d70bef1-fd38-4b0d-9978-7ef7e7b079e8" # my own
    "Authorization": "Bearer 2c3c4529-82ae-44fa-8ae0-66e2fea16cd8" # haobai
}

# 请求体，对应 curl 中的 -d 参数
def query_doubao(query_clause, max_tokens = 150, tools = []):
    data = {
        "messages": [
            {
                "content": query_clause,
                "role": "user"
            },
        ],
        "model": "doubao-seed-2-0-lite-260215",
        # "model": "doubao-seed-2-0-pro-260215",
        "thinking": {
            "type": "disabled"
        },
        "tools": tools,
        "max_tokens": max_tokens
    }

    # 发送 POST 请求
    response = requests.post(
        url=url,
        headers=headers,
        json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
        timeout=30  # 设置超时时间，避免请求挂起
    )

    # 解析并打印响应结果
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    return answer

