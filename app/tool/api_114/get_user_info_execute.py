


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