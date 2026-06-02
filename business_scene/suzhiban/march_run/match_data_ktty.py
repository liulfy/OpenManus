

import pandas as pd
import time
import threading
from business_scene.suzhiban.utils.info_extractor import wash_pending_content, split_thread_data
from math import ceil
# 按地域比例抽取若干条。看效果如何。如果效果不行就直接按地市维度来做。
import random
from business_scene.check_data import analysis_data
from business_scene.check_data import run_inference
from business_scene.suzhiban.complaint_judge_front.run_complaint_judge_front_new import front_complaint
from business_scene.suzhiban.march_run.sale_apis import run_pipeline
from business_scene.suzhiban.march_run.rules_save import yxfw_rule_set, ktty_rule_set


while 0:
    file_name = "business_scene/suzhiban/march_run/szb_3月清单.xlsx"
    df_a = pd.read_excel(file_name, engine="openpyxl")
    file_name2 = "business_scene/suzhiban/march_run/3月清单.xlsx"
    df_b = pd.read_excel(file_name2, engine="openpyxl")

    df_b = df_b.drop('last_self_deal', axis=1)

    merged_result = pd.merge(df_b, df_a[['service_order_id', 'last_self_deal']], on='service_order_id', how='inner')

    merged_result = merged_result.drop_duplicates(subset=['service_order_id'], keep='first')


    schema = ['service_order_id', 'accept_date', 'service_type_desc', 'accept_channel_desc', 'accept_content', 'region_name', 'appeal_prod_name', 'appeal_reason_desc', 'appeal_child_desc', 'prod_one_desc', 'prod_two_desc', 'offer_id', 'number_type', 'prod_num_new', 'cust_id', 'pd_inst_id', 'rela_info', 'cust_tp_id', 'insert_time', 'state', 'dispatch_time', 'dispatch_result', 'area_name', 'sub_station_name', 'is_zy', 'process_type', 'process_orgid', 'work_sheetid', 'dy_date', 'last_self_deal']
    schema_size = len(schema)

    data_size = len(merged_result)
    thread_num = 100


    def run_local_thread(result, df, start_index, end_index):
        for i in range(start_index, end_index):
            row_data = df.iloc[i]
            local_result = result[i]
            for j in range(schema_size):
                local_result.append(row_data[schema[j]])
            washed_data = wash_pending_content(row_data['appeal_prod_name'], '', row_data['accept_content'])
            local_result.append(washed_data)
            print(f"finish run {i}/{end_index} data")

    def thread_run(df, run_func, thread_num):
        data_size = len(df)
        thread_pool = []
        thread_indices = split_thread_data(data_size, thread_num)
        result = [[] for _ in range(data_size)]
        for i in range(thread_num):
            thread_pool.append(threading.Thread(target=run_func, args=(result, df, thread_indices[i], thread_indices[i+1],)))
        for t in thread_pool:
            t.start()
        for t in thread_pool:
            t.join()
        return result


    save_schema = schema.copy()
    save_schema.append('抽取内容')
    result1 = thread_run(merged_result, run_local_thread, thread_num)
    new_df = pd.DataFrame(result1, columns=save_schema)
    new_df.to_excel("szb_3月_new.xlsx", index=False, engine="openpyxl")


['营销服务类', '开通及停用类', '销户退订类', '费用争议类']
file_name = "szb_3月_new.xlsx"
df = pd.read_excel(file_name, engine="openpyxl")
df = df[df['appeal_prod_name'] == '开通及停用类']




cities = ["南京市", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"]
sample_num = 300
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

df.to_excel("szb_3月_开通及停用类_测试数据_300.xlsx", index=False, engine="openpyxl")

#######




df = pd.read_excel("szb_3月_开通及停用类_测试数据_300.xlsx", engine="openpyxl")


def get_result(identity_num, rough_result):
    if "无法判断" in rough_result:
        res = "无法判断"
    elif "集约" in rough_result:
        if "不集约" in rough_result:
            res = "下派"
        else:
            res = "不下派"
    elif "不下派" in rough_result:
        res = "不下派"
    else:
        res = "下派"
    # print(f"res: {res}, id: {identity_num}, input: {rough_result}")
    return res

def run_total_inference(identity_num, region, extract_content, prod_one_desc, prod_num_new, rule_set):
    def _run_1(identity_num, result, extract_content, index1, index2):
        this_result, reason = front_complaint(extract_content)
        result[index1] = get_result(identity_num, this_result)
        result[index2] = reason
    def _run_2(identity_num, result, region, extract_content, index1, index2):
        # result[index1] = "无法判断"
        # result[index2] = "未实际运行"
        retry = 1
        this_result = '无法判断'
        reason = "fail to run"
        while retry:
            try:
                this_result, reason = run_pipeline(identity_num, extract_content, prod_num_new, region, prod_one_desc)
                break
            except Exception as e:
                retry -= 1
                time.sleep(0.1)
                print(e)
                print(f"fail run {identity_num}")
        result[index1] = get_result(identity_num, this_result)
        result[index2] = reason
    def _run_3(result, rule_set, extract_content, index):
        result[index] = get_result(identity_num, run_inference(rule_set, extract_content))

    thread_pool = []
    result = ['', '', '', '', '']
    thread_pool.append(threading.Thread(target=_run_1, args=(identity_num, result, extract_content, 0,1,)))
    thread_pool.append(threading.Thread(target=_run_2, args=(identity_num, result, region, extract_content, 2,3,)))
    thread_pool.append(threading.Thread(target=_run_3, args=(result, rule_set, extract_content, 4,)))
    for t in thread_pool:
        t.start()
    for t in thread_pool:
        t.join()
    # if "无法判断" not in result[0]:
    #     return result[0]
    # if "无法判断" not in result[1]:
    #     return result[1]
    return result

def run_row_data(df, rule_set, result, start_index, end_index):
    for i in range(start_index, end_index):
        row_data = df.iloc[i]
        identity_num = row_data['service_order_id']
        region = row_data['region_name']
        content_1 = row_data['appeal_prod_name']
        pending_content = row_data['accept_content']
        prod_one_desc = row_data['prod_one_desc']
        prod_num_new = row_data['prod_num_new']
        extract_content = row_data['抽取内容'] + f"\n所属区域：{region}"
        to_assign = row_data['last_self_deal']
        inference_result = run_total_inference(identity_num, region, extract_content, prod_one_desc, prod_num_new, rule_set)
        local_result = [identity_num, region, content_1, pending_content, extract_content, to_assign]
        local_result.extend(inference_result)
        print(f"index: {i}, end: {end_index}, true: {to_assign}, result: {inference_result}")
        result[i] = local_result


# id_list = [
#     'TS3025260314781048', 'TS3025260329028664', 'TS3025260321875799', 'TS3025260314773538',
#     'TS3025260315789390', 'TS3025260317824955', 'TS3025260321885785', 'TS3025260319848960',
#     'TS3025260309699630', 'TS30510260315784571', 'TS30510260319852398', 'TS30510260322898550',
#     'TS30516260319853270', 'TS30516260307678986', 'TS30516260308681826', 'TS30516260315784300',
#     'TS30516260322902884', 'TS30516260301567519', 'TS30519260330051354', 'TS30512260326960709',
#     'TS30512260311737702', 'TS30512260321880148', 'TS30512260303611109', 'TS30512260303604178',
#     'TS30512260311737906', 'TS30512260306650212', 'TS30512260323916143', 'TS30512260311734532',
#     'TS30512260329025381', 'TS30512260311730135', 'TS30512260319855058', 'TS30512260306651322',
#     'TS30513260311726997', 'TS30513260325942053', 'TS30518260313764193', 'TS30518260314772915',
#     'TS30518260320860990', 'TS30518260329020531', 'TS30517260307666576', 'TS30517260301573878',
#     'TS30517260329029695', 'TS30515260318829414', 'TS30514260323918928', 'TS30527260331060223',
#     'TS30527260330050374', 'TS30527260318840732', 'TS30527260303602572', 'TS30527260302596004'
# ]
# newdf = df[df['service_order_id'].isin(id_list)]

newdf = df
data_size = len(newdf)
thread_num = 20
thread_pool = []
thread_indices = split_thread_data(data_size, thread_num)
result = [[] for _ in range(data_size)]

for i in range(thread_num):
    thread_pool.append(threading.Thread(target=run_row_data, args=(newdf, ktty_rule_set, result, thread_indices[i], thread_indices[i + 1],)))
for t in thread_pool:
    t.start()
for t in thread_pool:
    t.join()




unmatch_result, FN_result, FT_result = analysis_data(result, True)


new_df = pd.DataFrame(result, columns=['id', '地域', '一级目录', '投诉内容', '抽取内容', "真实标签", "人工规则判断", "人工规则判断解释", "销售品判断", "销售品判断解释", "自学习规则判断", "推理标签"])
new_df.to_excel("szb_3月_开通及停用类_推理结果_use_channel.xlsx", index=False, engine="openpyxl")



