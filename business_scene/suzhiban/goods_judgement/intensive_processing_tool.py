"""
投诉集约处理规则解析工具
根据用户所在区域和投诉的销售品/礼包，判断是否需要集约处理
"""


from typing import Optional, Tuple

import pandas as pd
# 规则文件路径
RULES_FILE = "business_scene/suzhiban/goods_judgement/rules.xls"


def _load_rules() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    加载规则文件
    返回四个工作表的数据
    """
    try:
        # 读取 Excel 文件的所有工作表
        excel_data = pd.read_excel(RULES_FILE, sheet_name=None)

        # 提取各个工作表
        df_sales = excel_data.get('集约销售品', pd.DataFrame())
        df_gifts = excel_data.get('集约如意商品与礼包', pd.DataFrame())

        # 南京苏州特殊表需要特殊处理（跳过第一行header，使用第二行作为列名）
        df_nj_suzhou_yes = pd.read_excel(RULES_FILE, sheet_name='南京苏州可集约处理', header=1)
        df_nj_suzhou_no = pd.read_excel(RULES_FILE, sheet_name='南京苏州不集约销售品与礼包', header=1)

        return df_sales, df_gifts, df_nj_suzhou_yes, df_nj_suzhou_no
    except Exception as e:
        # 如果文件不存在，返回空的数据框
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def _normalize_product_name(name: str) -> str:
    """
    标准化销售品/礼包名称，去除多余空格
    """
    if pd.isna(name) or not isinstance(name, str):
        return ""
    return name.strip()


def _check_sales_product(df_sales: pd.DataFrame, region: str, product_name: str) -> Optional[str]:
    """
    检查销售品是否集约处理
    返回处理结果说明或None（未找到）
    """
    # 标准化查询条件
    query_product = _normalize_product_name(product_name)

    # 在"涉及销售品"列中查找
    for idx, row in df_sales.iterrows():
        sales_name = _normalize_product_name(row.get('涉及销售品', ''))
        if not sales_name or pd.isna(sales_name):
            continue

        # 精确匹配或包含匹配
        if query_product == sales_name or query_product in sales_name or sales_name in query_product:
            # 检查处理范围
            range_100 = _normalize_product_name(row.get('100元（含100元)处理范围', ''))
            range_over_100 = _normalize_product_name(row.get('超过100元处理范围', ''))

            # 检查是否包含该区域
            if region in range_100 or region in range_over_100:
                return f"集约处理（销售品：{sales_name}，在{region}的处理范围内）"
            else:
                return f"不集约处理（销售品：{sales_name}，不在{region}的处理范围内）"

    return None


def _check_gift_product(df_gifts: pd.DataFrame, region: str, product_name: str) -> Optional[str]:
    """
    检查礼包是否集约处理
    返回处理结果说明或None（未找到）
    """
    # 标准化查询条件
    query_product = _normalize_product_name(product_name)

    # 在"涉及礼包"列中查找
    for idx, row in df_gifts.iterrows():
        gift_name = _normalize_product_name(row.get('涉及礼包', ''))
        if not gift_name or pd.isna(gift_name):
            continue

        # 精确匹配或包含匹配
        if query_product == gift_name or query_product in gift_name or gift_name in query_product:
            # 检查可处理地市范围
            scope = _normalize_product_name(row.get('可处理地市范围', ''))

            # 检查是否包含该区域
            if region in scope:
                return f"集约处理（礼包：{gift_name}，在{region}的处理范围内）"
            else:
                return f"不集约处理（礼包：{gift_name}，不在{region}的处理范围内）"

    return None


def _check_nj_suzhou_special(df_nj_suzhou_yes: pd.DataFrame, df_nj_suzhou_no: pd.DataFrame,
                            region: str, product_name: str) -> Optional[str]:
    """
    检查南京苏州特殊规则
    返回处理结果说明或None（未找到）
    """
    # 只处理南京和苏州
    if region not in ['南京', '苏州']:
        return None

    query_product = _normalize_product_name(product_name)

    # 根据区域确定列名
    if region == '南京':
        # 南京的数据在"涉及销售品/礼包"列
        column_name = '涉及销售品/礼包'
    else:  # 苏州
        # 苏州的数据在"涉及销售品"列
        column_name = '涉及销售品'

    # 先检查"不集约"列表（优先级更高）
    for idx, row in df_nj_suzhou_no.iterrows():
        product = _normalize_product_name(row.get(column_name, ''))
        if not product or pd.isna(product):
            continue

        if query_product == product or query_product in product or product in query_product:
            return f"不集约处理（销售品/礼包：{product}，在{region}不集约处理列表中）"

    # 检查可集约列表
    for idx, row in df_nj_suzhou_yes.iterrows():
        product = _normalize_product_name(row.get(column_name, ''))
        if not product or pd.isna(product):
            continue

        if query_product == product or query_product in product or product in query_product:
            return f"集约处理（销售品/礼包：{product}，在{region}可集约处理列表中）"

    return None


def check_intensive_processing(region: str, product_name: str) -> str:
    """
    判断投诉是否需要集约处理

    根据用户所在区域和投诉的销售品/礼包，判断该投诉是否集约处理。
    如果销售品/礼包不在业务规则中，返回集约处理。

    Args:
        region: 用户所在区域（如：无锡、镇江、南京、苏州等）
        product_name: 投诉的销售品/礼包名称

    Returns:
        判断结果说明，包含是否集约处理及相关依据
    """

    # 标准化输入
    region = region.strip()
    product_name = product_name.strip()
    if not product_name:
        return "无法判断"

    # 加载规则
    df_sales, df_gifts, df_nj_suzhou_yes, df_nj_suzhou_no = _load_rules()

    # 1. 优先检查南京苏州特殊规则
    result = _check_nj_suzhou_special(df_nj_suzhou_yes, df_nj_suzhou_no, region, product_name)
    if result:
        return result

    # 2. 检查销售品和礼包，优先返回集约处理的结果
    sales_result = _check_sales_product(df_sales, region, product_name)
    gift_result = _check_gift_product(df_gifts, region, product_name)

    # 如果任何一个结果是集约处理，优先返回集约处理
    if sales_result and "集约处理" in sales_result:
        return sales_result
    if gift_result and "集约处理" in gift_result:
        return gift_result

    # 如果有结果但都是不集约处理，返回其中一个
    if sales_result:
        return sales_result
    if gift_result:
        return gift_result

    # 3. 未找到规则，默认集约处理
    return f"集约处理（销售品/礼包：{product_name}，未在业务规则中找到，按默认规则集约处理）"


def get_available_regions() -> str:
    """
    获取所有可用的区域列表

    Returns:
        所有支持的区域名称列表
    """

    df_sales, df_gifts, df_nj_suzhou_yes, df_nj_suzhou_no = _load_rules()

    regions = set()

    # 从销售品规则中提取区域
    for col in ['100元（含100元)处理范围', '超过100元处理范围']:
        for value in df_sales[col].dropna():
            if value and isinstance(value, str):
                # 提取城市名称（简单的逗号和句号分割）
                cities = [r.strip() for r in value.replace('、', '，').replace('。', '').replace('.', '').split('，') if r.strip()]
                regions.update(cities)

    # 从礼包规则中提取区域
    for value in df_gifts['可处理地市范围'].dropna():
        if value and isinstance(value, str):
            cities = [r.strip() for r in value.replace('、', '，').replace('。', '').replace('.', '').split('，') if r.strip()]
            regions.update(cities)

    # 添加南京和苏州
    regions.add('南京')
    regions.add('苏州')

    # 清理无效区域
    valid_regions = sorted([r for r in regions if r and not r.startswith('可') and len(r) > 0])

    return f"可用区域：{', '.join(valid_regions)}"
