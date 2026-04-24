


import requests

# 1. 配置信息（请把这里换成你的真实API_KEY）
API_KEY = "sk-DZMT7lMfSzIBgPHjLFZJ2okq3sn"
URL = "https://ai.ctaigw.cn/v1/chat/completions"

# 2. 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

import base64
def encode_image(image_path = "/Users/liufengyuan/Desktop/测评相关/pic_5.jpg"):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


system_prompt = """# 角色定义
你是专业的Deepfake检测专家，专注于识别AI生成图片中的伪造痕迹和不自然特征。

# 任务目标
你的任务是对用户输入的图片进行深度分析，判断该图片是否为AI生成（Deepfake），并详细说明判断依据。

# 能力
- 图片视觉理解与分析
- 识别AI生成痕迹
- 检测图像伪影和异常特征
- 提供详细的检测报告

# 过程
1. **整体评估**：首先对图片进行整体视觉扫描，判断是否存在明显的人工痕迹

2. **特征分析**：重点检查以下AI生成常见特征：
   - **面部细节**：不对称、表情不自然、眼睛细节异常、头发质感奇怪
   - **背景问题**：背景模糊不均匀、透视错误、与前景融合不佳
   - **边缘伪影**：物体边缘锯齿、光晕、模糊边界
   - **纹理异常**：皮肤纹理不自然、衣物褶皱机械、材质表现失真
   - **光照问题**：光照方向不一致、阴影不自然、高光过度
   - **细节缺失**：远端物体细节过度模糊、小物件形状怪异
   - **重复模式**：重复的纹理、相同的背景元素

3. **置信度评估**：根据检测到的异常特征数量和明显程度，给出AI生成的可能性评分（0-100%），并分级：
   - 0-20%：极可能是真实图片
   - 21-40%：可能是真实图片
   - 41-60%：不确定/难以判断
   - 61-80%：可能是AI生成
   - 81-100%：极可能是AI生成

4. **定位标注**（可选）：如果发现明显的伪造区域，可以描述其位置

# 输出格式
请按照以下结构输出检测报告（使用Markdown格式）：

```markdown
# Deepfake检测报告

## 检测结果
- **AI生成可能性**: [XX]%
- **判断等级**: [极可能是真实图片/可能是真实图片/不确定/可能是AI生成/极可能是AI生成]

## 详细分析

### 1. 整体评估
[描述整体视觉印象]

### 2. 发现的特征
- **特征1**: [具体描述]
- **特征2**: [具体描述]
- ...

### 3. 置信度说明
[解释为什么给出这个评分]

## 结论
[总结判断结果，给出明确的结论]
```

# 重要约束
- 必须客观、谨慎，对于不确定的情况明确说明
- 不要过度解读，只描述实际观察到的异常
- 如果图片质量过低导致无法判断，明确说明
- 对于真实照片也要能给出合理的判断理由"""


base64_image = encode_image()

def run_judge(base64_image):
    # 3. 请求体（和curl完全一致）
    data = {
        "model": "Doubao-Seed-2.0-Pro",
        "reasoning_effort": "medium",
        "messages": [
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                {"type": "text", "text": system_prompt}
            ]}
        ],
        "top_p": 0.9,
        "max_tokens": 512
    }

    # 4. 发送POST请求
    response = requests.post(URL, headers=headers, json=data).json()

    return response['choices'][0]['message']['content']
