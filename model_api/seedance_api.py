

import requests

url = "https://ai.ctaigw.cn/v1/images/generations"
api_key = "sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

def run(prompt):
    data = {
        "model": "Doubao-Seedream-5.0-lite",
        "prompt": "星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车，抢视觉冲击力，电影大片，末日既视感，动感，对比色，oc渲染，光线追踪，动态模糊，景深，超现实主义，深蓝，画面通过细腻的丰富的色彩层次塑造主体与场景，质感真实，暗黑风背景的光影效果营造出氛围，整体兼具艺术幻想感，夸张的广角透视效果，耀光，反射，极致的光影，强引力，吞噬",
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": "2K",
        "stream": False,
        "watermark": False
    }
    response = requests.post(url, headers=headers, json=data)
    res = response.json()
    return res['data'][0]['url']

# 打印结果
print("状态码:", response.status_code)
print("响应内容:", response.json())