

import pandas as pd
from model_api.doubao_seed_2_lite import query_doubao
from ignore.szb_back.back import wash_pending_content

from business_scene.agg_usd_rules import rules

df = pd.read_excel("12月清单.xlsx", engine="openpyxl")
result = []
for index in range(10100, 10200):
    row_data = df.iloc[index]
    identity_num = row_data['受理单号']
    content_1 = row_data['一级目录']
    content_2 = row_data['二级目录']
    pending_content = row_data['受理内容']
    extracted_content = wash_pending_content(content_1, content_2, pending_content)
    to_assign = row_data['主单是否下派']

    prompt = f"请结合给定的投诉规则，判断投诉受理内容属于哪一类。" \
             f"投诉内容为：\n{extracted_content}\n\n" \
             f"投诉规则为：{rules}"

    local_result = query_doubao(prompt, 200)
    print(f"index：{index}，受理内容：{extracted_content}，分类：{local_result}")
    result.append([identity_num, content_1, content_2, pending_content, extracted_content, local_result, to_assign])

new_df1 = pd.DataFrame(result, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "场景分类", "主单是否下派"])
new_df1.to_excel("12月数据_分类_10000_10200.xlsx", index=False, engine="openpyxl")

