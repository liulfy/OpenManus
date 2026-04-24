


file_path = "business_scene/suzhiban/goods_judgement/违约金争议场景清单.xlsx"
"""
region_name
accept_content
service_order_id
"""

from business_scene.suzhiban.goods_judgement.goods_judgement import run_goods_judgement

import pandas as pd

df = pd.read_excel(file_path, engine="openpyxl")

data_size = len(df)

result = ["" for _ in range(data_size)]
import threading

def run_single_inference(result, start_index, end_index, df):
    for i in range(start_index, end_index):
        row_data = df.iloc[i]
        id = row_data['service_order_id']
        region_name = row_data['region_name']
        accept_content = row_data['accept_content']
        complaint_content = f"区域：{region_name}\n投诉内容：{accept_content}"
        judge_result = run_goods_judgement(complaint_content)
        local_result = [id, region_name, accept_content, judge_result]
        result[i] = local_result
        print(f"finish run {i}/{end_index}, {judge_result}")

indices = [0, 21, 42, 63, 84, 105, 126]
thread_pool = []
for i in range(6):
    thread_pool.append(threading.Thread(target=run_single_inference, args=(result, indices[i], indices[i+1], df,)))

for t in thread_pool:
    t.start()

for t in thread_pool:
    t.join()


new_df = pd.DataFrame(result, columns=["service_order_id", "region_name", "accept_content", "inference_result"])
new_df.to_excel("销售品推理结果.xlsx", index=False, engine="openpyxl")

# run_goods_judgement("天翼云盘铂金会员10元/12个月 南通")

