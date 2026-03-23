
from model_api.doubao_seed_2_lite import query_doubao
import pandas as pd


def build_extract_clause(content_1, content_2, pending_content):
    prompt = f"""
请根据投诉的一级目录和二级目录，抽取受理内容中对应于目录的具体细节。你只需要输出与目录内容对应的细节。如有相关的最新处理进展也请输出。不需要输出其它内容（包括对应时间，对应号码等等）。
一级目录：{content_1}，
二级目录：{content_2}，
受理内容：{pending_content}"""
    return prompt

def wash_pending_content(content_1, content_2, pending_content):
    extract_clause = build_extract_clause(content_1, content_2, pending_content)
    extracted_content = query_doubao(extract_clause)
    print(extracted_content)
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


if __name__ == "__main__":
    df = pd.read_excel("12月清单.xlsx", engine="openpyxl")
    "受理单号  一级目录  二级目录  受理内容  主单是否下派"

    data_size = min(len(df), 100)
    result = []
    for i in range(1329, 1500):
        result.append(run_piece_content(df, i))
        print(f"finish running {i}st data")


    new_df = pd.DataFrame(result, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "主单是否下派"])

    # 写入xlsx
    new_df.to_excel("12月清单抽取1300_1500.xlsx", index=False, engine="openpyxl")



## todo 再弄100条某个相同一级/二级目录下的数据
"""

"""