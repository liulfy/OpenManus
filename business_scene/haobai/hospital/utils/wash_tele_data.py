


prompt = """你将会给到一些电话客服的交互数据。每一个"拨号记录"对应一组交互数据。
请你识别每一组交互数据，提取"来源"为"主叫客户"的有实际意义的"内容"列数据，并输出。"""



from business_scene.haobai.hospital.hoapital_match_tool import query_result

import pandas as pd



df = pd.read_excel("business_scene/haobai/hospital/utils/电话客服交互数据.xlsx")
data_size = len(df)
result = []
for i in range(1620, data_size):
    row_data = df.iloc[i]
    id = row_data['拨号记录编号']
    user_content = row_data['主叫客户_医疗相关内容']
    assistant_content = row_data['机器人_内容']
    match_department = query_result(user_content)
    print(f"index: {i}, user_content: {user_content}, match_department: {match_department}")
    result.append([id, user_content, assistant_content, match_department])


