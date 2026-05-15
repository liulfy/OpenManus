from model_api.doubao_seed_2_lite import query_doubao_stream


def judge_assign_or_not(feature_prompt, user_complaint, reason=False):
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
    return query_doubao_stream(judge_assign_prompt, 200, "enabled")


def select_bad_case(judge_result, pred_label_index=4, truth_label_index=5):
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
    user_prompt = "请判断输入的内容，是否针对运营商销售品（包括且不限于流量、语音包、权益、云盘会员、礼包）违约金/否认订购进行投诉的。" \
                  "请注意，投诉内容中必须提及销售品名称，并明确表示对该销售品的违约金不认可，或者否认订购该销售品。" \
                  "如果是的，请你输出销售品名称。如果不是，请你'否'。你不需要输出其它任何内容，不需要进行解释。\n输入内容为：\n\n\n{complaint_content}"
    prompt = user_prompt.format(complaint_content=complaint_content)
    judge_result = query_doubao_stream(prompt)
    if "否" in judge_result:
        return 0
    return judge_result


def front_complaint(complaint_content):
    user_prompt = f"""
    你是一个智能客服投诉助手，请判断用户的投诉内容是否在以下内容中。
    你只需要输出'是'或者'否'，不需要进行解释。
    判断内容为：
    客户登记赠送免费 /**G 流量
    电信机房、设备相关问题
    营业厅业务办理问题：业务漏受理、办理差错、解释说明不清
    接到 10000 号营销电话争议（剔除外呼工号 30839、38开头、36、31、30开头派省层面）
    政企客户对本金 + 滞纳金欠费不认可
    涉及营业厅、装维、线下门店相关投诉问题
    网络质量类：网速慢、信号差、网络不稳定
    含智慧家 / 智家 / ACAP / 面板 / 终端 / 中屏 / 门锁 / 子母路由 / 银行保证 / CFQ / 橙分期的否认办业务、违约金争议
    涉及宽带及路由器安装咨询、投诉
    固话 / 宽带 /iTV/ 手机无法正常使用（断网、故障、宽带网速异常等）
    固话号码二次放号相关问题
    要求取消 VPN 业务


    用户投诉内容为：
    {complaint_content}
    """
    prompt = user_prompt.format(complaint_content=complaint_content)
    judge_result = query_doubao_stream(prompt)
    if "否" in judge_result:
        return "无法判断"
    return "下派"


# 需要先安装python-Levenshtein库
# 安装命令：pip install python-Levenshtein
from Levenshtein import distance


def find_closest_string_list(target: str, string_list: list, distance_threshold: int = -1) -> str:

    if not string_list:  # 处理空列表边界情况
        return ""

    # 找到距离最小的字符串
    closest_str = min(string_list, key=lambda s: distance(target, s))
    if distance_threshold < 0:
        return closest_str
    # 计算最小距离
    min_dist = distance(target, closest_str)
    print(f"{target}, {closest_str}, {min_dist}")
    # 判断是否满足阈值条件：最小距离 < 阈值
    if min_dist < distance_threshold:
        return closest_str
    # 不满足条件返回空字符串
    return ""


import Levenshtein
def find_closest_string(target: str, string_dict: dict, distance_threshold: int = -1) -> str:
    """
    调库计算列文斯顿距离，返回最接近的字符串
    """
    string_list = string_dict.keys()
    # 按距离从小到大排序，取第一个
    closest_str = min(string_list, key=lambda s: Levenshtein.distance(target, s))
    if distance_threshold < 0:
        return closest_str
    # 计算最小距离
    min_dist = distance(target, closest_str)
    print(f"{target}, {closest_str}, {min_dist}")
    # 判断是否满足阈值条件：最小距离 < 阈值
    if min_dist < distance_threshold:
        return closest_str
    # 不满足条件返回空字符串
    return " "

# def find_closest_string_list(target: str, string_list: list) -> str:
#     """
#     调库计算列文斯顿距离，返回最接近的字符串
#     """
#     # 按距离从小到大排序，取第一个
#     return min(string_list, key=lambda s: Levenshtein.distance(target, s))



from model_api.doubao_seed_2_lite import query_doubao_stream, query_doubao_batch

def judge_whether_contain_product(product, product_list):
    prompt = f"输入的投诉内容中包含了投诉的产品。请判断投诉产品是否在给到的产品列表中。" \
             f"请注意，投诉的产品名称可能会存在拼写错误，拼写不规范等问题，只要语义能够匹配，即认为匹配。" \
             f"如果投诉内容中没有提到投诉产品，或者投诉产品没有匹配上，请输出'不匹配'。如果匹配上了，请输出列表中标准的产品名称。" \
             f"你不需要输出其它任何字符" \
             f"输入的产品列表为：\n{product_list}" \
             f"\n\n\n输入的投诉内容为：\n{product}"
    res = query_doubao_stream(prompt, 50, 'enabled')
    if '不匹配' in res:
        return 0
    res = find_closest_string_list(res, product_list, 5)
    if not res:
        return 0
    return res


def judge_whether_contain_complaint_type(complaint_clause, product_list):
    prompt = f"请判断给定投诉内容中的争议，是否包含在给到的投诉争议列表中。" \
             f"请注意，只要语义能够匹配，即认为匹配。" \
             f"如果没有包含，请输出'不匹配'。如果匹配上了，请输出列表中对应的争议。" \
             f"你不需要输出其它任何字符" \
             f"输入的投诉争议列表为：\n{product_list}" \
             f"\n\n\n输入的投诉内容为：\n{complaint_clause}"
    res = query_doubao_stream(prompt, 50, 'enabled')
    if '不匹配' in res:
        return 0
    print(f"投诉内容：{complaint_clause}，匹配争议：{res}")
    return res