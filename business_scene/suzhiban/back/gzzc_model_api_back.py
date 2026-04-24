


import requests


url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# 请求头，对应 curl 中的 -H 参数
headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer 4d70bef1-fd38-4b0d-9978-7ef7e7b079e8" # my own
    "Authorization": "Bearer 2c3c4529-82ae-44fa-8ae0-66e2fea16cd8" # haobai
}


tools = [
    {
    "type": "function",
    "function": {
        "name": "dispatch_judgment",
        "description": '投诉下派判定工具 v2.1\n\n根据用户投诉内容、地域和类别，判断投诉应该【下派】还是【不下派】或【无法判断】。\n优化后控制"无法判断"占比≤30%。',
            "parameters": {
                "properties": {
                "region": {
                    "type": "string"
                    },
                "category": {
                    "type": "string"
                    },
                "content": {
                    "type": "string"
                    }
                },
                "required": [
                    "region",
                    "category",
                    "content",
                    ],
                "type": "object"
            }
        }
    }
]

from business_scene.suzhiban.gzzc_coze.dispatch_tool import dispatch_judgment, system_prompt
import json
user_prompt = "中通服网盈科技有限公司南京分公司@东山觅秀路直管营业厅;11244469;客户原本每月189元，后来被线上更改套餐，因其电话沟通机主与其家人说辞不一致，机主要求退回套餐，对方已告知价格不变的情况下11月查询每月多了20元，现在是209元，是主卡号码客户原本的随心选没有退订反而增加了第二个随心选业务，现在要求退订第二个随心选并退费，未竣工智家尽快撤单"

messages = [
    {
        "content": system_prompt,
        "role": "system"
    },
    {
        "content": user_prompt,
        "role": "user"
    }
]

data = {
    "messages": messages,
    "model": "doubao-seed-2-0-pro-260215",
    "thinking": {
        "type": "disabled"
    },
    "max_tokens": 100000,
    "caching": {"type": "enabled", "prefix": True},
    "tools": tools,
}

# 发送 POST 请求
response = requests.post(
    url=url,
    headers=headers,
    json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
    timeout=30  # 设置超时时间，避免请求挂起
).json()

response['choices'][0]['finish_reason'] == "tool_calls"
tool_calls_msg = response['choices'][0]['message']
tool_calls = tool_calls_msg['tool_calls']
messages.append(tool_calls_msg)
tool_info = tool_calls[0]['function']
args = json.loads(tool_info['arguments'])
tool_result = dispatch_judgment(**args)
messages.append(
    {"role": "tool", "content": json.dumps(tool_result), "tool_call_id": tool_calls[0]['id']}
)







