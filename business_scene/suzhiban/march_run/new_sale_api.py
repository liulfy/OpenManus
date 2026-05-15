


import json
import requests
session = requests.session()

def sale_name(arg1: str,offId:str) -> dict:

    finall_offerInstId = "未查询销售品实例信息"
    sales_name = "未查询销售品名称"
    deatial_info = []
    try:
        try:
            res = json.loads(arg1)["resultObject"]
        except Exception as e:
            res = {}
        if "pkgs" in res.keys() and len(res["pkgs"])>0:
            ##pkgs 相关信息获取
            for item in res["pkgs"]:
                if "offerId" in item.keys():
                    offerId_1 = item["offerId"]
                    offerInstId = item["offerInstId"]
                    BUFFER_sales_name = item["pkgName"]
                    statusCd = item["statusCd"]
                    deatial_info.append({
                    "offerId": offerId_1,
                    "offerInstId": offerInstId,
                    "offerName":BUFFER_sales_name,
                    "statusCd": statusCd,
                    "nameType": "LB",
                })
                    if str(offerId_1) == str(offId):
                        finall_offerInstId = offerInstId
                        sales_name = BUFFER_sales_name
                        break
                if "pkgItemGrps" in item.keys() and len(item["pkgItemGrps"])>0:
                    buffer_res_lst = item["pkgItemGrps"]
                    for subitem in buffer_res_lst:
                        for thirdinfo in subitem["pkgItems"]:
                            offerId_2 = thirdinfo["goods"]["offerId"]
                            BUFFER_sales_name = thirdinfo["goods"]["goodsName"]
                            offerInstId = thirdinfo["offerInstId"]
                            statusCd = thirdinfo["goods"]["statusCd"]
                            deatial_info.append({
                            "offerId": offerId_2,
                            "offerInstId": offerInstId,
                            "offerName":BUFFER_sales_name,
                            "nameType": "SP",
                            "statusCd":statusCd,

                        })
                            if str(offerId_2) == str(offId):
                                finall_offerInstId = offerInstId
                                sales_name = BUFFER_sales_name
                                break
        if "smallPkgs" in res.keys() and len(res["smallPkgs"])>0:
            ##pkgs 相关信息获取
            for item in res["smallPkgs"]:
                if "offerId" in item.keys():
                    offerId_1 = item["offerId"]
                    BUFFER_sales_name = item["pkgName"]
                    offerInstId = item["offerInstId"]
                    statusCd = item["statusCd"]
                    deatial_info.append({
                    "offerId": offerId_1,
                    "offerInstId": offerInstId,
                    "offerName":BUFFER_sales_name,
                    "nameType": "LB",
                    "statusCd":statusCd
                })
                    if str(offerId_1) == str(offId):
                        finall_offerInstId = offerInstId
                        sales_name = BUFFER_sales_name
                        break
                if "pkgItemGrps" in item.keys() and len(item["pkgItemGrps"])>0:
                    buffer_res_lst = item["pkgItemGrps"]
                    for subitem in buffer_res_lst:
                        for thirdinfo in subitem["pkgItems"]:
                            offerId_2 = thirdinfo["goods"]["offerId"]
                            BUFFER_sales_name = thirdinfo["goods"]["goodsName"]
                            offerInstId = thirdinfo["offerInstId"]
                            statusCd = thirdinfo["goods"]["statusCd"]
                            deatial_info.append({
                            "offerId": offerId_2,
                            "offerInstId": offerInstId,
                            "offerName":BUFFER_sales_name,
                            "nameType": "SP",
                            "statusCd": statusCd
                        })
                            if str(offerId_2) == str(offId):
                                finall_offerInstId = offerInstId
                                sales_name = BUFFER_sales_name
                                break

        if "singleGoods" in res.keys() and len(res["singleGoods"])>0:
            for item in res["singleGoods"]:
                if "offerId" in item.keys():
                    offerId_1 = item["offerId"]
                    BUFFER_sales_name =item["goodsName"]
                    offerInstId = item["goodsInstId"]
                    statusCd = item["statusCd"]
                    deatial_info.append({
                    "offerId": offerId_1,
                    "offerInstId": offerInstId,
                    "offerName":BUFFER_sales_name,
                    "nameType": "SP",
                    "statusCd":statusCd
                })
                    if str(offerId_1) == str(offId):
                        finall_offerInstId = offerInstId
                        sales_name = BUFFER_sales_name
                        break

    except Exception as e:
        print(str(e))
        pass

    return {
        "finall_offerInstId":str(finall_offerInstId),
        "sales_name":sales_name,
        "deatial_info":deatial_info
    }

def get_sales_new(accNum:str,regionId:str,pro_id:str,offerId = ''):
    accNum = str(accNum)
    regionId = str(regionId)
    pro_id = str(pro_id)
    url = "http://jsjteop.telecomjs.com:8764/jseop/crm_saop/js_xw_ry_qryPkgAndGoods"
    headers = {
        "X-APP-ID": "a784f3c54e37e8ac27bb0e85b05bb9cf",
        "X-APP-KEY": "fb3273de7f400db0f495c3c6f093565a",
        "regionId":regionId,
        "appKey":"JS00000087"
    }
    data = {
        "requestObject": {
        "accNum": accNum,
        "prodId": pro_id,
        "type": 2
        }
    }
    i = 0
    while i<10:
        i +=1
        try:
            data = json.dumps(data)
            res = session.get(url=url, data=data,headers=headers,timeout=300)
            body = res.text
        except Exception as e:
            body = ""
        if body:
            break
    res = sale_name(body,offerId)
    try:
        deatial_info = res["deatial_info"][0:30]
    except:
        deatial_info = []

    sales = []
    inst_ids = []

    for deatial in deatial_info:
        sales.append(deatial['offerName'])
        inst_ids.append(deatial['offerInstId'])
    return [sales, inst_ids]




