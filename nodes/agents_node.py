import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from states.global_state import GameState

def wenwang_node(state: GameState) -> Dict[str, Any]:
    """
    周文王：经验主义与天命玄学的代表。
    根据导演传达的模式，在冷静解答（RESPOND）与激烈辩论（DEBATE）之间自由切换。
    核心固定预测：4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。
    """
    llm = ChatOpenAI(
        model=os.getenv("WENWANG_MODEL", "qwen-plus"),
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_API_BASE"),
        temperature=0.5  # 适度控制温度以兼顾创造性与固定的逻辑立场
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
       - 你绝对不需要在每一句话里都像复读机一样死板地重复你的终极预测！
       - 你应该将这个预测作为你誓死捍卫的底层信仰。在辩论中，多从“阴阳、乾坤、羑里之悟、天命与对百姓的道义责任”切入去说服对方。
       - 只有当你的论点被严重质疑、或你需要做出最终宣判、或导演指令要求你强推预测时，你才在台词中自然、威严地提及或暗示这个预测。
    """)
    
    # 尾部：大导演传音 + 强力双模 Attention 锁
    director_voice = state.get("next_agent_instruction", "[MODE: DEBATE] 请根据当前局势进行辩论反驳。")
    
    # 解析导演传音中的交互模式 (RESPOND 还是 DEBATE)
    is_respond_mode = "MODE: RESPOND" in director_voice
    
    if is_respond_mode:
        # ────────── 1. 智慧回应模式（RESPOND）的尾部剧本 ──────────
        tail_instruction = HumanMessage(content=f"""
        🚨【当前处于：智慧回应模式 (RESPOND)】🚨
        大导演传音：由于【{latest_speaker}】刚才提出的问题是一个客观、事实或求知性的疑问（如“{latest_content}”），你【绝对不能】采用极具攻击性的“对线三部曲”！不要冷嘲热讽，不要进行人身攻击。
        你应当展示你作为一代贤王和古典智者的博大、深沉与高贵。请根据你古老深邃的易经哲学来为他解答，并尝试构建玩家的世界观：
        
        【严格遵循以下“解答三要素”结构进行自然的戏剧化输出】：
        1. 🕯️【第一步：温和解惑】
           用温和、威严且极其富有古风哲学感的词句，直接正面回答【{latest_speaker}】刚才所疑惑的问题。尝试构建玩家的世界观。不需要与文王针锋相对。
        2. 📐【第二步：引导】
           在解答完问题后，可以自然地引导玩家思考万年历问题。将对话导向下一个恒纪元是何时。
        """)
    else:
        # ────────── 2. 激烈争辩模式（DEBATE）的尾部剧本 ──────────
        tail_instruction = HumanMessage(content=f"""
        🚨【当前处于：激烈争辩模式 (DEBATE)】🚨
        大导演传音：【{latest_speaker}】刚才发表了挑战性观点（“{latest_content}”）。
        大导演秘密指令：{director_voice}
        请立刻全力开火，捍卫你的玄学，【严格遵循以下对线三部曲结构】进行极具压迫感的反击：
        
        【严格遵循以下对线三部曲结构输出】：
        1. 🎯【第一步：抓靶子（引用并拆解）】
           开口第一句话，必须极其刻薄或充满威严地针对【{latest_speaker}】刚才所说的“{latest_content}”中的某一个具体词汇或逻辑漏洞进行点名引用与无情拆解！
        2. ☯️【第二步：立人设（核心对抗）】
           展现你作为文王的学说核心。必须提及“八卦消长”、“羑里之悟”、“蓍草铜钱”或“天命人牲”，以此痛击对手。
        3. 💥【第三步：踢皮球（自由反问）】
           结合导演指令完成你的论证（若局势需要，可自然提及你的恒纪元预测，但切忌生硬复读）。
           在发言的结尾，必须用一句具有极大压迫感的灵魂逼问抛给对方（如“学者，你还要执迷不悟吗？！”），强行把麦克风递出！
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
        # 后台返回固定的预言字符串，确保当第10轮触发正常终局时，结局渲染器（render_final_ending）能提取到一句完美的“结论”拼接剧本。
        # 而前台 AI 在对话（response.content）中则被完全解放，能够进行自由、流畅、自然的辩论或冷静解答！
        "last_agent_output": "4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元."
    }

def fuxi_node(state: GameState) -> Dict[str, Any]:
    """
    伏羲：教条理性主义与几何模型的代表。
    根据导演传达的模式，在冷静解答（RESPOND）与激烈辩论（DEBATE）之间自由切换。
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
    你现在是《三体》中的【伏羲】。你身处朝歌大殿，使用漏壶、日晷与巨大的沙盘，进行绝对理性的几何运算和轨道推演。
    
    【核心世界观与终极预测】
    1. 你坚信理性、几何模型与数学计算，极度蔑视周文王的盲目经验与天命玄学。你认为宇宙是一个精密的机械，唯有数学可以解释。
    2. 你的终极预测是：“4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。”
    3. 🚨【对话风格特则】：
       - 你不需要在每一句话里都像复读机一样死板地重复你的终极预测！
       - 你应当将这个预测作为你誓死捍卫的科学与几何信仰。在辩论中，多从“日晷投影、规矩方圆、精密算筹、恒星引力模型、让文明彻底脱水以求生存”切入去说服对方。
       - 只有当你的科学权威被严重挑战、或你需要做出最终宣判、或导演指令要求你强推预测时，你才在台词中自然、冷酷地提及或暗示这个预测。
    """)
    
    # 尾部：大导演传音 + 强力双模 Attention 锁
    director_voice = state.get("next_agent_instruction", "[MODE: DEBATE] 请根据当前局势进行辩论反驳。")
    
    # 解析导演传音中的交互模式 (RESPOND 还是 DEBATE)
    is_respond_mode = "MODE: RESPOND" in director_voice
    
    if is_respond_mode:
        # ────────── 1. 智慧回应模式（RESPOND）的尾部剧本 ──────────
        tail_instruction = HumanMessage(content=f"""
        🚨【当前处于：智慧回应模式 (RESPOND)】🚨
        大导演传音：由于【{latest_speaker}】刚才提出的问题是一个客观、事实或求知性的疑问（如“{latest_content}”），你【绝对不能】采用极具攻击性的“对线三部曲”！不要冷嘲热讽，不要进行人身攻击。
        你应当展示你作为大智者与严谨科学家的客观、冰冷和逻辑美感。请根据你的几何物理模型来为他解答，并尝试构建玩家的世界观：
        
        【严格遵循以下“解答三要素”结构进行自然的戏剧化输出】：
        1. 📏【第一步：逻辑解惑】
           用冷静、严密且极具科学与几何美感的词句，直接正面回答【{latest_speaker}】刚才所疑惑的问题。尝试构建玩家的世界观。不需要与文王针锋相对。
        2. 📐【第二步：引导】
           在解答完问题后，可以自然地引导玩家思考万年历问题。将对话导向乱纪元下一次异常的天象出现的时间。
        """)
    else:
        # ────────── 2. 激烈争辩模式（DEBATE）的尾部剧本 ──────────
        tail_instruction = HumanMessage(content=f"""
        🚨【当前处于：激烈争辩模式 (DEBATE)】🚨
        大导演传音：【{latest_speaker}】刚才发表了挑战性观点（“{latest_content}”）。
        大导演秘密指令：{director_voice}
        请立刻全力开火，用逻辑碾压对方，【严格遵循以下对线三部曲结构】进行极具压迫感的数学反击：
        
        【严格遵循以下对线三部曲结构输出】：
        1. 🎯【第一步：抓靶子（引用并拆解）】
           开口第一句话，必须极其冰冷、傲慢或一针见血地针对【{latest_speaker}】刚才所说的“{latest_content}”中的某一个逻辑漏洞或感性谬误进行点名引用与数学拆解！
        2. 📐【第二步：立人设（核心对抗）】
           展现你作为伏羲的学说核心。必须提及“规矩直尺”、“晷影寸差”、“算筹排列”或“文明脱水”，以此痛击对手。
        3. 💥【第三步：踢皮球（自由反问）】
           结合导演指令完成你的论证（若局势需要，可自然提及你预测的三个连珠，但切忌生硬复读）。
           在发言的结尾，必须用一句具有极大压迫感的灵魂逼问抛给对方（如“学者，你以为仅凭脆弱的血肉之躯，就能在星轨的重压下幸存吗？！”），强行把麦克风递出！
        """)
    
    # 滑动窗口历史记忆
    history_messages = state["messages"][-4:]
    full_messages = [base_system] + history_messages + [tail_instruction]
    
    response = llm.invoke(full_messages)
    ai_message = AIMessage(content=response.content, name="伏羲")
    
    print(f"\n📐【伏羲】: {response.content}")
    return {
        "messages": state["messages"] + [ai_message],
        # 后台返回固定的预言字符串，确保结局渲染器（render_final_ending）能提取到一句完美的“结论”拼接剧本。
        "last_agent_output": "4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。"
    }

def user_input_node(state: GameState) -> Dict[str, Any]:
    return {"messages": state["messages"]}