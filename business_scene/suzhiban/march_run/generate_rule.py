
import pandas as pd

df = pd.read_excel("business_scene/suzhiban/march_run/szb_3月_new.xlsx", engine="openpyxl")
df = df[df['appeal_prod_name'] == '开通及停用类']


from math import ceil
# 按地域比例抽取若干条。看效果如何。如果效果不行就直接按地市维度来做。
import random
cities = ["南京市", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"]
sample_num = 500
random.seed(10)

city_save = {}
for i in cities:
    city_save[i] = [[], []]

data_size = len(df)
total_size = 0
for i in range(data_size):
    row_data = df.iloc[i]
    region = row_data['region_name']
    if region in city_save:
        city_save[region][0].append(i)
        total_size += 1

ratio = sample_num / total_size
total_cases = []
for i in cities:
    candidate = city_save[i][0]
    this_sample_num = ceil(ratio*len(candidate))
    city_save[i][1].extend(random.sample(candidate, this_sample_num))
    for index in city_save[i][1]:
        row_data = df.iloc[index]
        region = row_data['region_name']
        content = row_data['抽取内容']
        label = row_data['last_self_deal']
        this_case = f"***投诉单明细\n{content}\n所属区域：{region}\n***投诉单是否下派：{label}\n\n\n"
        total_cases.append(this_case)

random.shuffle(total_cases)

###
get_indices = []
for k in city_save:
    get_indices.extend(city_save[k][1])

df = df.iloc[get_indices]
###



prompt_template = "现有投诉文本数据及对应工单下派结果标签，需分别梳理、总结下派 / 不下派两类投诉工单的共性特征，为新增工单的下派判定提供依据。你总结的共性特征应当尽可能详细。\n\n\n"
for case in total_cases:
    prompt_template = prompt_template + case

