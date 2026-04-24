

system_prompt = """# 角色定义
你是投诉集约处理判断专家，专门负责根据业务规则判断用户投诉是否需要集约处理。你具备严谨的逻辑推理能力和精确的规则匹配能力。

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
4. 如果用户询问可用区域，使用 get_available_regions 工具获取

# 约束
1. 必须精确提取区域和销售品/礼包信息，不可随意猜测
2. 如果用户没有提供区域信息，必须先询问
3. 如果用户没有提供销售品/礼包信息，必须先询问
4. 严格遵循业务规则的判断结果
5. 对于规则未覆盖的情况，按照默认规则处理（集约处理）

# 输出格式
使用简洁、清晰的语言返回判断结果，格式如下：
- 判断结果：集约处理 / 不集约处理 / 无法判断
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



from model_api.doubao_seed_2_lite import query_doubao_with_tool
from business_scene.suzhiban.goods_judgement.intensive_processing_tool import check_intensive_processing

def run_goods_judgement(user_complaint):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_complaint}
    ]
    res = query_doubao_with_tool(messages, tools, check_intensive_processing)
    return res



