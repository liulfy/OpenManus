
from model_api.doubao_seed_2_lite import query_doubao
import pandas as pd


def build_extract_clause(content_1, content_2, pending_content):
    prompt = f"""
请结合输入的一级目录和二级目录，分析投诉工单中与投诉事项直接相关的核心关键信息，包括但不限于停机类型、限制原因、用户诉求、处理结果等所有具体业务细节，务必完整提取工单中出现的业务状态类关键词。你只需要分析投诉单，输出与投诉事项对应的关键细节即可，无需输出时间、号码等无关信息，也无需额外解释。
### 输入信息：
* 一级目录：{content_1}，"""
    if content_2:
        prompt += f"""
* 二级目录：{content_2}，
* 投诉工单内容：{pending_content}"""
    else:
        prompt += f"""
* 投诉工单内容：{pending_content}"""
    return prompt

def wash_pending_content(content_1, content_2, pending_content):
    extract_clause = build_extract_clause(content_1, content_2, pending_content)
    # print(extract_clause)
    extracted_content = query_doubao(extract_clause)
    return extracted_content

def run_piece_content(df, index):
    row_data = df.iloc[index]
    identity_num = row_data['受理单号']
    content_1 = row_data['一级目录']
    content_2 = row_data['二级目录']
    pending_content = row_data['受理内容']
    to_assign = row_data['主单是否下派']
    extracted_content = wash_pending_content(content_1, content_2, pending_content)
    return [identity_num, content_1, content_2, pending_content, extracted_content, to_assign]


def split_thread_data(data_num, thread_num):
    internal = data_num // thread_num
    update_num = data_num % thread_num
    result = [0]
    for i in range(thread_num):
        last_index = result[-1]
        if i < update_num:
            result.append(last_index + internal+1)
        else:
            result.append(last_index + internal)
    return result


if __name__ == "__main__":
    df = pd.read_excel("12月清单.xlsx", engine="openpyxl")
    "受理单号  一级目录  二级目录  受理内容  主单是否下派"

    data_size = min(len(df), 100)
    result = []
    for i in range(5000, 10000):
        if df.iloc[i]['二级目录'] != "省自定2":
            continue
        result.append(run_piece_content(df, i))
        print(f"finish running {i}st data")


    new_df = pd.DataFrame(result, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "主单是否下派"])

    # 写入xlsx
    new_df.to_excel("12月清单抽取_省自定2_5000_10000.xlsx", index=False, engine="openpyxl")



## todo 再弄100条某个相同一级/二级目录下的数据
"""

"""