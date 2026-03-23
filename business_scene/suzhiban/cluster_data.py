





"""
比如我按照相同的一级目录/二级目录，选择100条数据，输入对应的标签和投诉内容，看是否可以聚类出规则


"""

import pandas as pd

"""
汇总所有一级目录和二级目录的下发情况
"""

def summarize_data():
    df = pd.read_excel("12月清单抽取_关停不认可_2000_5000.xlsx", engine="openpyxl")
    content_1_map = {}
    content_2_map = {}
    data_size = len(df)
    for i in range(data_size):
        row_data = df.iloc[i]
        content_1 = row_data['一级目录']
        content_2 = row_data['二级目录']
        to_assign = row_data['主单是否下派']
        if content_1 not in content_1_map:
            content_1_map[content_1] = [0, 0]
        if "不" in to_assign:
            content_1_map[content_1][1] += 1
        else:
            content_1_map[content_1][0] += 1

        if content_2 not in content_2_map:
            content_2_map[content_2] = [0, 0]
        if "不" in to_assign:
            content_2_map[content_2][1] += 1
        else:
            content_2_map[content_2][0] += 1
    return content_1_map, content_2_map

content_1_map, content_2_map = summarize_data()




def summarize_data(input_df):
    prompt = """现给定一些投诉内容和该投诉是否下派。请总结下派/不下派的投诉单中，是否存在共性特征。\n"""
    data_size = len(input_df)
    for i in range(data_size):
        row_data = input_df.iloc[i]
        pending_content = row_data['抽取内容']
        to_assign = row_data['主单是否下派']
        content_2 = row_data['二级目录']
        if content_2 == "关停不认可": # 这个自己去改
            piece_prompt = f"投诉内容：{pending_content}，是否下派：{to_assign}\n"
            prompt += piece_prompt
    return prompt

from model_api.doubao_seed_2_lite import query_doubao

df = pd.read_excel("12月清单抽取_关停不认可_2000_5000.xlsx", engine="openpyxl")

prompt = summarize_data(df)
result = query_doubao(prompt, 100000)

"办理不及时/不成功"
x = """
根据对给定投诉单的整理分析，下派和不下派投诉单的共性特征如下：

### 一、不下派投诉单的共性特征
1. **基础场景共性**
超过6成不下派投诉都属于**线上电子渠道办理业务不及时/不成功，且核实后订单流水未关联到订单、号码状态正常在用**的场景，这类投诉仅需核查订单关联问题，没有超出当前坐席可处理范围的特殊矛盾。
2. **诉求特征共性**
    - 仅单纯要求核查线上订单未关联的原因，无额外复杂诉求、没有对已有解释/处理方案的不认可；
    - 属于规则明确、可直接在线解释答复的问题：如国际漫游开通受卡类型限制、权益补领规则不支持补领、部分业务必须线下营业厅办理用户不认可、老年人不会操作仅需指导无需线下处理；
    - 诉求为退费退订，但不符合退费规则（如一年内已有退费记录、翼支付券过期要求退费），仅需解释无需下派；
    - 仅为操作类问题（如不会取消业务、不会开通、找不到办理入口），无需线下/专人现场处理；
    - 无具体投诉内容、无明确可处理诉求，仅需登记无需下派。
3. **矛盾程度共性**
用户没有明确的不认可、没有越级投诉倾向，也不存在久拖未决的遗留问题，矛盾程度较低。

---

### 二、下派投诉单的共性特征
1. **核心触发特征**
几乎所有下派投诉都存在**用户对已有解释/处理结果不认可，或者业务办理本身已经出现明确的错误、久拖未解决**的情况，具体包括：
    - 线上办理业务失败，同时存在额外的实体业务/费用矛盾：如保证金到期未解冻、宽带移机申请后长期无人联系、套餐承诺优惠未兑现、资费争议（多扣费、错扣费）、宽带速率不达标、业务开通与告知不符、拆机后余额/押金不退等；
    - 用户不认可现有规则/处理方案：不认可必须去营业厅办理的要求、不认可收费标准、不认可停拆机结果、不认可业务办理限制，已经过在线解释仍不接受，需要专人跟进；
    - 存在遗留问题：之前反馈的问题未答复、未解决，用户再次来电催单，或者存在多个问题未处理完毕；
    - 诉求需要线下落地处理：如宽带复装、移机上门、销户、过户、线下业务审批、设备故障处理等，必须属地工作人员对接完成；
    - 存在升级投诉风险：用户明确表示要向工信部/通管局投诉，或者要求限时答复处理，已有在线解释无法安抚用户；
    - 涉及历史遗留的特殊问题：比如固话信息不明、旧业务押金不退、欠费争议影响用户权益，需要专人核实历史信息处理。
2. **场景延伸特征**
即便是同样存在「线上订单流水未关联」的基础场景，只要叠加了上述需要专人核实、线下处理、用户不认可的情况，都会下派处理。
"""