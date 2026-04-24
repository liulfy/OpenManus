


# 计算混淆矩阵
while 0:
    df = pd.read_excel("business_scene/suzhiban/gzzc_vote/ZQ自学习.xlsx", engine="openpyxl")
    data_size = len(df)
    tp = []
    tf = []
    fp = []
    ft = []

    for i in range(data_size):
        row_data = df.iloc[i]
        inference = row_data['inference_result'].strip()
        truth = row_data['人工复核结论'].strip()
        if truth == "下派":
            if inference == "下派":
                tp.append(i)
            else:
                ft.append(i)
        else:
            if inference == "下派":
                fp.append(i)
            else:
                tf.append(i)

    df2 = pd.read_excel("business_scene/suzhiban/gzzc_vote/12月清单_规则政策类_10000_推理结果_result.xlsx", engine="openpyxl")
    data_size = len(df2)

    for i in range(data_size):
        row_data = df2.iloc[i]
        inference = row_data['inference_result'].strip()
        truth = row_data['主单是否下派'].strip()
        if inference == truth:
            if inference == "下派":
                tp.append(i)
            else:
                tf.append(i)



from model_api.doubao_seed_2_lite import query_doubao

# 判断是否与销售品相关
while 0:
    ### split 自学习 data to two sheet.

    user_prompt = "请判断输入的内容，是否明确提及运营商销售品的名称（包括且不限于流量、语音包、权益、云盘会员、礼包）有关。你只需要输出'是'或者'否'，不需要进行解释。\n输入内容为：\n\n\n{reason}"

    result_1 = []
    result_2 = []
    for i in range(data_size):
        row_data = df.iloc[i]
        id = row_data['受理单号']
        content_1 = row_data['一级目录']
        complaint_content = row_data['受理内容']
        parsed_content = row_data['抽取内容']
        inference_result = row_data['inference_result']
        truth_label = row_data['人工复核结论']
        reason = row_data['理由']
        if isinstance(reason, str) and inference_result != truth_label:
            local_result = [id, content_1, complaint_content, parsed_content, inference_result, truth_label, reason]
            judge_result = query_doubao(user_prompt.format(reason = complaint_content))
            print(judge_result)
            if "否" not in judge_result:
                result_2.append(local_result)
            else:
                result_1.append(local_result)
        print(f"finish {i}")

    new_df = pd.DataFrame(result_1, columns=["受理单号", "一级目录", "受理内容", "抽取内容", "inference_result", "人工复核结论", "理由"])
    new_df.to_excel("自学习_销售品不相关结果.xlsx", index=False, engine="openpyxl")

    new_df = pd.DataFrame(result_2, columns=["受理单号", "一级目录", "受理内容", "抽取内容", "inference_result", "人工复核结论", "理由"])
    new_df.to_excel("自学习_销售品相关结果.xlsx", index=False, engine="openpyxl")



while 0:
    from business_scene.suzhiban.goods_judgement.goods_judgement import run_goods_judgement
    data_size = len(result_2)
    for i in range(data_size):
        row_data = result_2[i]
        complaint_content = row_data[2]
        judge_result = run_goods_judgement(complaint_content)
        print(judge_result)

# 构造自学习prompt
while 0:
    df = pd.read_excel("business_scene/suzhiban/gzzc_vote/ZQ自学习.xlsx", engine="openpyxl")
    data_size = len(df)
    result = []
    for i in range(data_size):
        row_data = df.iloc[i]
        id = row_data['受理单号']
        content_1 = row_data['一级目录']
        complaint_content = row_data['受理内容']
        parsed_content = row_data['抽取内容']
        inference_result = row_data['inference_result']
        truth_label = row_data['人工复核结论']
        reason = row_data['理由']
        if isinstance(reason, str) and reason != "":
            local_result = [id, content_1, complaint_content, parsed_content, inference_result, truth_label, reason]
            result.append(local_result)

# 可能需要对这些业务规则进行单独整理，而不是合并到已整理过的规则中
# 但是需要与已有业务场景进行区分，即如何先判断属于哪个场景
# 销售品相关不管，只去看销售品不相关的
import pandas as pd
prompt = """在依据投诉内容判断工单是否下派的场景中，请结合投诉内容与分派判断结果，梳理归纳此类业务数据存在的共性特征。

"""

df = pd.read_excel("business_scene/suzhiban/gzzc_vote/ZQ自学习.xlsx", engine="openpyxl")
data_size = len(df)
for i in range(data_size):
    row_data = df.iloc[i]
    parsed_content = row_data['抽取内容'].strip()
    reason = row_data['理由']
    inference_result = row_data['inference_result']
    truth_label = row_data['人工复核结论']
    if inference_result != truth_label and isinstance(reason, str) and reason != "":
        local_prompt = f"投诉内容：\n{parsed_content}\n分派判断结果：{reason.strip()}\n\n"
        prompt += local_prompt

# 选择欠费违约金
while 0:

    import pandas as pd
    from business_scene.suzhiban.utils.utils import judge_whether_sales
    import threading


    file_path = "/Users/liufengyuan/Desktop/12月清单.xlsx"
    df = pd.read_excel(file_path, engine="openpyxl")

    cities = ["南京市", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"]

    result = [[] for _ in range(13)]

    def run_local_result(result, df, city):
        data_size = len(df)
        save_num = 0
        for i in range(data_size):
            row_data = df.iloc[i]
            id = row_data['受理单号']
            region = row_data['地域'].strip()
            if region != city:
                continue
            content_1 = row_data['一级目录']
            complaint_content = row_data['受理内容']
            label = row_data['主单是否下派']
            if judge_whether_sales(complaint_content):
                local_result = [id, region, content_1, complaint_content, label]
                result.append(local_result)
                print(f"finish run {save_num} in {city}。\n投诉内容：{complaint_content}")
                save_num += 1
                if save_num >= 20:
                    return

    thread_pool = []
    for i in range(13):
        thread_pool.append(threading.Thread(target=run_local_result, args=(result[i], df, cities[i],)))

    for t in thread_pool:
        t.start()

    for t in thread_pool:
        t.join()

    total_result = []
    for i in result:
        total_result.extend(i)

    new_df = pd.DataFrame(total_result, columns=["受理单号", "地域", "一级目录", "受理内容", "主单是否下派"])
    new_df.to_excel("销售品相关结果_v1.xlsx", index=False, engine="openpyxl")

# 推理跑销售品违约金相关
# while 0:

df = pd.read_excel("销售品相关结果_v1.xlsx", engine="openpyxl")
data_size = len(df)
total_result = df.values.tolist()


from business_scene.suzhiban.goods_judgement.goods_judgement import run_goods_judgement
import threading
def run_local_thread(result, total_result, start_index, end_index):
    for i in range(start_index, end_index):
        row_data = total_result[i]
        region = row_data[1]
        complaint_content = row_data[3]
        prompt = f"所在区域：{region}\n投诉内容：{complaint_content}"
        judge_result = run_goods_judgement(prompt)
        result.append(judge_result)
        print(f"finish run {i}/{end_index}")

result = [[] for _ in range(4)]
thread_pool = []
for i in range(4):
    thread_pool.append(threading.Thread(target=run_local_thread, args=(result[i], total_result, i*41, (i+1)*41,)))

for t in thread_pool:
    t.start()

for t in thread_pool:
    t.join()

final_result = []
for i in result:
    final_result.extend(i)

for i in range(164):
    local_result = []
    local_result.extend(total_result[i])
    local_result.append(final_result[i])
    final_result[i] = local_result

new_df = pd.DataFrame(final_result, columns=["受理单号", "地域", "一级目录", "受理内容", "主单是否下派", "推理结果"])
new_df.to_excel("销售品相关结果_v1_推理结果.xlsx", index=False, engine="openpyxl")

run_goods_judgement("南京 创新业务-权益业务/会员随心选")


# 地域	一级目录	受理内容	主单是否下派	分类是否准确






