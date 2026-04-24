

from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key="sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn",
    # 国内中转/代理地址替换此处
    base_url="https://ai.ctaigw.cn/v1"
)

# 对话请求
response = client.chat.completions.create(
    model="Doubao-Seed-2.0-Pro",  # 模型：gpt-4o / gpt-4o-mini / gpt-3.5-turbo
    messages=[
        {"role": "system", "content": "你是严谨的技术顾问，回答简洁准确"},
        {"role": "user", "content": "什么是大模型RAG检索？"}
    ]
)

# 提取结果
print(response.choices[0].message.content)


