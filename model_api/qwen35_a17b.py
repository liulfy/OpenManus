



import requests
import json


# 1. 配置请求参数
url = "http://132.254.211.161:30000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 84111b87f2754f9199d86cfece4e1522"  # 替换为你的真实token
}
# 请求体（完全对应curl的data-raw内容）
def query_qwen35_a17b(query_clause, max_tokens = 150):
    payload = {
        "model": "Qwen3.5-397B-A17B",
        # "model": "Qwen3-30B-A3B-Instruct-2507",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query_clause
                    }
                ]
            }
        ],
        "max_tokens": max_tokens,
        "enable_thinking": False
    }

    # 2. 发送POST请求
    response = requests.post(
        url=url,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        # data=json.dumps(payload, ensure_ascii=False),  # 确保中文正常传输
        timeout=30  # 设置超时时间，避免无限等待
    )

    return json.loads(response.text)['choices'][0]['message']['content']
