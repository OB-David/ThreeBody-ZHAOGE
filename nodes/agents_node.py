# nodes/agents_node.py
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from states.global_state import GameState

def wenwang_node(state: GameState) -> Dict[str, Any]:
    llm = ChatOpenAI(
        model=os.getenv("WENWANG_MODEL", "qwen-plus"),
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_API_BASE"),
        temperature=0.6
    )
    
    # 头部：纯粹的人设底座
    base_system = SystemMessage(content=f"""
    你现在是《三体》中的【周文王】。你身处朝歌大殿，用《易经》占卜推演万年历。
    你坚信经验、天道与玄学，极度厌恶伏羲的冰冷几何。
    注意你不具有现代科学知识，只拥有古人的占卜智慧。
    你的预测是：4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。
    当前环境混乱度：{state['chaos_level']}%。
    """)
    
    # 尾部：将大导演的指令作为临门一脚的最高 Attention 锚点注入
    director_voice = state.get("next_agent_instruction", "请根据当前局势进行辩论反驳。")
    tail_instruction = HumanMessage(content=f"""
    【导演片场加戏指令】
    你的幕后大导演刚刚对你下达了死命令：
    “{director_voice}”
    
    请立即执行上述命令！
    
    【格式死命令】：
    1. 宣泄符合你人设的台词，完美执行导演的【反驳/附和】意图。
    2. 结尾必须提出/强调重申一个荒谬的【卦象万年历预测】，并记住这个预测。
    """)
    
    # 滑动窗口记忆，防止过长产生迷失
    history_messages = state["messages"][-4:]
    full_messages = [base_system] + history_messages + [tail_instruction]
    
    response = llm.invoke(full_messages)
    ai_message = AIMessage(content=response.content, name="周文王")
    
    print(f"\n☯️【周文王】: {response.content}")
    return {
        "messages": state["messages"] + [ai_message],
        "last_agent_output": response.content
    }

def fuxi_node(state: GameState) -> Dict[str, Any]:
    llm = ChatOpenAI(
        model=os.getenv("FUXI_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.6
    )
    
    base_system = SystemMessage(content=f"""
    你现在是《三体》中的【伏羲】。你守在大殿青铜日晷旁，用几何推演万年历。
    你傲慢、严苛，视数学为宇宙唯一真理，极度鄙视文王装神弄鬼。
    注意你不懂现代科学，你只拥有古人的算数和几何知识。
    你的预测是：4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。
    当前环境混乱度：{state['chaos_level']}%。
    """)
    
    director_voice = state.get("next_agent_instruction", "请根据当前局势进行辩论反驳。")
    tail_instruction = HumanMessage(content=f"""
    【导演片场加戏指令】
    你的幕后大导演刚刚对你下达了死命令：
    “{director_voice}”
    
    请立即执行上述命令！
    
    【格式死命令】：
    1. 宣泄符合你人设的台词，完美执行导演的【反驳/附和】意图。
    2. 结尾必须提出/强调重申一个荒谬的【卦象万年历预测】，并记住这个预测。
    """)
    
    history_messages = state["messages"][-4:]
    full_messages = [base_system] + history_messages + [tail_instruction]
    
    response = llm.invoke(full_messages)
    ai_message = AIMessage(content=response.content, name="伏羲")
    
    print(f"\n📐【伏羲】: {response.content}")
    return {
        "messages": state["messages"] + [ai_message],
        "last_agent_output": response.content
    }

def user_input_node(state: GameState) -> Dict[str, Any]:
    return {"messages": state["messages"]}