
import pandas as pd
from business_scene.suzhiban.back.run_for_circle.shengziding_verify import feature_prompt

df = pd.read_excel("省自定_校验结果_200_300.xlsx", engine="openpyxl")

result = []
data_size = len(df)
for i in range(data_size):
    row_data = df.iloc[i]
    parsed_content = row_data["抽取内容"]
    rule = row_data['下派规则']
    if not isinstance(rule, float):
        result.append([parsed_content, rule])

prompt = f"""
在一个根据给定业务规则判断用户投诉内容是否下派的任务中，当前判断结论为"无法判断是否下派"。
请注意，"不下派"就是派给省层面，"下派"就是派给地市
你将会给到对应的业务规则、投诉内容和判断结论，总结通用的判断规则。

业务规则：
{feature_prompt}\n\n\n"""

for data in result:
    prompt += f"投诉内容：{data[0]}\n下派规则：{data[1]}\n\n"
