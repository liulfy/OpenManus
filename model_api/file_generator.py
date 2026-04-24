

import requests

# 请求 URL
url = "https://ai.ctaigw.cn/v1/services/aigc/video-generation/video-synthesis"

# 请求头（完全对应 curl 的 -H）
headers = {
    "Authorization": "Bearer sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn",  # 把 sk-xxxxxxx 换成你真实的密钥
    "Content-Type": "application/json",
    "X-DashScope-Async": "enable"
}

# 请求体（完全对应你的 -d 数据）
data = {
    "model": "wan2.6-t2v",
    "input": {
        "prompt": "一幅史诗级可爱的场景。一只小巧可爱的卡通小猫将军，身穿细节精致的金色盔甲，头戴一个稍大的头盔，勇敢地站在悬崖上。他骑着一匹虽小但英勇的战马，说：”青海长云暗雪山，孤城遥望玉门关。黄沙百战穿金甲，不破楼兰终不还。“。悬崖下方，一支由老鼠组成的、数量庞大、无穷无尽的军队正带着临时制作的武器向前冲锋。这是一个戏剧性的、大规模的战斗场景，灵感来自中国古代的战争史诗。远处的雪山上空，天空乌云密布。整体氛围是“可爱”与“霸气”的搞笑和史诗般的融合。"
    },
    "parameters": {
        "size": "1280*720",
        "prompt_extend": True,
        "duration": 10,
        "audio": False,
        "shot_type": "multi"
    }
}

# 发送 POST 请求（json 参数自动处理 Content-Type）
response = requests.post(url, headers=headers, json=data)

task_id = "b631e18f-faef-441c-9726-b050f5206793"

import requests

# 请求头（完全对应 curl 的 -H）
headers = {
    "Authorization": "Bearer sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn",  # 把 sk-xxxxxxx 换成你真实的密钥
    "Content-Type": "application/json",
    "X-DashScope-Async": "enable"
}

task_id = "408ed0f7-4dcf-465b-9a9a-a80f9c6da53a"
# 拼接请求 URL
url = f"https://ai.ctaigw.cn/v1/tasks/{task_id}"
# 发送 GET 请求
res = requests.get(url, headers=headers).json()


# curl -X GET https://ai.ctaigw.cn/v1/tasks/408ed0f7-4dcf-465b-9a9a-a80f9c6da53a \--header "Authorization: Bearer sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn"