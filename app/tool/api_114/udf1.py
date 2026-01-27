
"""
第一个api：根据用户信息查询所有相关出票信息
第二个api：查询单次出票详情信息
第三个api：查询单次出票支付信息
"""

"""
话务员会根据用户提供的电影名字和支付时间信息来进一步确认

我理解查询先根据用户的额外信息来查询，然后如果查询记录多于一条或者没查到的话需要和用户再问一遍，
如果还是一样的结果就只能转人工了

先确认是否为用户的电话。如果不是让用户澄清。电话号码不允许模糊。

用户可能有多个电影，或者给到对应的电影观影时间，可能存在模糊，需要跟用户进行确认，哪个是用户想要的。


"""

"get"
url1 = "https://movmgr.js118114.com/bapi/c/order?action=query&limit=10&offset=0&terms={}"

def get_user_films(phone_number, ):
  return [
    {
    "orderId": "60120105817458159",
    "cinemaName": "中影模范电影城",
    "filmName": "飞行家",
    "startDate": "2026-01-13 00:00:00",
    "endDate": "2026-01-20 23:59:59",

  }
  ]




"get"
url2 = "https://movmgr.js118114.com/bapi/c/order?action=detail&orderId={}"

orderId = "60120105817458159"

def get_film_detail(order_id):
  return {}




"post"
url3 = "https://movmgr.js118114.com/bapi/c/order?action=queryPay"


orderId = "60120105817458159"

def get_film_pay_info(phone_number):
  return [
      {
        "payId": 513107,
        "orderId": "60120094312991367",
        "amount": 3500,
        "payType": 12,
        "payTypeName": "院线通-通券",
        "credit": "78405299220198520",
        "payTime": "2026-01-20 09:44:25",
        "operation": 1,
        "allowRefundTag": "",
        "refundCommissionInfo": "",
        "canRefund": ""
      },
      {
        "payId": 513108,
        "orderId": "60120094312991367",
        "amount": 3500,
        "payType": 12,
        "payTypeName": "院线通-通券",
        "credit": "87703939540176621",
        "payTime": "2026-01-20 09:44:25",
        "operation": 1,
        "allowRefundTag": "",
        "refundCommissionInfo": "",
        "canRefund": ""
      }
    ]


{
  "orderId": "60120105817458159",
  "cinemaName": "中影模范电影城",
  "filmName": "飞行家",
  "province": 320000,
  "city": 320100,
  "county": 320104,
  "state": 6,
  "startDate": "2026-01-13 00:00:00",
  "endDate": "2026-01-20 23:59:59",
  "agentId": 2,
  "user": "18154311079",
  "mobile": "18154311079"
}