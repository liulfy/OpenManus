
from model_api.doubao_seed_2_lite import query_doubao

def judge_assign_or_not(feature_prompt, user_complaint, reason = False):
    if reason:
        reason_prompt = "并说明理由。"
    else:
        reason_prompt = ""
    judge_assign_prompt = f"""
    请结合给定的下派和不下派投诉单的判断规则，判断给定的投诉内容属于具体哪类场景，并输出"下派"或者"不下派"。如果无法判断是否下派，请输出"无法判断"。
    你需要综合判断是否下派。{reason_prompt}
    判断规则：
    {feature_prompt}

    用户投诉如下：
    {user_complaint}
    """
    return query_doubao(judge_assign_prompt, 200)


def select_bad_case(judge_result, pred_label_index = 4, truth_label_index = 5):
    unmatch_result = []
    FN_result = []
    FT_result = []
    for index, row_data in enumerate(judge_result):
        local_label = row_data[pred_label_index]
        truth_label = row_data[truth_label_index]
        if "无法判断" in local_label:
            unmatch_result.append(index)
        else:
            if truth_label == "下派":
                if "不下派" in local_label:
                    FN_result.append(index)
            else:
                if "不下派" not in local_label:
                    FT_result.append(index)
    return unmatch_result, FN_result, FT_result


def judge_whether_sales(complaint_content):
    user_prompt = "请判断输入的内容，是否针对运营商销售品（包括且不限于流量、语音包、权益、云盘会员、礼包）违约金进行投诉的。" \
                  "请注意，投诉内容中必须提及销售品名称，并明确表示对该销售品的违约金不认可。" \
                  "你只需要输出'是'或者'否'，不需要进行解释。\n输入内容为：\n\n\n{complaint_content}"
    prompt = user_prompt.format(complaint_content = complaint_content)
    judge_result = query_doubao(prompt)
    if "否" in judge_result:
        return 0
    return 1

