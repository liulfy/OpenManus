

import pandas as pd
from business_scene.suzhiban.gzzc_coze.agent import run
from business_scene.suzhiban.utils.gzzc_model_api import markdown_json_to_dict

file_path = "business_scene/suzhiban/gzzc_coze/业务数据_规则政策类.xlsx"

df = pd.read_excel(file_path, engine="openpyxl")
data_size = len(df)

result = []

for i in range(150):
    row_data = df.iloc[i]
    region = row_data['地域']
    content_1 = row_data['一级目录']
    content_2 = row_data['二级目录']
    pending_content = row_data['受理内容']
    to_assign = row_data['主单是否下派']
    query_prompt = f"region：{region}，category：{content_2}，content：{pending_content}"
    inference_result = run(query_prompt)
    inference_result = markdown_json_to_dict(inference_result)
    local_result = [region, content_1, content_2, to_assign]
    judgement = inference_result['判定']
    reason = inference_result['理由']
    confidence = inference_result['置信度']
    local_result.extend([judgement, reason, confidence, pending_content])
    # judgement = inference_result['判定']
    # reason = inference_result['理由']
    # confidence = inference_result['置信度']
    # local_result = [region, content_1, content_2, pending_content, to_assign, judgement, reason, confidence]
    print(f"index: {i}, result: {local_result}")
    result.append(local_result)



def select_bad_case(judge_result):
    bad_category = ["业务生效/失效规则争议", "省自定2"]
    unmatch_result = []
    FN_result = []
    FT_result = []
    for index, row_data in enumerate(judge_result):
        local_label = row_data[3]
        truth_label = row_data[4]
        if "无法判断" in local_label or row_data[-2] == "低":
        # if "无法判断" in local_label or (row_data[2] in bad_category and row_data[-1] != "高"):
            unmatch_result.append(index)
        else:
            if truth_label == "下派":
                if "不下派" in local_label:
                    FN_result.append(index)
            else:
                if "不下派" not in local_label:
                    FT_result.append(index)
    return unmatch_result, FN_result, FT_result

unmatch_result_index, FN_result_index, FT_result_index = select_bad_case(result)

new_df1 = pd.DataFrame(result, columns=["地域", "一级目录", "二级目录", "受理内容", "主单是否下派", "判定", "理由", "置信度"])
new_df1.to_excel("规则政策_分类结果_500.xlsx", index=False, engine="openpyxl")
