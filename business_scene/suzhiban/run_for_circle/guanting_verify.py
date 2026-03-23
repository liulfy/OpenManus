

import pandas as pd
from model_api.doubao_seed_2_lite import query_doubao
from business_scene.suzhiban.info_extractor import wash_pending_content

feature_prompt = """### 一、下派投诉单的特征
同时满足以下两个条件才应当下派：
1. **属于可下派的风险类型，或满足例外触发条件**：
   - 非中风险双停、非低风险单停的停机场景，可触发下派判断；
   - 中风险双停/低风险单停场景，仅在同时满足「用户已尝试常规复机流程操作失败」+「存在明确升级投诉风险/紧急诉求」两个条件时，才可触发下派，其余情况均不下派。
2. **满足任意一项下派通用条件**：
   （1）存在特殊客观场景，现有流程无法满足需求：
   - 用户卡丢失、异地补卡要求先复机，或者已补卡但系统识别异常无法复机；
   - 机主身处境外/外地，不方便到归属地指定营业厅办理，且**已尝试线上自助操作失败**；
   - 机主为高龄老人，无法自行操作/到厅办理；
   - 证件特殊（如用护照登记，证件不在身边/异地无法线下办理）；
   - 实际使用人离职、机主和卡片/实际使用人分离，无法完成自助实人认证，且引导后用户仍无法完成操作；
   - 线下营业厅多次办理都未成功复机，常规流程无法解决问题。
   （2）用户有明确的超出常规解释的诉求，且前期解释无效：
   - 用户不认可运营商给出的停机原因解释，明确要求核查出具体停机原因、给出明确说法，甚至要求提供关停证据、对应规则依据；
   - 除复机外还附带额外诉求：比如要求退还停机期间的扣费、赔偿停机造成的损失、投诉工作人员态度问题、要求道歉，或是要求承诺后续不再对该号码停机、将号码加入白名单；
   - 用户明确表示不认可已经给出的处理方案（比如不认可线下营业厅办理的要求、不认可低金额补偿方案），坚持要求其他解决方案，且解释无效。
   （3）情况紧急/存在升级投诉风险：
   - 用户有紧急用机需求，比如要赶飞机、紧急办公、急需联系，要求限时处理；
   - 用户明确表达了不满，针对规则政策类的问题，提出如果不按时处理就向工信部/12345越级投诉，或者已经发起越级投诉需要跟进处理。
   （4）存在特殊异常场景：
   比如已经完成实名认证仍被停机、复机流程出现故障（邀约码失效、系统排队、认证通道卡住）、停机类型异常、已经按要求办理复机但未成功等。

---

### 二、不下派投诉单的特征
满足任意一项特征即不下派：
1. 中风险双停，未同时满足「已尝试常规复机失败+存在升级投诉风险/紧急诉求」；
2. 低风险单停，未同时满足「已尝试常规复机失败+存在升级投诉风险/紧急诉求」；
3. 诉求简单常规，可通过现有流程引导解决：仅笼统提出“对停机不认可，要求尽快处理/要求复机”，没有特殊困难，一线坐席可直接引导用户通过线上自助、线下营业厅的常规流程办理，不需要线下跟进处理；
4. 符合现有规则限制，无需下派：
   - 用户违反了自然年内复机次数限制，坚持要求再次复机，规则已明确无法办理，仅需做好解释，无需下派跟进；
   - 用户拒绝配合任何复机操作（拒绝自助认证、拒绝到厅、拒绝提供相关信息），没有可推进处理的空间，无需下派；
5. 已有工单在跟进处理，用户仅为催促：问题已经进入处理流程，用户来电仅为催促加急，不需要新开下派工单跟进；
6. 用户仅提出质疑，号码尚未实际停机：比如用户仅不认可收到的二次停机提醒短信，号码目前仍正常使用，可直接在线解释，不需要下派；
7. 无特殊困难，仅普通诉求：用户仅要求核查停机原因、要求复机，没有特殊的客观阻碍，也没有升级投诉倾向，一线可直接引导处理，不需要下派。

---

### 补充说明
存在少量模糊案例（比如同是“用户人在外地要求线上复机”，部分下派部分不下派），核心差异是：如果用户已经尝试过常规流程失败、或是解释后仍不接受方案、同时满足对应风险等级的下派触发条件，就会下派；如果仅提出无法办理的困难，未尝试流程、也无紧急诉求/升级风险，则不下派。"""

def judge_assign_or_not(user_complaint):
    judge_assign_prompt = f"""
    请结合给定的下派和不下派投诉单的共性特征，判断给定的投诉内容属于以下哪个特征，并输出是否下派。
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
for index in range(100):
    row_data = df.iloc[index]
    identity_num = row_data['受理单号']
    content_1 = row_data['一级目录']
    content_2 = row_data['二级目录']
    pending_content = row_data['受理内容']
    extracted_content = row_data['抽取内容']
    to_assign = row_data['主单是否下派']
    judge_result = judge_assign_or_not(extracted_content)
    print(f"index: {index}，判断结果：{judge_result}, 真实标签：{to_assign}")
    result.append([identity_num, content_1, content_2, pending_content, extracted_content, judge_result, to_assign])


new_df1 = pd.DataFrame(result, columns=["受理单号", "一级目录", "二级目录", "受理内容", "抽取内容", "抽取特征", "主单是否下派"])
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