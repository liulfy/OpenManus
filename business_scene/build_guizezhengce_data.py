

"""
step1 wash data

"""

import pandas as pd
from model_api.doubao_seed_2_lite import query_doubao

def wash_pending_content(content_1, pending_content):
    extract_clause = f"""
请结合输入的一级目录和二级目录，分析投诉工单中与投诉事项直接相关的核心关键信息，包括但不限于停机类型、限制原因、用户诉求、处理结果等所有具体业务细节，务必完整提取工单中出现的业务状态类关键词。你只需要分析投诉单，输出与投诉事项对应的关键细节即可，无需输出时间、号码等无关信息，也无需额外解释。
### 输入信息：
* 一级目录：{content_1}，
* 投诉工单内容：{pending_content}"""
    extracted_content = query_doubao(extract_clause, 200)
    return extracted_content

if __name__ == "__main__":
    df = pd.read_excel("12月清单.xlsx", engine="openpyxl")
    result = []
    for index in range(10000):
        row_data = df.iloc[index]
        identity_num = row_data['受理单号']
        content_1 = row_data['一级目录']
        if content_1 != "费用争议类":
            continue
        pending_content = row_data['受理内容']
        extracted_content = wash_pending_content(content_1, pending_content)
        to_assign = row_data['主单是否下派']
        print(f"index：{index}，受理内容：{extracted_content}")
        result.append([identity_num, content_1, pending_content, extracted_content, to_assign])


    new_df1 = pd.DataFrame(result, columns=["受理单号", "一级目录", "受理内容", "抽取内容", "主单是否下派"])
    new_df1.to_excel("12月清单_费用争议类_10000.xlsx", index=False, engine="openpyxl")

