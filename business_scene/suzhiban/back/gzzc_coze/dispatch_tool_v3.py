"""
投诉下派判定工具 v4.8
最终优化版 - 精准平衡
"""

import json
import re
from langchain.tools import tool



def get_text_content(content):
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        if content and isinstance(content[0], str):
            return " ".join(content)
        else:
            return " ".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text")
    return str(content)


def apply_rule_based_prediction(region: str, category: str, content: str) -> dict:
    """基于规则引擎的预测 v4.8"""
    text = str(content) if content else ''

    # ============================================================
    # 明确不下派
    # ============================================================

    if category == '达量降速规则争议':
        return {
            'prediction': '不下派',
            'confidence': '高',
            'prob': 0.92,
            'reason': '达量降速规则省级可解释',
            'needs_llm': False
        }

    if category == '业务/优惠抵扣次序':
        return {
            'prediction': '不下派',
            'confidence': '高',
            'prob': 0.90,
            'reason': '抵扣次序省级可处理',
            'needs_llm': False
        }

    if category == '下线业务无法变更或恢复':
        if any(kw in text for kw in ['一号双终端', 'eSIM']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '一号双终端系统优化中',
                'needs_llm': False
            }
        return {
            'prediction': '下派',
            'confidence': '高',
            'prob': 0.90,
            'reason': '下线业务需地市核实',
            'needs_llm': False
        }

    # 停复机规则
    if category == '停复机规则不认可':
        if '180044' in text or '骚扰' in text:
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '骚扰单停申诉省级可处理',
                'needs_llm': False
            }
        if '180015' in text or ('保护性' in text and '直接' in text):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '风险单停需地市核实',
                'needs_llm': False
            }
        if any(kw in text for kw in ['直接复机', '立即复机', '紧急复机']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '复机诉求需地市处理',
                'needs_llm': False
            }
        if '业务退订' in text or '退订' in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '退订需地市办理',
                'needs_llm': False
            }
        return {
            'prediction': '下派',
            'confidence': '中',
            'prob': 0.70,
            'reason': '停复机问题需地市核实',
            'needs_llm': False
        }

    # 实名制
    if category == '实名制/一证五号办理规则':
        if any(kw in text for kw in ['实名补登记', '补签', '实名认证', '实名登记']):
            # 不方便去营业厅 -> 不下派
            if '不方便' in text or '不便' in text:
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '实名办理省级可协调',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '实名登记需地市办理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['取消', '固话', '销户', '注销']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '业务办理需地市处理',
                'needs_llm': False
            }
        return {
            'prediction': '不下派',
            'confidence': '中',
            'prob': 0.75,
            'reason': '实名规则省级可解释',
            'needs_llm': False
        }

    # ============================================================
    # 营销活动规则争议
    # ============================================================
    if category == '营销活动规则争议':
        if any(kw in text for kw in ['无法领取', '没到账', '未收到', '没有收到', '未到账']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '营销问题省级可处理',
                'needs_llm': False
            }
        if '宽带' in text:
            if '邻居' in text and ('核实' in text or '办理' in text):
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '规则咨询省级可处理',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '宽带业务需地市处理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['机顶盒', 'ITV', 'iptv', '高清', '标清']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '设备问题需地市处理',
                'needs_llm': False
            }
        if '主副卡' in text or ('取消' in text and '主卡' in text):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '主副卡变更需地市处理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['升级套餐', '变更套餐', '要求退订', '取消活动']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '套餐变更需地市处理',
                'needs_llm': False
            }
        if '不认可' in text and any(kw in text for kw in ['收费', '费用', '扣费', '计费']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.80,
                'reason': '费用问题需地市核实',
                'needs_llm': False
            }
        if '核实' in text or '核查' in text:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '核实咨询省级可处理',
                'needs_llm': False
            }
        if '携转' in text or '携出' in text or '携入' in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '携转问题需地市核实',
                'needs_llm': False
            }
        if '不认可' in text:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '规则咨询省级可处理',
                'needs_llm': False
            }
        return {
            'prediction': '无法判断',
            'confidence': '低',
            'prob': 0.50,
            'reason': '信息不足，需人工判定',
            'needs_llm': False
        }

    # ============================================================
    # 业务生效/失效规则争议
    # ============================================================
    if category == '业务生效/失效规则争议':
        if '结转' in text:
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '结转规则省级可解释',
                'needs_llm': False
            }
        if any(kw in text for kw in ['通话清单', '通话记录', '通话详单', '详单']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '通话记录省级可查询',
                'needs_llm': False
            }
        if any(kw in text for kw in ['短期流量包', '流量膨胀包', '流量月包', '不能共享']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '流量包规则省级可解释',
                'needs_llm': False
            }
        if any(kw in text for kw in ['APP', '客户端', '天翼生活']) and any(kw in text for kw in ['不方便', '不会', '操作']):
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': 'APP使用问题省级可处理',
                'needs_llm': False
            }
        if '积分' in text and any(kw in text for kw in ['兑换', '话费', '流量']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '积分问题需地市核实',
                'needs_llm': False
            }
        # 会员/云盘失效 -> 下派
        if any(kw in text for kw in ['会员', '云盘']):
            # 但只是规则咨询 -> 不下派
            if '生效' in text or '失效' in text:
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '会员规则省级可解释',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '会员问题需地市核实',
                'needs_llm': False
            }
        if any(kw in text for kw in ['套餐', '更改', '变更', '降低']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '套餐变更需地市处理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['合约', '协议', '自动续费', '续约', '自动转']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '合约问题需地市核实',
                'needs_llm': False
            }
        if '不认可' in text and any(kw in text for kw in ['收费', '费用', '退费', '退款', '套餐费']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '费用问题需地市核实',
                'needs_llm': False
            }
        if '包年' in text and '自动' in text:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '包年规则省级可解释',
                'needs_llm': False
            }
        if '不认可' in text:
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.70,
                'reason': '不认可问题需地市核实',
                'needs_llm': False
            }
        return {
            'prediction': '无法判断',
            'confidence': '低',
            'prob': 0.50,
            'reason': '信息不足，需人工判定',
            'needs_llm': False
        }

    # ============================================================
    # 省自定2
    # ============================================================
    if category == '省自定2':
        if any(kw in text for kw in ['一号双终端', 'eSIM', '系统优化']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '系统优化中省级可关注',
                'needs_llm': False
            }
        if any(kw in text for kw in ['达量', '降速', '限速']):
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '达量降速规则省级可解释',
                'needs_llm': False
            }
        if '协议期' in text:
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '协议期规则省级可解释',
                'needs_llm': False
            }
        if '结转' in text:
            return {
                'prediction': '不下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '结转规则省级可解释',
                'needs_llm': False
            }
        if any(kw in text for kw in ['携出', '携入', '携号转网', '携转']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.95,
                'reason': '携号转网需地市办理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['移机', '迁移', '装机', '安装']):
            if '资源' in text or '找不到' in text:
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '资源问题省级可关注',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.95,
                'reason': '移机/装机需地市处理',
                'needs_llm': False
            }
        if '宽带' in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.92,
                'reason': '宽带业务需地市处理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['拆机', '销户', '注销']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.95,
                'reason': '拆机/销户需地市处理',
                'needs_llm': False
            }
        if '过户' in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.95,
                'reason': '过户需地市办理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['补卡', '换卡']):
            if any(kw in text for kw in ['状态异常', '无法受理', '系统']):
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '系统问题省级可关注',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.95,
                'reason': '补换卡需地市办理',
                'needs_llm': False
            }
        if any(kw in text for kw in ['恢复', '复装', '复机']):
            if '协议' in text or '限制' in text:
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '规则限制省级可解释',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '恢复业务需地市处理',
                'needs_llm': False
            }
        if '固话' in text:
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '固话业务需地市处理',
                'needs_llm': False
            }
        if '积分' in text and '转' in text:
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '积分转号省级可处理',
                'needs_llm': False
            }
        if '副卡' in text and any(kw in text for kw in ['升级', '变更', '主卡']):
            return {
                'prediction': '下派',
                'confidence': '高',
                'prob': 0.90,
                'reason': '副卡变更需地市处理',
                'needs_llm': False
            }
        if '副卡' in text and not any(kw in text for kw in ['升级', '变更', '主卡', '取消']):
            return {
                'prediction': '不下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '副卡规则省级可解释',
                'needs_llm': False
            }
        if any(kw in text for kw in ['机顶盒', '设备']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '设备问题需地市核实',
                'needs_llm': False
            }
        if any(kw in text for kw in ['退费', '退款', '减免']):
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.75,
                'reason': '退费问题需地市核实',
                'needs_llm': False
            }
        if '积分' in text:
            # 不会操作 -> 不下派
            if '不会' in text or '无法' in text:
                return {
                    'prediction': '不下派',
                    'confidence': '中',
                    'prob': 0.75,
                    'reason': '操作问题省级可指导',
                    'needs_llm': False
                }
            return {
                'prediction': '下派',
                'confidence': '中',
                'prob': 0.70,
                'reason': '积分问题需地市核实',
                'needs_llm': False
            }
        return {
            'prediction': '无法判断',
            'confidence': '低',
            'prob': 0.50,
            'reason': '信息不足，需人工判定',
            'needs_llm': False
        }

    return {
        'prediction': '无法判断',
        'confidence': '低',
        'prob': 0.50,
        'reason': '信息不足，需人工判定',
        'needs_llm': False
    }

from model_api.doubao_seed_2_lite import query_doubao_with_msgs

def call_llm_judgment(region: str, category: str, content: str) -> dict:
    """调用LLM进行判定"""

    system_prompt = """你是电信投诉下派判定专家。判断投诉应该【下派】还是【不下派】。

## 下派原则（需地市处理）
- 业务办理：过户、携号转网、拆机、移机、宽带安装、套餐变更、补卡换卡等
- 业务变更：变更套餐、取消宽带、主副卡变更等
- 费用核查：用户对实际收费有异议需核查
- 设备退费：机顶盒等设备退费
- 携转后退费问题

## 不下派原则（省级可处理）
- 规则咨询：达量降速、协议期、结转规则、流量包不能共享等
- 系统优化中：一号双终端/eSIM系统优化
- 骚扰单停申诉（180044类型）
- 通话清单/通话记录查询
- APP使用不便
- 规则限制问题
- 中风险双停场景（不包括中风险单停场景）

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


@tool
def dispatch_judgment(region: str, category: str, content: str) -> str:
    """投诉下派判定工具 v4.8"""
    rule_result = apply_rule_based_prediction(region, category, content)

    pred = rule_result['prediction']
    method = '规则引擎'

    if pred == '无法判断':
        llm_result = call_llm_judgment(region, category, content)
        if llm_result['prediction'] != '无法判断':
            pred = llm_result['prediction']
            rule_result['reason'] = llm_result['reason']
            rule_result['confidence'] = llm_result['confidence']
            method = 'LLM'
    
    return json.dumps({
        '判定': pred,
        '理由': rule_result['reason'],
        '置信度': rule_result['confidence'],
        '判定方式': method,
        '概率': round(rule_result['prob'], 2)
    }, ensure_ascii=False)
