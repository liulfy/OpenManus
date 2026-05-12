

import pandas as pd
from model_api.doubao_seed_2_lite import query_doubao
from business_scene.suzhiban.back.info_extractor import wash_pending_content

# doubao-seed-2.0-pro 260215
feature_prompt = """
SUPER RULE：如与以下规则匹配，则优先按此规则操作
0.1 对于中风险双停的，任何时候均不下派。
0.2 针对中风险单停，输出无法判断。

一、不下派规则（满足任意一条即可判定不下派）

1.1 用户仅笼统表述 “对封停不认可、要求尽快处理”，未提及无法通过自助 / 线下常规渠道复机的客观困难，也无额外诉求的，不下派。
1.2 用户仅因主观意愿（如嫌麻烦）不愿配合常规复机流程（不愿去营业厅、不愿自助操作），无客观阻碍的，不下派。
1.3 用户仅收到停机预警短信、号码仍正常在用，仅提出 “不要停机、核实预警原因” 诉求的，不下派。
1.4 用户复机次数已达自然年上限（如同名下年复机≥3 次），不符合常规复机规则的，不下派。
1.5 用户对停机原因、复机流程的标准解释不认可，但无新的事实依据或合理额外诉求的，不下派。
1.6 用户对常规赔偿方案（如 20-30 元话费补偿）不认可，但未提出合理的额外损失依据的，不下派。
1.7 用户自助复机过程中出现操作类问题（如上传身份证卡顿、通道占用、邀约码失效等），前台可直接指导操作或重发邀约码解决的，不下派。
1.8 用户仅提出加急处理诉求，但无特殊紧急场景、无复机客观办理障碍的，不下派。
1.9 用户提出不符合服务规范的无合理依据诉求（如要求出具停机大数据模型的详细涉密依据、要求工作人员上门道歉等），可通过标准口径回应的，不下派。


二、下派规则（满足任意一条即可判定下派）

2.1 号码用护照、军官证等非居民身份证登记，线上 / 常规营业厅无法办理复机的，下派。
2.2 机主为高龄老人、未成年人等特殊群体，无法自主操作或到厅办理复机的，下派。
2.3 用户手机卡 / 身份证丢失，出现 “补卡需先复机、复机需用卡收验证码” 的流程矛盾，无法通过常规流程解决的，下派。
2.4 机主在境外、异地，无法到归属地指定营业厅办理，且线上渠道因身份核验问题无法使用的，下派。
2.5 用户已多次尝试自助复机、比邻柜台操作均失败，或已前往多家营业厅办理均未成功的，下派。
2.6 停机类型为工信部断卡行动停机、集团大数据保护性停机、公安要求停机等前台无处理权限的特殊关停类型的，下派。
2.7 存在服务 / 流程差错（如之前承诺 3-5 分钟处理完成实际需 3-5 天、复机后仍无法正常使用等），需要核查整改的，下派。
2.8 用户有合理理由需突破现有复机规则（如工作机因正常通话频繁被停机、年复机次数已满但确有紧急使用需求），需要特殊审批复机的，下派。
2.9 存在明确费用纠纷（如停机期间仍正常扣费、因停机导致无法取消业务产生额外费用），需要后台核实账目处理的，下派。
2.10 用户提出非停机类特殊诉求（如宽带已拆机仍被催缴欠费等），需要后台核查历史业务记录的，下派。
2.11 号码为办公用卡急需开展业务、用户在机场 / 外地出差急需用卡、家中老人 / 小孩急事需用卡，且无法通过常规流程快速办理的，下派。
2.12 用户已多次致电投诉，常规口径解释无效，且诉求合理（如多次无故停机、复机流程长期卡壳），需要专人对接处理的，下派。


三、边界判定规则（相似场景优先按本规则判定）

3.1 针对 “不愿去营业厅要求线上复机” 场景：仅主观不愿去的适用不下派规则，因客观原因（人在境外、证件丢失等）无法去的适用下派规则。
3.2 针对 “着急使用要求加急” 场景：仅情绪着急但可走常规流程的适用不下派规则，存在特殊紧急场景 + 复机办理障碍的适用下派规则。
3.3 针对 “对复机次数上限不认可” 场景：仅不满规则无合理理由的适用不下派规则，确有正常使用需求（如工作机通话多非骚扰）的适用下派规则。


"""

def judge_assign_or_not(user_complaint):
    judge_assign_prompt = f"""
    请结合给定的下派和不下派投诉单的共性特征，判断给定的投诉内容属于以下哪个特征，并输出"下派"或者"不下派"。如果无法判断是否下派，则输出"无法判断"
    你需要综合判断是否下派。
    特征：
    {feature_prompt}
    
    用户投诉如下：
    {user_complaint}
    """
    return query_doubao(judge_assign_prompt, 200)


df = pd.read_excel("12月清单抽取_关停不认可_5000_10000.xlsx", engine="openpyxl")

data_size = 30
result = []
for index in range(100, 200):
    row_data = df.iloc[index]
    identity_num = row_data['受理单号']
    content_1 = row_data['一级目录']
    content_2 = row_data['二级目录']
    pending_content = row_data['受理内容']
    # extracted_content = row_data['抽取内容']
    extracted_content = wash_pending_content(content_1, content_2, pending_content)
    to_assign = row_data['主单是否下派']
    judge_result = judge_assign_or_not(pending_content)
    print(f"index: {index}，判断结果：{judge_result}, 真实标签：{to_assign}")
    result.append([identity_num, content_1, content_2, pending_content, extracted_content, judge_result, to_assign])


new_df1 = pd.DataFrame(result, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "判断结果", "主单是否下派"])
new_df1.to_excel("关停不认可_校验结果.xlsx", index=False, engine="openpyxl")



"""对于判断不对的，分析什么原因"""


def select_bad_case(judge_result):
    result = []
    for row_data in judge_result:
        local_label = row_data[5]
        truth_label = row_data[6]
        prompt = f"""你将会给到一个判断的真实标签和用户推导的结论。请你判断推导结论是否与真实标签一致。如果一致请输出1，不一致输出0，不需要输出其它内容。
        真实标签为：{truth_label}
        推导结论为：{local_label}"""
        match_result = query_doubao(prompt)
        print(f"判断结果：{local_label}, 真实标签：{truth_label}, 判断结论：{match_result}")
        if '0' in match_result:
            result.append(row_data)
    return result

unmatch_result = select_bad_case(result)



def update_rules(unmatch_result):
    update_prompt = f"""
    以下任务中，会依据业务规则，根据用户的投诉内容，判断是否是否下派。
    你将会给到若干判断错误的例子。请你结合这些例子以及这些例子中的判断依据，总结出原有业务规则中的不足，并对原有业务规则进行调整。
    请注意，你在分析判断错误的例子时，不得将单个例子的问题总结为业务特征。只有出现过较多次数、具有一定共同点的问题才能总结为业务规则。
    业务规则如下：
    {feature_prompt}\n\n"""
    for row_data in unmatch_result:
        this_prompt = f"\n投诉内容：{row_data[4]}, 判断情况：{row_data[5]}, 真实标签：{row_data[6]}"
        update_prompt += this_prompt
    print(update_prompt)
    return query_doubao(update_prompt, 100000)

rule = update_rules(unmatch_result)



fail_data_index = [34, 36, 41, 47, 51, 52, 60, 64, 73, 70, 71, 74, 75, 76, 79, 80, 81, 82, 86, 91, 95, 97]