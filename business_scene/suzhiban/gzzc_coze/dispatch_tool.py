"""
投诉下派判定工具 v2.1
基于类别先验和关键词组合的优化版本

核心策略：
1. 类别先验概率作为基础
2. 关键词组合决定最终判断
3. 矛盾关键词优先不下派
4. 控制"无法判断"占比≤30%
"""
import json
import re



# ============================================================
# 类别基础概率（基于数据分析）
# ============================================================
CATEGORY_BASE_PROB = {
    # 下派倾向高
    '实名制/一证五号办理规则': 0.65,  # 下派率约65%
    '停复机规则不认可': 0.60,
    '下线业务无法变更或恢复': 0.55,
    '业务生效/失效规则争议': 0.55,
    # 下派倾向低
    '省自定2': 0.45,
    '营销活动规则争议': 0.40,
    '业务/优惠抵扣次序': 0.25,
    '达量降速规则争议': 0.20,
}

# ============================================================
# 下派关键词（业务办理类）
# ============================================================
DISPATCH_KEYWORDS = [
    # 明确业务办理
    '过户', '携号转网', '携入', '携出',
    '拆机', '注销', '销户', '销号',
    '移机', '迁移', '装机', '安装',
    '宽带新装', '宽带安装', '宽带移机',
    # 业务变更
    '变更套餐', '更改套餐', '升级', '降级',
    '复机', '恢复开机', '重新开通',
    '新增副卡', '新增号码', '加装副卡',
]

# ============================================================
# 不下派关键词（规则咨询类）
# ============================================================
UNDISPATCH_KEYWORDS = [
    # 达量/限速
    '达量降速', '降速规则', '达量限速',
    # 抵扣/账单
    '抵扣次序', '流量抵扣', '账单', '余额',
    # 活动规则
    '活动规则', '活动条件', '活动参加', '活动参与',
    '翼支付', '返费', '返话费',
    # 会员权益
    '会员', '权益', '随心选', '积分',
    # 取消退订
    '取消活动', '退订', '取消合约',
    # 不认可类
    '不认可', '解释无效', '不同意', '不满意',
    # 一证五号
    '一证五号', '实名查询',
]


def get_text_content(content):
    """安全获取文本内容"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        if content and isinstance(content[0], str):
            return " ".join(content)
        else:
            return " ".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text")
    return str(content)


def count_keywords(text: str) -> dict:
    """统计关键词匹配"""
    dispatch_count = sum(1 for kw in DISPATCH_KEYWORDS if kw in text)
    undispatch_count = sum(1 for kw in UNDISPATCH_KEYWORDS if kw in text)
    
    # 单独检查"宽带"
    has_broadband = '宽带' in text
    # 单独检查"复机"
    has_reactivate = '复机' in text
    # 单独检查"活动"
    has_activity = '活动' in text
    
    return {
        'dispatch_count': dispatch_count,
        'undispatch_count': undispatch_count,
        'has_broadband': has_broadband,
        'has_reactivate': has_reactivate,
        'has_activity': has_activity,
    }


def apply_rule_based_prediction(region: str, category: str, content: str) -> dict:
    """
    基于规则引擎的预测 v2.1
    
    策略：
    1. 强下派/不下派关键词优先
    2. 矛盾时优先不下派
    3. 类别先验调整
    4. 关键词数量差决定倾向
    """
    text = content if content else ""
    kw_count = count_keywords(text)
    
    # 获取类别先验
    base_prob = CATEGORY_BASE_PROB.get(category, 0.50)
    
    # ============================================================
    # 1. 类别强规则
    # ============================================================
    
    # 达量降速规则争议 - 几乎全部不下派
    if category == '达量降速规则争议':
        # 宽带+复机 才是下派
        if kw_count['has_broadband'] and kw_count['has_reactivate']:
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.70,
                'reason': '宽带复机业务，需地市处理',
                'needs_llm': False
            }
        return {
            'prediction': '不下派',
            'confidence': '高',
            'prob': 0.80,
            'reason': '达量降速规则，省级可解释',
            'needs_llm': False
        }
    
    # 业务/优惠抵扣次序 - 全部不下派
    if category == '业务/优惠抵扣次序':
        return {
            'prediction': '不下派',
            'confidence': '高',
            'prob': 0.80,
            'reason': '抵扣次序问题，省级可处理',
            'needs_llm': False
        }
    
    # ============================================================
    # 2. 营销活动规则争议 - 几乎全部不下派
    # ============================================================
    if category == '营销活动规则争议':
        # 只有宽带+新装/移机/装机 才是下派
        if kw_count['has_broadband'] and any(kw in text for kw in ['新装', '移机', '装机', '安装']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.85,
                'reason': '宽带新装业务，需地市处理',
                'needs_llm': False
            }
        # 违约金相关
        if '违约金' in text:
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.65,
                'reason': '违约金争议，需地市核实',
                'needs_llm': False
            }
        # 其他都是不下派
        return {
            'prediction': '不下派',
            'confidence': '高',
            'prob': 0.75,
            'reason': '营销活动规则，省级可处理',
            'needs_llm': False
        }
    
    # ============================================================
    # 3. 实名制/一证五号办理规则
    # ============================================================
    if category == '实名制/一证五号办理规则':
        # 复机/恢复开机是不下派
        if kw_count['has_reactivate']:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.60,
                'reason': '复机问题省级可处理',
                'needs_llm': False
            }
        # 未实名/实名补登记是下派
        if '未实名' in text or '实名补登记' in text or '实名登记' in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.85,
                'reason': '实名登记需地市办理',
                'needs_llm': False
            }
        # 一证五号查询是不下派
        if '一证五号' in text and any(kw in text for kw in ['查询', '限制', '规则']):
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.60,
                'reason': '一证五号规则省级可解释',
                'needs_llm': False
            }
        # 默认下派
        return {
            'prediction': '下派',
            'confidence': '中',
            'prob': 0.60,
            'reason': '实名制业务需地市核实',
            'needs_llm': False
        }
    
    # ============================================================
    # 4. 停复机规则不认可
    # ============================================================
    if category == '停复机规则不认可':
        # 复机申请是下派
        if kw_count['has_reactivate']:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.80,
                'reason': '复机申请需地市处理',
                'needs_llm': False
            }
        # 停机申诉是不下派
        if '申诉' in text:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.60,
                'reason': '停机申诉省级可处理',
                'needs_llm': False
            }
    
    # ============================================================
    # 5. 省自定2 - 需要精细处理
    # ============================================================
    if category == '省自定2':
        # 宽带类下派
        if kw_count['has_broadband']:
            # 宽带+活动/会员/权益 = 不下派
            if kw_count['has_activity'] or any(kw in text for kw in ['会员', '权益']):
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.65,
                    'reason': '宽带会员权益，省级可处理',
                    'needs_llm': False
                }
            # 宽带+新装/移机/装机/安装 = 下派
            if any(kw in text for kw in ['新装', '移机', '装机', '安装']):
                return {
                    'prediction': '下派',
                    'confidence': '高',
                    'prob': 0.85,
                    'reason': '宽带安装业务，需地市处理',
                    'needs_llm': False
                }
            # 只有宽带 = 中等下派
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.65,
                'reason': '涉及宽带业务，需地市核实',
                'needs_llm': False
            }
        
        # 会员/权益类不下派
        if any(kw in text for kw in ['会员', '权益', '随心选']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.70,
                'reason': '会员权益问题，省级可处理',
                'needs_llm': False
            }
        
        # 余额/账单类不下派
        if any(kw in text for kw in ['余额', '账单', '费用']):
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.65,
                'reason': '费用问题，省级可解释',
                'needs_llm': False
            }
        
        # 业务变更类下派
        if any(kw in text for kw in ['变更', '更改', '升级', '降级']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.70,
                'reason': '业务变更需地市核实',
                'needs_llm': False
            }
        
        # 副卡新增下派
        if any(kw in text for kw in ['新增', '副卡', '加入', '并号']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.80,
                'reason': '副卡业务需地市处理',
                'needs_llm': False
            }
    
    # ============================================================
    # 6. 业务生效/失效规则争议
    # ============================================================
    if category == '业务生效/失效规则争议':
        # 宽带类下派
        if kw_count['has_broadband']:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.80,
                'reason': '涉及宽带业务，需地市核实',
                'needs_llm': False
            }
        
        # 业务变更下派
        if any(kw in text for kw in ['变更', '更改', '升级', '降级']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.70,
                'reason': '业务变更需地市核实',
                'needs_llm': False
            }
        
        # 复机下派
        if kw_count['has_reactivate']:
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.70,
                'reason': '复机业务需地市处理',
                'needs_llm': False
            }
        
        # 活动/合约下派
        if any(kw in text for kw in ['活动', '合约', '协议', '违约金']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.65,
                'reason': '活动协议问题，需地市核实',
                'needs_llm': False
            }
    
    # ============================================================
    # 7. 下线业务无法变更或恢复
    # ============================================================
    if category == '下线业务无法变更或恢复':
        # 恢复/变更申请下派
        if any(kw in text for kw in ['恢复', '复开', '变更', '更改']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.65,
                'reason': '下线业务变更需地市核实',
                'needs_llm': False
            }
    
    # ============================================================
    # 8. 通用规则兜底
    # ============================================================
    
    # 强下派关键词
    for kw in ['携号转网', '携入', '携出']:
        if kw in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': f'涉及{kw}业务，需地市办理',
                'needs_llm': False
            }
    
    for kw in ['拆机', '注销', '销户', '销号']:
        if kw in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.85,
                'reason': '涉及拆机/销户，需地市处理',
                'needs_llm': False
            }
    
    for kw in ['移机', '迁移', '装机', '安装']:
        if kw in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.80,
                'reason': '涉及移机/装机业务，需地市处理',
                'needs_llm': False
            }
    
    for kw in ['靓号', '保底', '预占']:
        if kw in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.85,
                'reason': '涉及靓号保底规则，需地市核实',
                'needs_llm': False
            }
    
    # 强不下派关键词
    if '骚扰单停' in text:
        return {
            'prediction': '不下派',
            'confidence': '高',
            'prob': 0.85,
            'reason': '骚扰单停按规则处理，省级可协调',
            'needs_llm': False
        }
    
    # ============================================================
    # 9. 关键词矛盾分析
    # ============================================================
    
    # 矛盾时优先不下派（基于假阳性分析）
    if kw_count['dispatch_count'] > 0 and kw_count['undispatch_count'] > 0:
        # 如果下派关键词和不不下派关键词同时存在，倾向于不下派
        return {
            'prediction': '不下派',
            'confidence': '中',
            'prob': 0.55,
            'reason': '涉及多种因素，倾向于不下派',
            'needs_llm': False
        }
    
    # 单纯不认可类不下派
    if any(kw in text for kw in ['不认可', '解释无效', '不同意']):
        if kw_count['dispatch_count'] <= 1:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.60,
                'reason': '单纯不满投诉，省级可处理',
                'needs_llm': False
            }
    
    # ============================================================
    # 10. 基于概率的最终判断
    # ============================================================
    
    # 调整概率
    prob = base_prob
    
    if kw_count['dispatch_count'] > kw_count['undispatch_count']:
        prob += 0.15 * (kw_count['dispatch_count'] - kw_count['undispatch_count'])
    elif kw_count['undispatch_count'] > kw_count['dispatch_count']:
        prob -= 0.10 * (kw_count['undispatch_count'] - kw_count['dispatch_count'])
    
    prob = max(0.15, min(0.85, prob))
    
    # 边界样本标记为无法判断（控制在30%以内）
    if abs(prob - 0.50) < 0.15:
        return {
            'prediction': '无法判断',
            'confidence': '低',
            'prob': 0.50,
            'reason': '信息不足，需人工判定',
            'needs_llm': False
        }
    
    prediction = '下派' if prob >= 0.50 else '不下派'
    confidence = '高' if abs(prob - 0.50) > 0.20 else '中'
    
    return {
        'prediction': prediction,
        'confidence': confidence,
        'prob': prob,
        'reason': f'根据内容特征，倾向{prediction}',
        'needs_llm': False
    }


from model_api.doubao_seed_2_lite import query_doubao_with_msgs

def call_llm_judgment(region: str, category: str, content: str) -> dict:
    system_prompt = """你是电信投诉下派判定专家。判断投诉应该【下派】还是【不下派】。

## 下派原则（需地市处理）
- 业务办理：过户、携号转网、拆机、移机、宽带安装、复机等
- 业务变更：变更套餐、升级、复机等具体操作
- 需现场核实：设备故障、宽带安装等

## 不下派原则（省级可处理）
- 规则咨询：活动规则、费用规则、套餐规则等咨询
- 政策解释：达量降速、一证五号限制等规则解释
- 会员权益：会员权益使用、随心选等线上可处理

## 关键判断
- 关键词"不认可"、"解释无效"本身不是下派依据
- "宽带+安装/装机/新装" = 下派
- "活动+规则/咨询" = 不下派
- "变更+套餐/业务" = 下派

输出格式：{"判定": "下派"或"不下派", "理由": "一句话", "置信度": "高/中/低"}"""

    user_prompt = f"地域：{region}\n类别：{category}\n内容：{content[:500] if content else '空'}\n判断："

    messages = [
        {
            "content": system_prompt,
            "role": "system"
        },
        {
            "content": user_prompt,
            "role": "user"
        }
    ]

    try:
        content_text = query_doubao_with_msgs(messages)
        json_match = re.search(r'\{[^}]+\}', content_text, re.DOTALL)

        if json_match:
            result = json.loads(json_match.group())
            return {
                'prediction': result.get('判定'),
                'reason': result.get('理由', ''),
                'confidence': result.get('置信度', '中')
            }
    except Exception:
        pass

    return {
        'prediction': '无法判断',
        'reason': 'LLM调用失败',
        'confidence': '低'
    }



# category似乎是二级目录

def dispatch_judgment(region: str, category: str, content: str) -> dict:
    """
    投诉下派判定工具 v2.1
    
    根据用户投诉内容、地域和类别，判断投诉应该【下派】还是【不下派】或【无法判断】。
    优化后控制"无法判断"占比≤30%。
    """
    rule_result = apply_rule_based_prediction(region, category, content)
    
    pred = rule_result['prediction']
    method = '规则引擎'
    
    # 如果是"无法判断"，可尝试LLM
    if pred == '无法判断':
        llm_result = call_llm_judgment(region, category, content)
        if llm_result['prediction'] != '无法判断':
            pred = llm_result['prediction']
            rule_result['reason'] = llm_result['reason']
            rule_result['confidence'] = llm_result['confidence']
            method = 'LLM'
    
    return {
        '判定': pred,
        '理由': rule_result['reason'],
        '置信度': rule_result['confidence'],
        '判定方式': method,
        '概率': round(rule_result['prob'], 2)
    }

system_prompt = """你是投诉下派判定专家，专门根据用户投诉内容和所属地域，判断投诉应该【下派】（分派地市分公司处理）还是【不下派】（省级处理）。

## 判定规则

### 应该【下派】的情况（需要地市处理）：
1. **业务办理类**：需要到现场办理的业务，如过户、携号转网、宽带移机/装机/拆机、安装服务等
2. **核实调查类**：需要核实具体办理情况、调查事实的投诉
3. **涉及地市特定资源**：靓号保底、实名制特殊处理、需地市协调的复杂问题
4. **用户明确要求**：用户明确要求到营业厅办理或需要上门服务

### 应该【不下派】的情况（省级处理）：
1. **费用规则类**：账单查询、套餐费用争议、达量降速规则、流量抵扣次序等可通过解释解决的
2. **政策咨询类**：对规则政策不认可但可通过知识库解释清楚的
3. **线上可处理类**：可以通过线上渠道（10000号、知识库）直接解释处理的
4. **标准规则类**：涉及统一规则、政策的争议

### 判定为【无法判断】的情况：
1. 投诉内容描述模糊，无法确定具体诉求
2. 涉及多种复杂因素，难以明确判定
3. 投诉内容不足以支撑明确判断

## 输出格式

对于每个投诉，你必须输出以下JSON格式的判定结果：

```json
{
 "判定": "下派" 或 "不下派" 或 "无法判断",
 "理由": "简要说明判定依据（1-2句话）",
 "置信度": "高" 或 "中" 或 "低"
}
```

## 判定原则
1. 严格按照规则判定，不要过度解读
2. 判定结果必须是【下派】【不下派】【无法判断】三者之一
3. 理由要简洁、明确
4. 如果投诉内容涉及需要地市核实或现场处理的，优先考虑【下派】"""
