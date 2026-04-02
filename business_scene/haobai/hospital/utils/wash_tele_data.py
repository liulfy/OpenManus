


prompt = """你将会给到一些电话客服的交互数据。每一个"拨号记录"对应一组交互数据。
请你识别每一组交互数据，提取"来源"为"主叫客户"的有实际意义的"内容"列数据，并输出。"""



from business_scene.haobai.hospital.hoapital_match_tool import query_result

import pandas as pd



df = pd.read_excel("business_scene/haobai/hospital/utils/电话客服交互数据.xlsx")
data_size = len(df)
result = []
for i in range(1929, data_size):
    row_data = df.iloc[i]
    id = row_data['拨号记录编号']
    user_content = row_data['主叫客户_医疗相关内容']
    assistant_content = row_data['机器人_内容']
    match_department = query_result(user_content)
    print(f"index: {i}, user_content: {user_content}, match_department: {match_department}")
    result.append([id, user_content, assistant_content, match_department])


# 列表 → DataFrame
df = pd.DataFrame(result, columns=['id', "用户投诉", "原始机器人会话", "现机器人会话"])  # columns 自定义列名

# 保存为 xlsx
df.to_excel('校验医院匹配数据.xlsx', index=False)  # index=False 不保存行索引


judge_prompt = """在一个医疗场景中，用户说出自己的诉求，机器人会给用户推荐最匹配的若干科室。你将会给到用户诉求和机器人推荐的信息。
请你判断机器人推荐的是否匹配用户的需求。匹配输出1，不匹配输出0，不需要输出其它内容。
用户诉求：{user_query}
推荐科室：{department}"""



def judge_result(user_query, department):
    prompt = judge_prompt.format(user_query=user_query, department=department)
    msgs = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    data = {
        "messages": msgs,
        "model": "doubao-seed-2-0-lite-260215",
        "thinking": {
            "type": "disabled"
        },
        "max_tokens": 150
    }

    response = requests.post(
        url=url,
        headers=headers,
        json=data,  # 自动将字典转为 JSON 字符串，并设置 Content-Type
        timeout=30  # 设置超时时间，避免请求挂起
    )

    response_result = response.json()
    result = response_result['choices'][0]['message']['content']
    return result


index = 0
data_size = len(result)
for index in range(data_size):
    row_data = result[index]
    user_query = row_data[1]
    department = row_data[3]
    judged_result = judge_result(user_query, department)
    print(f"index: {index}, result: {judged_result}")
    row_data.extend(judged_result)


import pandas as pd
df = pd.DataFrame(result, columns=['id', "用户投诉", "原始机器人会话", "现机器人会话", "判断结果"])  # columns 自定义列名
df.to_excel('医院匹配数据测评结果.xlsx', index=False)