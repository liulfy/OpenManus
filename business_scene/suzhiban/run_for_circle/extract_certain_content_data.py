
import pandas as pd
from business_scene.suzhiban.info_extractor import wash_pending_content


df = pd.read_excel("12月清单.xlsx", engine="openpyxl")
result1 = []
result2 = []

for i in range(5000, 10000):
    row_data = df.iloc[i]
    content_2 = row_data['二级目录']
    if not content_2 in ("省自定2", "关停不认可"):
        continue
    identity_num = row_data['受理单号']
    content_1 = row_data['一级目录']
    pending_content = row_data['受理内容']
    to_assign = row_data['主单是否下派']
    extracted_content = wash_pending_content(content_1, content_2, pending_content)
    row_result = [identity_num, content_1, content_2, pending_content, extracted_content, to_assign]
    print(f"index is {i}, data is {row_result}")
    if content_2 == "关停不认可":
        result1.append(row_result)
    else:
        result2.append(row_result)


new_df1 = pd.DataFrame(result1, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "主单是否下派"])
new_df1.to_excel("12月清单抽取_关停不认可_5000_10000.xlsx", index=False, engine="openpyxl")


new_df2 = pd.DataFrame(result2, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "主单是否下派"])
new_df2.to_excel("12月清单抽取_省自定_5000_10000.xlsx", index=False, engine="openpyxl")

