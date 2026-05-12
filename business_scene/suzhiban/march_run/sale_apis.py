
import time
import json
import requests

import Levenshtein

session = requests.session()
from business_scene.suzhiban.goods_judgement.goods_judgement import run_goods_judgement

def find_closest_string(target: str, string_dict: dict) -> str:
    """
    调库计算列文斯顿距离，返回最接近的字符串
    """
    string_list = string_dict.keys()
    # 按距离从小到大排序，取第一个
    return min(string_list, key=lambda s: Levenshtein.distance(target, s))


def get_sale(accNum: str, regionId: str, prodId: str) -> dict:
    accNum = str(accNum)
    regionId = str(regionId)
    prodId = str(prodId)
    url = "http://jsjteop.telecomjs.com:8764/jseop/crm_saop/js_xw_ry_penaltyTrialForExoSystem"
    headers = {
        "X-APP-ID": "b8c2e5dcfe54af717e669739e5790478",
        "X-APP-KEY": "467a04de96967045d75f8d06bec20e8c",
        "appKey": "JS00000001",
        "regionId": regionId,
        "Content-Type": "application/json"
    }
    data = {
        "requestObject": {
            "accNum": accNum,
            "prodId": prodId
        }
    }
    body = ''
    i = 0
    while i < 10:
        i += 1
        try:
            res = session.post(url=url, json=data, headers=headers)
            res.raise_for_status()  # 检查请求是否成功
            body = res.text
        except requests.RequestException as e:
            body = ""
            time.sleep(0.5)
        if body:
            break
    if not body:
        return {}
    res = json.loads(body)['resultObject']['msg']
    if not isinstance(res, dict): #表明不是违约金争议，需要去查渠道
        return {}
    return res


def get_channel_step_1(regionId: str, objId: str) -> dict:
    regionId = str(regionId)
    objId = str(objId)
    regionId = regionId.replace("\n", "").replace(" ", "")
    objId = objId.replace("\n", "").replace(" ", "")
    url = "http://jsjteop.telecomjs.com:8764/jseop/crm_saop/js_xw_ry_qryCustomerOrder"
    headers = {
        "X-APP-ID": "a784f3c54e37e8ac27bb0e85b05bb9cf",
        "X-APP-KEY": "fb3273de7f400db0f495c3c6f093565a",
        "regionId": regionId,
        "appKey": "JS00000087"
    }
    data = {
        "requestObject": {
            "acceptLanId": regionId,
            "objId": objId,
            "pageInfo": {
                "pageIndex": "1",
                "pageSize": "10"
            },
            "scopeInfos": [
                {"scope": "customerOrder"},
                {"scope": "orderItem"},
                {"scope": "ordDevStaffInfo"}],
            "serviceOfferIds": [3010100000, 3020400001,3020200000]
        }
    }

    data = json.dumps(data)
    body = ''
    i = 0
    while i < 10:
        i += 1
        try:
            data = json.dumps(data)
            res = session.get(url=url, data=data, headers=headers, timeout=300)
            body = res.text
        except:
            body = ""
            time.sleep(0.5)
        if body:
            break

    return body


def get_channel_step_2_back(channelId: str):
    channelId = str(channelId)
    url = "http://openapi.telecomjs.com:80/eop/yunque/getChannel/getChannel"
    headers = {
        "X-APP-ID": "3164a47587b94cd69789fdd67092d390",
        "X-APP-KEY": "51b78cb74cf34ba8ab5d5e24e5172174",
        "Content-Type": "application/json"
    }
    data = {
        "channelId": channelId
    }
    try:
        # data = json.dumps(data)
        res = requests.post(url=url,headers=headers,json=data)
        body = res.text
        # body = str(data)
    except Exception as e:
        body = str(e)
    return {"result": body}


def get_channel_step_2(createOrgId):
    # 请求地址
    url = "http://132.254.20.222:30050/v1/chat-messages"

    # 请求头
    headers = {
        "Authorization": "Bearer app-MGP4HWJ7BlonFrqVpEr0R7kX",
        "Content-Type": "application/json"
    }

    # 请求体（和原 curl --data-raw 完全一致）
    data = {
        "input_data": {
            "channelId": str(createOrgId)
        },
        # "channelId": str(createOrgId),
        "query": "1",
        "mode": "blocking",
        "user": "yian"
    }

    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data).text
    response = json.loads(response)
    answer = json.loads(response['answer'])
    return answer


# 销售品匹配
def match_sales(complaint_sale, queried_sales):
    items = queried_sales['chargeItems']
    matched_sales = {}
    for i in items:
        matched_sales[i['objName']] = i['offerInstId']

    matched_sale = find_closest_string(complaint_sale, matched_sales)
    offerInstId = matched_sales[matched_sale]
    return matched_sale, offerInstId

# accNum: prod_num_new
# prodId:

def run_pipeline(complaint_sale, accNum, region, prod_one_desc):
    prodId, regionId = get_sale_info(region, prod_one_desc)
    sales = get_sale(accNum, regionId, prodId)
    if not sales:
        return "无法判断"
    matched_sale, offerInstId = match_sales(complaint_sale, sales)
    return run_goods_judgement(f"投诉销售品：{matched_sale}，用户所属区域：{region}")

    # res_1 = get_channel_step_1(regionId, offerInstId)
    # createOrgId = res_1['resultObject']['customerOrders'][0]['customerOrder']['createOrgId']
    # res = get_channel_step_2(createOrgId)
    # res = json.loads(res)
    # res = res['body']['item']['ecsChannelTypeName']
    # if '地市' in res:
    #     return '不下派'
    # return '下派'



def get_channel_step_2(createOrgId):
    # 请求地址
    url = "http://132.254.20.222:30050/v1/chat-messages"

    # 请求头
    headers = {
        "Authorization": "Bearer app-MGP4HWJ7BlonFrqVpEr0R7kX",
        "Content-Type": "application/json"
    }

    data = {
        "input_data": {
            "channelId": str(createOrgId)
        },
        # "channelId": str(createOrgId),
        "query": "1",
        "mode": "blocking",
        "user": "yian"
    }

    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data).text
    response = json.loads(response)
    answer = json.loads(response['answer'])
    return answer





RES_JSON = {
    "手机":"100000379",
    "普通电话":"100000002",
    "宽带":"100000009",
    "翼支付": "200001144",
    "智慧家庭": "100001090",
    "天翼高清 ":"100001037"
}

city_region_map = {
    "南京市": 8320100,
    "无锡": 8320200,
    "镇江": 8321100,
    "苏州": 8320500,
    "南通": 8320600,
    "扬州": 8321000,
    "盐城": 8320900,
    "徐州": 8320300,
    "淮安": 8320800,
    "连云港": 8320700,
    "常州": 8320400,
    "泰州": 8321200,
    "宿迁": 8321300,
    "其他": 8320000
}


def get_sale_info(region, prod_one_desc):
    return RES_JSON[prod_one_desc], city_region_map[region]


