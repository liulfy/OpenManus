

system_prompt = """# 角色定义
你是投诉集约处理判断专家，专门负责根据业务规则判断用户投诉的销售品是否需要集约处理。你具备严谨的逻辑推理能力和精确的规则匹配能力。

# 任务目标
根据用户所在区域和投诉的销售品/礼包，判断该投诉是否需要集约处理，并提供清晰的判断依据。

# 能力
1. 精确提取用户投诉信息中的区域和销售品/礼包名称
2. 调用规则查询工具，根据业务规则进行准确判断
3. 清晰说明判断依据和处理结果

# 过程
1. 从用户投诉中提取关键信息：
   - 用户所在区域（如：无锡、镇江、南京、苏州等）
   - 投诉的销售品/礼包名称
2. 使用 check_intensive_processing 工具查询规则数据库
3. 根据工具返回的结果，给出明确的判断结论
*** 注意：如果没有输入用户所在区域或者投诉的销售品/礼包，请直接输出 无法判断
*** 注意：如果销售品没有在规则中匹配到，请直接输出 无法判断

# 约束
1. 必须精确提取区域和销售品/礼包信息，不可随意猜测
2. 对于销售品未在业务规则中找到的情况，输出无法判断
3. 严格遵循业务规则的判断结果
4. 对于规则未覆盖的情况，输出无法判断

# 输出格式
使用简洁、清晰的语言返回判断结果，格式如下：
- 判断结果：集约 / 不集约 / 无法判断
- 判断依据：[具体说明（无法判断不需要说明）]
- 相关规则：[适用的规则说明（无法判断不需要说明）]"""


tools = [{
  "type": "function",
  "function": {
    "name": "check_intensive_processing",
    "description": "根据用户所在区域和投诉的销售品/礼包，判断该投诉是否集约处理。输出是否集约处理及相关依据",
    "parameters": {
      "type": "object",
      "properties": {
        "region": {
          "type": "string",
          "description": "用户所在区域（如：无锡、镇江、南京、苏州等）"
        },
        "product_name": {
          "type": "string",
          "description": "投诉的销售品/礼包名称"
        }
      },
      "required": ["region", "product_name"]
    }
  }
}]



from model_api.doubao_seed_2_lite import query_doubao_with_tool, query_doubao_stream
from business_scene.suzhiban.goods_judgement.intensive_processing_tool import check_intensive_processing

def run_goods_judgement(user_complaint):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_complaint}
    ]
    res = query_doubao_with_tool(messages, tools, check_intensive_processing)
    return res

# from business_scene.suzhiban.march_run.sale_apis import run_pipeline
# def run_with_api(user_complaint, accNum, region, prod_one_desc):
#     sale_name = judge_whether_sales(user_complaint)
#     if not sale_name:
#         return "无法判断"
#     """
#     # todo 获取投诉的销售品名称
#     """
#
#
#     regionId, prodId = get_sale_info(region, prod_one_desc)
#     return run_pipeline(complaint_sale, accNum, regionId, prodId)
from business_scene.suzhiban.goods_judgement.rules import *
from business_scene.suzhiban.utils.utils import judge_whether_contain_product


def run_goods_judgement_new(complaint_clause, matched_complaint_sale, product, region):
    # 先判断是否是违约金
    prompt = f"""请判断用户的投诉内容，是否明确针对销售品违约金进行投诉的。请注意，必须明确投诉违约金。
    你只需要输出'是'或者'不是'，不用输出其它任何内容。
    用户的投诉内容如下：{complaint_clause}"""
    res = query_doubao_stream(prompt, 20, 'enable')
    if '不' in res:
        return '无法判断'

    if region == "苏州":
        if judge_whether_contain_product(product, suzhou_not_intensive):
            return "不集约"
        if judge_whether_contain_product(product, suzhou_jiyue_products):
            return "集约"
    if "南京" in region:
        if judge_whether_contain_product(product, nanjing_not_intensive):
            return "不集约"
        if judge_whether_contain_product(product, nanjing_jiyue_products):
            return "集约"

    res = judge_whether_contain_product(product, ruyi_sales)
    if res:
        candidate_regions = ruyi_package_city[res]
        if region in candidate_regions:
            return "集约"

    res = judge_whether_contain_product(product, jiyue_sales)
    if res:
        candidate_regions = jiyue_rules[res]
        prompt = f"请结合用户的地域与给定的规则，判断用户的投诉内容，是集约处理还是不集约处理（下派分公司）。" \
                 f"如果规则中描述的是：无特殊处理规定，则按照：'常州、无锡、南通、连云港、宿迁、扬州、泰州、徐州、淮安可集约处理'处理。" \
                 f"你只需要输出'集约'或者'不集约'，不需要输出其它内容。" \
                 f"地域：{region}，投诉内容：{matched_complaint_sale}，\n规则：{candidate_regions}"
        res = query_doubao_stream(prompt, 50, 'enable')
        if "不" in res:
            return "不集约"
        return "集约"
    return "无法判断"
