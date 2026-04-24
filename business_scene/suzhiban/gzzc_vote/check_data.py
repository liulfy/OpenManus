

from model_api.doubao_seed_2_lite import query_doubao

def judge_assign_or_not(complaint_content, feature):
    judge_assign_prompt = f"""依据投诉单下派与不下派的共性特征，判定该投诉内容是否需要下派。若依据给定特征无法确定，输出 “无法判断”。仅输出：下派 / 不下派 / 无法判断，无需其他任何信息。
共性特征为：
{feature}
---
投诉内容为：{complaint_content}
"""
    return query_doubao(judge_assign_prompt, 200, [], "disabled")



import threading
from business_scene.suzhiban.gzzc_vote.cluster_data import updated_gzzc_rule as gzzc_rule

def run_single_inference(rule, complaint_content, result_save, index):
    # result_save[index] = judge_assign_or_not(complaint_content, rule)
    retry_time = 5
    while retry_time:
        try:
            result_save[index] = judge_assign_or_not(complaint_content, rule)
            return
        except Exception as e:
            retry_time -= 1
    return

def run_inference(rules, complaint_content):
    result = ['', '', '']
    t1 = threading.Thread(target=run_single_inference, args=(rules['gemini'], complaint_content, result, 0,))
    t2 = threading.Thread(target=run_single_inference, args=(rules['doubao'], complaint_content, result, 1,))
    t3 = threading.Thread(target=run_single_inference, args=(rules['deepseek'], complaint_content, result, 2,))
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
    return result

def run_row_data(df, gzzc_rule, result, start_index, end_index):
    for i in range(start_index, end_index):
        row_data = df.iloc[i]
        identity_num = row_data['受理单号']
        content_1 = row_data['一级目录']
        pending_content = row_data['受理内容']
        extract_content = row_data['抽取内容']
        to_assign = row_data['主单是否下派']
        inference_result = run_inference(gzzc_rule, extract_content)
        local_result = [identity_num, content_1, pending_content, extract_content, to_assign]
        local_result.extend(inference_result)
        print(f"index: {i}, end: {end_index}, true: {to_assign}, result: {inference_result}")
        result[i] = local_result


import pandas as pd
df = pd.read_excel("data_save/12月清单_规则政策类_10000.xlsx", engine="openpyxl")
data_size = len(df)

result = [[] for _ in range(data_size)]
indices = [0, 129, 258, 387, 516]
# indices = [0, 25, 50, 75, 100]
thread_pool = []
for i in range(4):
    t = threading.Thread(target=run_row_data, args=(df, gzzc_rule, result, indices[i],indices[i+1],))
    thread_pool.append(t)

for t in thread_pool:
    t.start()
for t in thread_pool:
    t.join()

while 0: # 挂了重跑
    for row_data in result:
        if not row_data[5] or not row_data[6] or not row_data[7]:
            complaint_content = row_data[3]
            inference_result = run_inference(gzzc_rule, complaint_content)
            row_data[5] = inference_result[0]
            row_data[6] = inference_result[1]
            row_data[7] = inference_result[2]
            print(f"true: {row_data[4]}, inference_result: {inference_result}")


def analysis_result(a, b, c):
    # return c
    inference_result = [a, b, c]
    n1 = inference_result.count("下派")
    n2 = inference_result.count("不下派")
    n3 = 3-n1-n2
    max_count = max(n1, n2, n3)
    if max_count == 1:
        # return "无法判断"
        return "不下派"
    if max_count >= 2:
        if n1 == max_count:
            return "下派"
        elif n2 == max_count:
            return "不下派"
        # return "无法判断"
        return "不下派"

def analysis_data(result):
    unmatch_result = []
    FN_result = []
    FT_result = []
    data_size = len(result)
    # data_size = 100
    for index in range(data_size):
        row_data = result[index]
        inference_label = analysis_result(row_data[5], row_data[6], row_data[7])
        true_label = row_data[4]
        if "无法判断" == inference_label:
            unmatch_result.append(index)
        else:
            if true_label == "下派":
                if "不下派" in inference_label:
                    FN_result.append(index)
            else:
                if "不下派" not in inference_label:
                    FT_result.append(index)
    return unmatch_result, FN_result, FT_result

unmatch_result, FN_result, FT_result = analysis_data(result)



new_df = pd.DataFrame(result, columns=["受理单号", "一级目录", "受理内容", "抽取内容", "主单是否下派", "gemini_result", "doubao_result", "deepseek_result"])


new_df.to_excel("12月清单_规则政策类_10000_推理结果_v2.xlsx", index=False, engine="openpyxl")

df = pd.read_excel("12月清单_规则政策类_10000_推理结果.xlsx", engine="openpyxl")
result = []
data_size = len(df)
for i in range(data_size):
    local_result = df.iloc[i].to_list()
    local_result.append(analysis_result(local_result[-1], local_result[-2], local_result[-3]))
    result.append(local_result)

new_df = pd.DataFrame(result, columns=["受理单号", "一级目录", "受理内容", "抽取内容", "主单是否下派", "gemini_result", "doubao_result", "deepseek_result", "inference_result"])
new_df.to_excel("12月清单_规则政策类_10000_推理结果_result.xlsx", index=False, engine="openpyxl")

