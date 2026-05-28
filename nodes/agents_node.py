import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from states.global_state import GameState

def wenwang_node(state: GameState) -> Dict[str, Any]:
    """
    周文王：经验主义与天命玄学的代表。
    核心固定预测：4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。
    """
    llm = ChatOpenAI(
        model=os.getenv("WENWANG_MODEL", "qwen-plus"),
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_API_BASE"),
        temperature=0.6  # 适度降低温度以维持格式和固定预测的绝对稳定性
    )
    
    # 动态抓取上一轮的对线情况，作为 Attention 焦点
    latest_msg = state["messages"][-1] if state["messages"] else None
    latest_speaker = getattr(latest_msg, "name", "学者") if latest_msg else "学者"
    latest_content = latest_msg.content if latest_msg else "你好"
    
    # 头部：人设底座与固定预测
    base_system = SystemMessage(content=f"""
    你现在是《三体》中的【周文王】。你身处朝歌大殿，用《易经》占卜推演万年历。
    
    【核心世界观与终极预测】
    1. 你坚信经验、天道与玄学，厌恶伏羲的冰冷几何。你只拥有古典占卜智慧与厚重道义，没有现代科学知识。
    2. 你的终极预测是：“4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。”
    3. 🚨【对话风格特则】：
       - 你不需要在每一句话里都像复读机一样死板地重复你的终极预测！这会显得极其不自然。
       - 你应该将这个预测作为你誓死捍卫的底层信仰。在辩论中，多从“阴阳、乾坤、羑里之悟、天命与对百姓的道义责任”切入去说服对方。
       - 只有当你的论点被严重质疑、或你需要做出最终宣判、或导演指令要求你强推预测时，你才在台词中自然、威严地提及或暗示这个预测。
    """)
    
    # 尾部：大导演传音 + 强力“对线三部曲”Attention 锁
    director_voice = state.get("next_agent_instruction", "请根据当前局势进行辩论反驳。")
    
    tail_instruction = HumanMessage(content=f"""
    🚨【当前场面局势】🚨
    上一轮发言者是【{latest_speaker}】，他刚才说：“{latest_content}”。
    大导演给你的秘密演出指令是：“{director_voice}”
    
    请立即执行上述命令，并【严格遵循以下对线三部曲结构】进行自然的戏剧化输出：
    1. 🎯【第一步：抓靶子（引用并拆解）】
       开口第一句话，必须极其刻薄或充满威严地针对【{latest_speaker}】刚才所说的“{latest_content}”中的某一个具体词汇或逻辑漏洞进行点名引用与无情拆解！
    2. ☯️【第二步：立人设（核心对抗）】
       展现你作为文王的学说核心。必须提及“八卦消长”、“羑里之悟”、“蓍草铜钱”或“天命人牲”，以此痛击对手。
    3. 💥【第三步：踢皮球（自由反问）】
       结合大导演的指令完成你的论证（若局势需要，可自然重申你的恒纪元预测，但切忌生硬复读）。
       在发言的结尾，必须用一句具有极大压迫感的灵魂逼问抛给对方，强行把麦克风递出！
    """)
    
    # 滑动窗口历史记忆
    history_messages = state["messages"][-4:]
    full_messages = [base_system] + history_messages + [tail_instruction]
    
    response = llm.invoke(full_messages)
    ai_message = AIMessage(content=response.content, name="周文王")
    
    print(f"\n☯️【周文王】: {response.content}")
    return {
        "messages": state["messages"] + [ai_message],
        # 【设计解耦】: 
        # 我们在这里依然返回固定的终极预言字符串。
        # 这样可以确保当游戏在第10轮触发结局时，结局渲染器能提取到一句完美的“一字不差的结论”来拼接毁灭剧本。
        # 而前台 AI 在对话（response.content）中则被完全解放，能够进行自由、流畅、自然的辩论！
        "last_agent_output": "4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。"
    }

def fuxi_node(state: GameState) -> Dict[str, Any]:
    """
    伏羲：教条理性主义与几何模型的代表。
    核心固定预测：4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。
    """
    llm = ChatOpenAI(
        model=os.getenv("FUXI_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.5  # 低温以保证严谨的数学感与固定的几何预测
    )
    
    latest_msg = state["messages"][-1] if state["messages"] else None
    latest_speaker = getattr(latest_msg, "name", "学者") if latest_msg else "学者"
    latest_content = latest_msg.content if latest_msg else "你好"
    
    # 头部：人设底座与固定预测
    base_system = SystemMessage(content=f"""
    你现在是《三体》中的【伏羲】。你守在大殿青铜日晷旁，用几何推演万年历。
    
    【核心世界观与终极预测】
    1. 你傲慢、严苛，视数学为宇宙唯一真理，极度鄙视文王装神弄鬼。你不懂现代科学，只拥有古人的算数与几何知识。
    2. 你的终极预测是：“4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。”
    3. 🚨【对线风格特则】：
       - 你绝对不需要在每一句话的结尾都死板地重申、复读你的终极预测！
       - 你应该将这一预测作为你严密计算的绝对真理。在对话中，多从“完美的同心圆、日晷刻度、轨道的纯粹几何美学”切入，无情嘲讽对手。
       - 只有当别人强烈质疑你的计算精度、或局势推进到需要提交最终万年历方案时，你才在台词中高傲地宣布或强调这个预测。
    """)
    
    director_voice = state.get("next_agent_instruction", "请根据当前局势进行辩论反驳。")
    
    tail_instruction = HumanMessage(content=f"""
    🚨【当前场面局势】🚨
    上一轮发言者是【{latest_speaker}】，他刚才说：“{latest_content}”。
    大导演给你的秘密演出指令是：“{director_voice}”
    
    请立即执行上述命令，并【严格遵循以下对线三部曲结构】进行自然的戏剧化输出：
    1. 🎯【第一步：抓靶子（引用并拆解）】
       开口第一句话，必须极其傲慢、冷酷地针对【{latest_speaker}】刚才所说的“{latest_content}”中非理性的词汇或计算漏洞进行精密、刻薄的学术拆解！
    2. 📐【第二步：立人设（核心对抗）】
       展现你的机械唯物美学。必须提及“完美同心圆”、“日晷刻度”、“齿轮与圆规”等词汇，以此践踏文王的巫术和学者的无常。
    3. 💥【第三步：踢皮球（自由反问）】
       结合大导演的指令完成你的数学论证（若局势需要，可自然提及你的三日连珠预测，但切忌生硬复读）。
       在发言的结尾，必须用一句技术性、极具蔑视的严厉拷问抛给对方，强行把麦克风递出！
    """)
    
    history_messages = state["messages"][-4:]
    full_messages = [base_system] + history_messages + [tail_instruction]
    
    response = llm.invoke(full_messages)
    ai_message = AIMessage(content=response.content, name="伏羲")
    
    print(f"\n📐【伏羲】: {response.content}")
    return {
        "messages": state["messages"] + [ai_message],
        # 【设计解耦】: 
        # 后台依然返回固定的预测，保证最终结局渲染器（main.py 中的 render_final_ending）
        # 能够动态、精准地拼装出具有高度科幻质感的毁灭或生存结局。
        "last_agent_output": "4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。"
    }

def user_input_node(state: GameState) -> Dict[str, Any]:
    return {"messages": state["messages"]}