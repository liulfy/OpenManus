


import requests
import json


# 1. 配置请求参数
url = "http://132.254.211.161:30000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 84111b87f2754f9199d86cfece4e1522"  # 替换为你的真实token
}
# 请求体（完全对应curl的data-raw内容）
"/Users/liufengyuan/Desktop/测评相关/pic_5.jpg"
"C://Users//Administrator//Desktop//fake_pic_check//pic_0.jpg"
payload = {
    "model": "Doubao-Seed-2.0-pro",
    "messages": [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "/Users/liufengyuan/Desktop/测评相关/pic_5.jpg"}},
            {"type": "text", "text": "描述这张图片的内容"}
        ]}
    ],
    "max_tokens": 200
}


# 2. 发送POST请求
response = requests.post(
    url=url,
    headers=headers,
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    # data=json.dumps(payload, ensure_ascii=False),  # 确保中文正常传输
    timeout=30  # 设置超时时间，避免无限等待
)



import base64
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

base64_image = encode_image("/path/to/image.png")
response = client.chat.completions.create(
    model="doubao-seed-2-0-pro-260325",
    messages=[
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
            {"type": "text", "text": "描述这张图片的内容"}
        ]}
    ]
)


import requests

# 1. 配置信息（请把这里换成你的真实API_KEY）
API_KEY = "sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn"
URL = "https://ai.ctaigw.cn/v1/chat/completions"

# 2. 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

import base64
def encode_image(image_path = "/Users/liufengyuan/Desktop/测评相关/pic_5.jpg"):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# 3. 请求体（和curl完全一致）
data = {
    "model": "Doubao-Seed-2.0-Pro",
    "reasoning_effort": "medium",
    "messages": [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encode_image()}"}},
            {"type": "text", "text": "描述这张图片的内容"}
        ]}
    ]
}

# 4. 发送POST请求
response = requests.post(URL, headers=headers, json=data)

# 5. 打印结果
print("状态码:", response.status_code)
print("响应内容:", response.json())