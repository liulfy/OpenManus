
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量（把你的密钥存在 .env 文件里，避免硬编码）
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # 你的OpenAI Key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # 你的和风天气Key


# ===================== 第一步：定义天气查询Skill（核心功能） =====================
def get_weather(city: str) -> dict:
    """
    天气查询Skill：根据城市名获取实时天气
    :param city: 城市名称（如"北京"、"上海"）
    :return: 结构化的天气数据（JSON格式）
    """
    # 先通过城市名获取城市ID（和风天气的要求）
    city_url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={WEATHER_API_KEY}"
    try:
        # 1. 获取城市ID
        city_response = requests.get(city_url, timeout=10)
        city_data = city_response.json()
        if city_data["code"] != "200" or not city_data["location"]:
            return {"error": f"未找到{city}的城市信息"}

        city_id = city_data["location"][0]["id"]

        # 2. 根据城市ID获取实时天气
        weather_url = f"https://devapi.qweather.com/v7/weather/now?location={city_id}&key={WEATHER_API_KEY}"
        weather_response = requests.get(weather_url, timeout=10)
        weather_data = weather_response.json()

        # 3. 封装结构化结果（方便大模型解析）
        if weather_data["code"] == "200":
            return {
                "city": city,
                "temperature": weather_data["now"]["temp"],  # 温度（℃）
                "condition": weather_data["now"]["text"],  # 天气状况（晴/雨等）
                "wind": weather_data["now"]["windDir"] + weather_data["now"]["windScale"] + "级"  # 风向风力
            }
        else:
            return {"error": f"获取{city}天气失败：{weather_data['code']}"}

    except Exception as e:
        return {"error": f"Skill执行异常：{str(e)}"}


# ===================== 第二步：定义Skill的元数据（供大模型识别） =====================
weather_skill_metadata = {
    "name": "get_weather",  # Skill名称（必须和函数名一致）
    "description": "用于查询指定城市的实时天气信息，包括温度、天气状况、风向风力",  # 大模型判断是否调用的关键
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称，例如：北京、上海、广州"  # 明确参数要求，减少调用错误
            }
        },
        "required": ["city"]  # 必填参数
    }
}


# ===================== 第三步：调用GPT-4o，触发Skill执行 =====================
def call_llm_with_skill(user_query: str):
    """
    调用GPT-4o，自动判断是否需要执行天气Skill，并返回最终回答
    :param user_query: 用户的自然语言问题（如"北京今天天气怎么样？"）
    :return: 整合Skill结果后的自然语言回答
    """
    # 1. 第一步调用：让大模型判断是否需要调用Skill，并生成调用参数
    response = client.chat.completions.create(
        model="gpt-4o",  # 也可以用gpt-3.5-turbo，效果稍弱但成本低
        messages=[{"role": "user", "content": user_query}],
        functions=[weather_skill_metadata],  # 注册Skill
        function_call="auto"  # 让大模型自动决定是否调用Skill
    )

    # 2. 解析大模型的响应：是否要调用Skill
    response_message = response.choices[0].message
    if response_message.function_call:
        # 2.1 提取Skill调用信息
        function_name = response_message.function_call.name
        function_args = json.loads(response_message.function_call.arguments)

        # 2.2 执行对应的Skill（这里只有天气Skill，可扩展多Skill的路由逻辑）
        if function_name == "get_weather":
            city = function_args["city"]
            skill_result = get_weather(city)  # 执行天气Skill
            print(f"【Skill执行结果】：{json.dumps(skill_result, ensure_ascii=False)}")

        # 2.3 第二步调用：把Skill结果传给大模型，让它生成自然语言回答
        second_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": user_query},
                response_message,  # 带上第一步的响应（包含Skill调用决策）
                {
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(skill_result, ensure_ascii=False)  # Skill的结构化结果
                }
            ]
        )
        return second_response.choices[0].message.content
    else:
        # 不需要调用Skill，直接返回大模型的回答
        return response_message.content


# ===================== 测试运行 =====================
if __name__ == "__main__":
    # 示例1：需要调用Skill的场景
    user_question1 = "上海今天的天气怎么样？"
    print(f"用户提问：{user_question1}")
    print(f"最终回答：{call_llm_with_skill(user_question1)}\n")

    # 示例2：不需要调用Skill的场景
    user_question2 = "解释一下什么是大模型的Skill调用？"
    print(f"用户提问：{user_question2}")
    print(f"最终回答：{call_llm_with_skill(user_question2)}")
