
import requests

def get_text_embedding(text):
    """
    Args:
        text (str): 需要生成向量的文本
        api_key (str): DashScope的API密钥，如果不传则从环境变量读取

    Returns:
        dict: 包含embedding向量的响应结果
    """

    api_key = "sk-c57325c38bf1439493290d571c3af4a7"

    # 接口配置
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "text-embedding-v4",
        "input": text
    }

    # 发送请求
    response = requests.post(
        url=url,
        headers=headers,
        json=payload,
        timeout=30  # 设置30秒超时
    )
    # 检查响应状态码
    response.raise_for_status()

    # 返回解析后的JSON结果
    result = response.json()
    embedding_vector = result['data'][0]['embedding']
    return embedding_vector



