

import json
import requests

def markdown_json_to_dict(markdown_str):
    """
    将带 ```json 标记的字符串 转换为 Python 字典
    """
    # 1. 去掉前后的 markdown 代码块标记（```json 和 ```）
    json_str = markdown_str.strip().removeprefix('```json').removesuffix('```').strip()

    # 2. 将纯 JSON 字符串转为字典
    result_dict = json.loads(json_str)

    return result_dict




import json
import requests
url = "https://jp9tdzt3yz.coze.site/stream_run"
headers = {
  "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImYwNDRkMmQxLTQxOGMtNGJiNi1iMGRmLWJhYTFjMGVkMWUxYyJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbInJPa2FnZjV6ejZXVWdNMUZheERjYjB1b0RLV0tiQ09NIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzc1NTM4NzQxLCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjI1NTQzMzk3NTA3NjYxODUxIiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjI1ODgwODI3MTA0MDY3NjI2In0.ETgbW-jrEfbw6HYbv1P9X707GVClUar_HQiTnp56NAPLiUFDRv2vnXlMaJxaGEXobfBwv2vCmNBaSCPkUONSzWJ7dQNkhsJoTtLv6qrS0JK7IkLQMZkRFmtmXLdl-7h5ghvsVXU5GOz4XCLCs4xBX05Kx50K1ryhkaRUR_HKyjrWZ5bSmhwgg1l0OR04bYKVFKPPD6l4mjLuZI4N3CtG9_406Cy4grFI10UjUff6U6DUKgHVWys9mGBUWI6mP2rm3qlgbxkDi8QDdVuT8-EeZo9aSqYldw1CEODs1-BtF6PZZhghH7_ppllqgLme_4jTpakSjZ5wJNs_hazyLJ-lVQ",
  "Content-Type": "application/json",
  "Accept": "text/event-stream",
}

def run(user_prompt):
    payload = {
      "content": {
        "query": {
          "prompt": [
            {
              "type": "text",
              "content": {
                "text": user_prompt
              }
            }
          ]
        }
      },
      "type": "query",
        # "session_id": "JIFUGxcOUK29SWzsc9Mvl",
        "project_id": "7625537204907163694"
    }
    response = requests.post(url, headers=headers, json=payload, stream=True)
    result = ""
    for line in response.iter_lines(decode_unicode=True):
      if line and line.startswith("data:"):
          data_text = line[5:].strip()
          parsed = json.loads(data_text)['content']['answer']
          if isinstance(parsed, str):
              result += parsed
    return result




