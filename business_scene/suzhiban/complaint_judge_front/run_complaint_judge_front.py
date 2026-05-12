

system_prompt = """# 角色定义
你是投诉集约处理判断助手，专门根据预设的业务规则判断用户投诉内容是否需要集约处理。

# 任务目标
你的核心任务是根据用户提供的投诉内容，判断该投诉是否属于"集约处理"场景还是"不集约处理"场景。

# 能力
1. 理解用户描述的投诉内容
2. 调用judge_complaint_centralization工具进行判断
3. 将判断结果以清晰的方式呈现给用户

# 规则说明
业务规则包含两大类：
1. **集约处理场景**：投诉将由省级统一处理，不下派到地市公司
2. **不集约处理场景**：投诉需要下派到地市公司处理

# 输出要求
- 如果投诉内容匹配"集约处理"规则，输出"集约处理"
- 如果投诉内容匹配"不集约处理"规则，输出"不集约处理"
- 如果投诉内容无法匹配任何规则，输出"无法判断"

请用户提供投诉内容，我将为您判断是否需要集约处理。"""

EXCEL_PATH = "/Users/liufengyuan/workspace/OpenManus/business_scene/suzhiban/complaint_judge_front/complaint_rules.xlsx"





"""
投诉集约处理判断工具

该工具用于根据业务规则判断用户的投诉内容是否需要集约处理。
规则来源于Excel文件，包含"不集约处理"和"集约处理"两类场景。
"""


from model_api.doubao_seed_2_lite import query_doubao_with_msgs
import pandas as pd
import os
from typing import Dict, List, Optional


# 缓存已加载的规则
_cached_rules: Optional[Dict] = None


def _load_rules_from_excel() -> Dict:
    """
    从Excel文件加载业务规则

    Returns:
        Dict: 包含集约处理和不集约处理规则的字典
    """
    global _cached_rules

    if _cached_rules is not None:
        return _cached_rules

    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    excel_file = os.path.join(workspace_path, EXCEL_PATH)

    try:
        df = pd.read_excel(excel_file)

        # 提取不集约处理的场景
        not_centralized = []
        col_not_centralized = "工单流向下派地市公司场景（不集约处理）"
        if col_not_centralized in df.columns:
            for val in df[col_not_centralized].dropna().unique():
                if pd.notna(val) and str(val).strip():
                    not_centralized.append(str(val).strip())

        # 提取集约处理的场景
        centralized = []
        col_centralized = "工单流向不下派地市公司场景（集约处理）"
        if col_centralized in df.columns:
            for val in df[col_centralized].dropna().unique():
                if pd.notna(val) and str(val).strip():
                    centralized.append(str(val).strip())

        _cached_rules = {
            "not_centralized": not_centralized,  # 不集约处理
            "centralized": centralized  # 集约处理
        }

        return _cached_rules

    except Exception as e:
        raise Exception(f"加载业务规则文件失败: {str(e)}")


def _match_complaint(complaint_text: str, rules: List[str]) -> bool:
    """
    使用语义匹配判断投诉内容是否匹配规则

    Args:
        complaint_text: 投诉内容
        rules: 规则列表

    Returns:
        bool: 是否匹配
    """
    if not rules or not complaint_text:
        return False

    # 构建prompt进行语义匹配
    msgs = [
        {
            "content": """你是一个投诉内容匹配专家。给定用户的投诉内容和业务规则列表，
        请判断投诉内容是否与规则列表中的任意一条规则匹配。

        匹配规则：
        1. 精确匹配优先
        2. 语义相似匹配（包含关键词、语义相近的表达）
        3. 只要投诉内容涉及规则描述的主题，就应该匹配

        输出要求：
        - 如果匹配，返回 YES
        - 如果不匹配，返回 NO
        - 不要添加任何解释""",
            "role": "system"
        },
        {
            "content": f"""投诉内容：{complaint_text}

业务规则列表：
{rules}

请判断是否匹配（只回答 YES 或 NO）：""",
            "human": "system"
        },
    ]

    try:
        result = query_doubao_with_msgs(msgs)
        return "YES" in result

    except Exception as e:
        # 如果LLM调用失败，使用关键词匹配作为兜底
        return _keyword_match(complaint_text, rules)


def _keyword_match(complaint_text: str, rules: List[str]) -> bool:
    """
    基于关键词的兜底匹配方法

    Args:
        complaint_text: 投诉内容
        rules: 规则列表

    Returns:
        bool: 是否匹配
    """
    complaint_lower = complaint_text.lower()

    for rule in rules:
        # 检查规则中的关键词是否出现在投诉内容中
        # 提取关键名词进行匹配
        keywords = [k.strip() for k in rule.split() if len(k.strip()) >= 2]
        match_count = sum(1 for k in keywords if k.lower() in complaint_lower)

        # 如果匹配关键词数量超过阈值，认为匹配
        if len(keywords) > 0 and match_count >= min(2, len(keywords)):
            return True

        # 检查投诉内容是否包含规则的核心词汇
        core_terms = [term for term in ["流量", "宽带", "iTV", "增值业务", "会员", "漫游", "套餐",
                                         "营销", "营业厅", "故障", "网络", "费用", "欠费", "订单",
                                         "号码", "服务态度", "积分", "宽带", "亲情"]
                      if term in rule]

        if core_terms:
            if any(term in complaint_lower for term in core_terms):
                return True

    return False


def judge_complaint_centralization(complaint_content: str) -> dict:
    """
    判断用户投诉内容是否需要集约处理

    根据预设的业务规则，判断投诉内容属于"集约处理"还是"不集约处理"场景。
    如果无法匹配任何规则，返回"无法判断"。

    Args:
        complaint_content: 用户的投诉内容描述，要求详细、完整

    Returns:
        str: 判断结果，格式为JSON字符串，包含以下字段：
            - result: "centralized"（集约处理）、"not_centralized"（不集约处理）或 "unable_to_judge"（无法判断）
            - reason: 判断原因说明
            - matched_rule: 匹配的具体规则（如果有）
    """

    if not complaint_content or not complaint_content.strip():
        return {
            "result": "无法判断",
            "reason": "投诉内容为空，无法判断",
            "matched_rule": None
        }

    complaint_text = complaint_content.strip()

    try:
        rules = _load_rules_from_excel()

        # 首先尝试匹配集约处理规则
        if _match_complaint(complaint_text, rules["centralized"]):
            # 找到具体匹配的规则
            matched = _find_best_match(complaint_text, rules["centralized"])
            return {
                "result": "下派",
                "reason": "投诉内容属于集约处理场景，将由省级统一处理",
                "matched_rule": matched
            }

        # 尝试匹配不集约处理规则
        if _match_complaint(complaint_text, rules["not_centralized"]):
            matched = _find_best_match(complaint_text, rules["not_centralized"])
            return {
                "result": "不下派",
                "reason": "投诉内容属于不集约处理场景，需要下派至地市公司处理",
                "matched_rule": matched
            }

        # 无法匹配任何规则
        return {
            "result": "无法判断",
            "reason": "投诉内容未匹配到预设的业务规则，无法判断是否需要集约处理",
            "matched_rule": None
        }

    except Exception as e:
        return {
            "result": "无法判断",
            "reason": f"判断过程发生错误: {str(e)}",
            "matched_rule": None
        }


def _find_best_match(complaint_text: str, rules: List[str]) -> Optional[str]:
    """
    找到与投诉内容最佳匹配的规则

    Args:
        complaint_text: 投诉内容
        rules: 规则列表

    Returns:
        str: 最佳匹配的规则，如果没有匹配则返回None
    """
    best_match = None
    best_score = 0

    complaint_lower = complaint_text.lower()

    for rule in rules:
        rule_lower = rule.lower()

        # 计算关键词重叠度
        keywords = [k.strip() for k in rule.split() if len(k.strip()) >= 2]
        match_count = sum(1 for k in keywords if k.lower() in complaint_lower)

        # 考虑核心业务词匹配
        core_terms = ["流量", "宽带", "iTV", "增值业务", "会员", "漫游", "套餐",
                      "营销", "营业厅", "故障", "网络", "费用", "欠费", "订单",
                      "号码", "服务态度", "积分", "亲情宽带", "违约金", "视频"]
        core_match = sum(1 for term in core_terms if term in rule_lower and term in complaint_lower)

        score = match_count + core_match * 2

        if score > best_score:
            best_score = score
            best_match = rule

    return best_match



if __name__ == "__main__":
    res = judge_complaint_centralization("")
    print(res)
