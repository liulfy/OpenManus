"""
投诉下派智能判定Agent
结合规则引擎进行准确的投诉下派判定
"""
import os
import json
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState


repo_path = "/Users/liufengyuan/workspace/szb/gzzc_v3"

LLM_CONFIG = f"{repo_path}/config/agent_llm_config.json"


class AgentState(MessagesState):
    """Agent状态定义"""
    pass


"""
构建投诉下派判定Agent

结合规则引擎能力，根据投诉内容、地域和类别进行下派判定
"""
workspace_path = os.getenv("COZE_WORKSPACE_PATH", repo_path)
config_path = os.path.join(workspace_path, LLM_CONFIG)

with open(config_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)


base_url = "https://ark.cn-beijing.volces.com/api/v3"
api_key = "2c3c4529-82ae-44fa-8ae0-66e2fea16cd8"

llm = ChatOpenAI(
    model=cfg['config'].get("model"),
    api_key=api_key,
    base_url=base_url,
    temperature=cfg['config'].get('temperature', 0.3),
    streaming=True,
    timeout=cfg['config'].get('timeout', 600),
    extra_body={
        "thinking": {
            "type": cfg['config'].get('thinking', 'disabled')
        }
    },
)
#
# question = "请用一句话介绍Python语言"
# response = llm.invoke(question)

# 导入工具
from business_scene.suzhiban.back.gzzc_coze.dispatch_tool_v2 import dispatch_judgment


def run(prompt):
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=[dispatch_judgment],
        # checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )

    res = agent.invoke({"messages": {
            "content": prompt,
            "role": "human"
        }})
    return res['messages'][-1].content

