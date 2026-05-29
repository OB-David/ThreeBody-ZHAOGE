import os
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from states.global_state import GameState

# 🤫 静默模式开关：设为 True 则只在控制台展示角色对话，不打印任何幕后思考与中间审计日志
SILENT_MODE = False

def _generate_llm_ending(llm: ChatOpenAI, state: GameState, end_type: str, A: int, B: int, C: int, D: int) -> str:
    # 提取并格式化全剧对话历史
    history_lines = []
    for msg in state.get("messages", []):
        speaker = getattr(msg, "name", "玩家") if getattr(msg, "name", None) else ("AI" if isinstance(msg, AIMessage) else "玩家")
        history_lines.append(f"【{speaker}】: {msg.content}")
    history_str = "\n".join(history_lines)

    if end_type == "chaos_death":
        prompt_intent = """
        【结局走向：混乱暴毙 (chaos_death)】
        - 核心剧情：玩家的言论彻底激怒了所有人（大殿混乱度突破临界点）。周文王怒斥其为妖孽，伏羲叹息其亵渎真理，大殿卫兵一涌而上，乱刀之下，玩家血染沙盘。
        - 氛围渲染：幽暗的火光，冰冷的刀兵，以及极具讽刺感的一幕——半个时辰后的天机与文明兴衰，已不再与这个狂妄的死者相关。
        """
    elif end_type == "success_end":
        prompt_intent = """
        - 核心剧情：玩家展现了无可辩驳的现代科学理性，彻底指出了周文王玄学占卜的幸存者偏差，以及伏羲精密几何模型的突变漏洞（C >= 50 且完全压制NPC）。
        - 关键生成约束：请务必仔细阅读【对局发言历史】中【玩家】的最后一句发言！辨别玩家在面对最终质问时，做出的终极抉择是选择【脱水/隐藏】还是【浸泡/复活/春耕】。
          1. 若玩家最终选择【脱水/隐藏】：全城绝对服从指令，化为皮卷存入地窖。半个时辰后，地表爆发了极其恐怖的毁灭性灾难（如三日并凌空或酷热严寒突变），但由于理性保存，文明的火种在黑暗中安然存活。
          2. 若玩家最终选择【浸泡/复活/春耕】：全城赌上一切开启浸泡仪式，复活春耕。半个时辰后，温和明亮的恒纪元太阳奇迹般升起，世界春暖花开，文明由于没有盲目脱水而免于长满青苔化为春泥，在现代科学的引领下走向大跨越。
        """
    else:  # fail_end
        if A >= B:
            fail_flavor = "【经验的代价】纣王采纳了周文王的天誓预测：半个时辰后太阳从西方升起，开启百年恒纪元。全城停止一切防寒准备，开仓放粮，干枯的皮卷在欢呼中涌入浸泡池复活。然而半个时辰后，地平线上同时升起三颗巨大炽热的恒星——三日并凌空！在这片白炽的光海中，整个文明瞬间气化，朝歌归于永恒的沉寂。"
        else:
            fail_flavor = "【数学的傲慢】国家盲信了伏羲精密几何推导：乱纪元将持续200年，太阳将是三日连珠。朝廷下达残酷命令：全员立刻脱水折叠送入地窖。然而半个时辰后宇宙开了一个讽刺的玩笑，温和舒适的恒纪元准时降临。但由于地表无人员看守与举行复苏仪式，所有皮卷在长期温暖湿润中无声长满青苔化为春泥。文明在最期盼的春天里陷入永远的沉睡。"
        prompt_intent = f"""
        【结局走向：辩论失败 (fail_end)】
        - 当前主导错误世界观的NPC：{"周文王（经验与迷信占主导）" if A >= B else "伏羲（机械几何与傲慢占主导）"}
        - 结局基调参考：{fail_flavor}
        - 生成指令：结合整场对局中玩家未能说服两人的平庸表现，用极其悲壮、深沉、带有一丝宇宙冷酷讽刺的科幻文笔，描写这一场因盲信NPC而导致的文明毁灭。
        """

    system_prompt = f"""
    你现在是硬科幻巨著《三体》小说的总编剧。当前‘万年历辩论’已经迎来最终落幕。
    请根据以下提供的对局历史、最终世界指标和结局走向大纲，撰写一段画面感极强、极具史诗感和科幻哲思的动态终局叙事文本。

    【最终指标】
    - 周文王经验权威(A): {A}%
    - 伏羲理性权威(B): {B}%
    - 玩家理性确定性(C): {C}%
    - 环境混乱度(D): {D}%

    【对局发言历史】
    {history_str}

    【结局走向大纲】
    {prompt_intent}

    【严格写作要求】
    1. 必须保持高度宏大、冷酷、极具诗意与科学哲思的刘慈欣式笔触。
    2. 必须将玩家在整个辩论中的具体表现或他最后的生死抉择有机地编织进文本中，禁止生搬硬套。
    3. 绝对不要包含类似 "delta_A"、"Success"、"Game Over" 等任何游戏系统字眼或 Markdown 代码块包裹（严禁使用 ``` 标记），它应该是一段一气呵成的小说终章。
    """
    try:
        response = llm.invoke([SystemMessage(content=system_prompt)])
        return response.content.strip()
    except Exception as e:
        return f"【系统观测中断】朝歌大殿坍塌在不可预测的引力波动中，星系运行的冰冷规律抹去了一切观测记录... (错误: {str(e)})"


def supervisor_node(state: GameState) -> Dict[str, Any]:
    # -----------------------------------------------------------------
    # 1. 物理层级硬判定：读取当前轮数并划分“三幕剧”阶段
    # -----------------------------------------------------------------
    turn_count = state.get("turn_count", 6)
    
    if turn_count >= 5:
        current_stage = 1  # 第一幕：大殿异端 (5-6 轮)
        max_ai_strikes = 2 # NPC 连续对线保护
    elif 2 <= turn_count <= 4:
        current_stage = 2  # 第二幕：学术论战 (2 - 4 轮)
        max_ai_strikes = 3 # NPC 连续对线解禁
    else:
        current_stage = 3  # 第三幕：末日审判 (0 - 1 轮)
        max_ai_strikes = 2 # 终局摊牌阶段

    # 读取当前指标
    current_chaos = state.get("chaos_level", 20)
    A = state.get("empirical_authority", 20)
    B = state.get("fuxi_authority", 20)
    C = state.get("rational_certainty", 20)

    # -----------------------------------------------------------------
    # 【核心新增】2. 终局条件硬拦截 + 动态生成史诗级大结局
    # -----------------------------------------------------------------
    # 物理拦截需要大导演模型实例
    llm = ChatOpenAI(
        model=os.getenv("SUPERVISOR_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.1  # 指标审计保持低温度确保严谨，结局渲染函数内会单独处理语感
    )

    if current_stage == 3 and current_chaos >= 80:
        ending_text = _generate_llm_ending(llm, state, "chaos_death", A, B, C, current_chaos)
        return {"game_over_reason": "chaos_death", "final_ending_text": ending_text}
    
    if turn_count <= 0:
        # 当轮数耗尽，检查玩家是否达成了高理性大获全胜的指标
        if C >= 50 and C > A and C > B:
            end_type = "success_end"
        else:
            end_type = "fail_end"
        ending_text = _generate_llm_ending(llm, state, end_type, A, B, C, current_chaos)
        return {"game_over_reason": "normal_end", "turn_count": 0, "final_ending_text": ending_text}

    # 获取最新一条发言
    latest_msg = state["messages"][-1] if state["messages"] else None
    
    is_player_turn = True
    latest_speaker = "玩家"
    latest_content = "你好"
    
    if latest_msg:
        is_player_turn = isinstance(latest_msg, HumanMessage) or not getattr(latest_msg, "name", None)
        latest_speaker = getattr(latest_msg, "name", "玩家")
        latest_content = latest_msg.content

    # 3. 精准计算当前末尾连续的 NPC (AI) 发言轮数
    ai_strike_count = 0
    if state["messages"]:
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) or getattr(msg, "name", None) in ["周文王", "伏羲"]:
                ai_strike_count += 1
            else:
                break

    # -----------------------------------------------------------------
    # 5. 【保留原核心逻辑，增补理性胜出抉择判断】动态生成第三幕的分支戏剧背景
    # -----------------------------------------------------------------
    if C >= 50 and C > A and C > B:
        # 🌟 新增：玩家高理性分支，在大结局前（turn_count == 1）强行切入逼问回合
        stage_3_context = f"""
        * 【戏剧状态 - 真理降临/理性觉醒】当前学者（玩家）展现出了无可辩驳的现代科学理性({C}%)，完全压制了周文王({A}%)与伏羲({B}%)！他们的历史经验与几何沙盘模型被你无情拆穿，两人跌坐在殿堂阴影中。
        * 🚨演出传音特则：由于玩家理性度处于绝对制霸地位，你必须派出一名心服口服但极度惶恐的NPC（或大导演亲自传音），向玩家发起整场游戏最核心的【灵魂拷问】！
        * 🚨逼问要求：必须用颤抖但极其庄严的语气，迫使玩家（学者）在半个时辰后的末日天象到来前做出全文明的最终抉择——到底是【全员立刻脱水折叠送入地窖】还是【全员浸泡复活准备迎接春耕】？
        """
    elif A >= 50 and A > B:
        stage_3_context = f"""
        * 【戏剧状态 - 文王制霸】当前周文王权威极高({A}%)，占据绝对统治地位！他高傲地认为他的易经八卦已经推演出了宇宙终极乾坤。他已经决定强推春耕，坚信万物将进入黄金盛世！
        * 🚨演出传音特则：你发给【周文王】的指令必须是“以绝对自信的贵族姿态，重申并捍卫他的终极预测：‘半个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。’，强推春耕，视反抗为亵渎天命”。
            文王不停催促玩家拥护这个决定，不停地劝伏羲迷途知返。
            发给【伏羲】的则是“绝望、被边缘化，只能眼睁睁看着文明走向毁灭”。
        """
    elif B >= 50 and B > A:
        stage_3_context = f"""
        * 【戏剧状态 - 伏羲制霸】当前伏羲权威极高({B}%)，占据绝对统治地位！他以冰冷傲慢的理性姿态宣称，他的日晷算筹沙盘模型是唯一真理。
        * 🚨演出传音特则：你发给【伏羲】的指令必须是“以数学至上的骄傲与自负，重申并捍卫他的测算：‘半个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。’，冷酷命令所有人避难”。
            伏羲不停催促玩家拥护这个决定，不停地劝文王放弃迷信，接受科学的末日预言。
            发给【周文王】的则是“卦象崩塌、在大殿角落如低沉地发出临终的诅咒”。
        """
    else:
        stage_3_context = f"""
        * 【戏剧状态 - 诸神黄昏】当前双方权威均等或较低，两人均未建立模型优势。
        * 🚨演出传音特则：发给演员的指令必须包含“癫狂、挣扎与惶恐”。文王和伏羲的世界观遭受冲击，他们都不知道半个时辰之后降临的是什么。文王和伏羲放弃了所有的预测，放弃说服互相，决定亲眼去见半个时辰后的结果。
        * 🚨必须逼问玩家（学者）做出最终选择，引导玩家说出："脱水准备三日连珠的乱纪元，或全员浸泡准备春耕"。
        """

    stage_intro_prompts = {
        1: f"""
        【当前处于第一幕：大殿异端 (游戏保护期 / 拒绝超前)】
        - 戏剧基调：玩家作为未来学者初登大殿，朝歌弥信与僵化气氛极浓。文王和伏羲对现代科学毫无认知。文王和伏羲正在对一个时辰后的天象进行辩论。
        - 🚨审计特则：如果玩家提出“引力”、“多星运动”、“三体”等现代科学概念，必须判定为“异端邪说”。此时玩家理性度(C)本轮必须强制增加 0！同时文王与伏羲的权威应有所升高，环境混乱度(D)必须大增 10 - 20。
        - 🚨一般情况：玩家发言若未触及敏感话题或者显著混乱，请决定理性度(C)变化：减少0-5或者增加0-5，和混乱度（D）变化：减少0-5或者增加0-5。
        """,
        2: f"""
        【当前处于第二幕：学术论战 (理性解锁期)】
        - 戏剧基调：狂风骤雨，大殿天象异变，文王与伏羲不得不审视学者的观点。真正的论战开启。距离它们预测的天象降临还有半个时辰，时间紧迫，悬念迭起。
        - 🚨审计特则：开始支持玩家获取理性度(C)。大导演需检查玩家或者NPC发言是否咬住了上一个说话者 [{state.get('last_speaker', '无')}] 的逻辑漏洞。
        - 如果玩家能精准击中伏羲的“完美圆周，连续的模型无法解释突变”，或文王的“演卦纯属幸存者偏差”，理性度(C)暴增 10 - 20，混乱度(D)下降。
        - 如果文王和伏羲互相攻击对方的预测漏洞，理性度(C)小增 5-10，混乱度(D)小增 5-10。文王的权威度(A) and 伏羲的权威度(B)也应根据攻击的犀利程度小幅变动。
        - 如果玩家毫无建树、泛泛而谈，混乱度(D)增加 5-15。
        - 🚨预警状态：当前环境混乱度为 {current_chaos}%，若玩家继续胡言乱语导致混乱度突破 70%，导演必须在 reason 中给出严厉的灭亡预警。
        """,
        3: f"""
        【当前处于第三幕：末日审判 (诸神黄昏)】
        - 戏剧基调：半个时辰即将耗尽，毁灭性的乱纪元威压在即。
        {stage_3_context}
        - 🚨生死局：文王和伏羲应该催促玩家给出他的最终预测，做最后的决定。
        """
    }

    if is_player_turn:
        turn_decrement = 1
        system_prompt = f"""
        你现在是《三体》游戏【幕后总导演/裁判】。文王，伏羲和玩家在朝歌大殿上讨论即将到来的天象。
        文王始终坚持他的经验主义预测，认为一个时辰后日出西方，为期100年的恒纪元将降临。伏羲则坚信他的机械几何模型，认为一个时辰后将是三日连珠，乱纪元还将持续至少200年。
        玩家（学者）刚刚发言。请更新世界指标，并根据【针对目标判定】或局势指派一名NPC上场。
        
        {stage_intro_prompts[current_stage]}

        【强硬规则：必须指派 AI 回复】
        因为现在是玩家刚发言完毕的回合，为了保证互动的连贯性，你【绝对不能】选择 'REQUEST_USER'！
        你【必须】在 'ACTIVATE_WENWANG'（激活周文王）与 'ACTIVATE_FUXI'（激活伏羲）之间二选一。
        
        【当前世界状态】
        * 文王权威度(A): {A} 
        * 伏羲权威度(B): {B} 
        * 玩家理性度(C): {C} 
        * Environment 混乱度(D): {current_chaos}
        """
    else:
        turn_decrement = 0
        if ai_strike_count >= max_ai_strikes:
            action_instruction = f"【🚨强力约束】当前连续对线数已达该阶段上限 {max_ai_strikes} 轮。为了不让玩家受冷落，你【必须】选择 'REQUEST_USER' 将控制权还给玩家。"
        else:
            other_actor = "伏羲" if "文王" in latest_speaker else "周文王"
            next_actor_action = "ACTIVATE_FUXI" if "文王" in latest_speaker else "ACTIVATE_WENWANG"
            action_instruction = f"当前NPC对线轮数为 {ai_strike_count} 轮，上限为 {max_ai_strikes} 轮。你可以根据【针对目标判定】，选择让 '{other_actor}' 立即跳出来争辩（选择 '{next_actor_action}'），或者把控制权还给玩家（选择 'REQUEST_USER'）。"

        system_prompt = f"""
        你现在是《三体》游戏【幕后总导演】。NPC【{latest_speaker}】刚刚完成了台词。
        请根据【针对目标判定】决定下一步的调度。
        {action_instruction}
        
        {stage_intro_prompts[current_stage]}
        """

    # 追加针对目标判定、动态结盟与格式规范，并特别引入“回应模式”判定规则
    system_prompt += f"""
    
    【🚨核心判定：交互模式探测器（回应 RESPOND vs 争辩 DEBATE）】
    请根据玩家发言的意图和语气，判定本次互动的基本模式：
    - 如果玩家问的是一个**求知、客观、纯粹事实或中性的问题**（例如：“现在是文明第几个轮回”、“这日晷是由什么打造的”、“大殿外是何天象”、“这是哪里”），请在返回中将模式记为 `RESPOND` 模式。
    - 如果玩家发表的是**观点挑战、质疑、争论、或者是带有明显价值偏向的断言**（例如：“你们讨论这些没意义”、“科学是唯一的真理”、“文王的易经是伪科学”），请在返回中将模式记为 `DEBATE` 模式。

    【🚨核心调度：针对目标判定与动态结盟规则】
    1. 仔细分析【{latest_speaker}】刚才说的那句话，判定他到底是在跟谁说话：
       - 如果发言或动作中明确点名对方（如“伏羲”、“文王”、“学者”），则 target 为被叫名字的人（周文王 / 伏羲 / 玩家）。
       - 如果发言没有点名，但内容是强烈的反驳，通常是在对上一个说话的人说话。
       - 如果NPC第一次回答是在冷静回应玩家，则target更新为另一个NPC，让这个NPC不要误导玩家。
       - 如果NPC泛泛而谈或对所有人说话，则 target 是另一个NPC，期望另一个NPC可以多参与对话。
       - 只有玩家泛泛而谈时认为target是“所有人”。
       
    2. 【动态结盟 (Dynamic Alliance) 特别逻辑】：
       - 如果当前在【第二幕】，且上一轮是【玩家发言】在严厉地批判【伏羲】的数学，你应当让【周文王】乘胜追击进行拉拢结盟。
       - 如果 target 是“文王”，且玩家指出了文王的谬误，请指派 【伏羲】乘胜追击进行拉拢结盟。

    【调度决策树】
    1. 如果 NPC 连续对线已经达到该阶段上限 {max_ai_strikes} 轮，必须选择 REQUEST_USER。
    2. 如果当前是玩家刚发言完毕的回合（is_player_turn 为 True），则 next_action 必须在 ACTIVATE_WENWANG 与 ACTIVATE_FUXI 中选择，绝对禁止选择 REQUEST_USER。
    3. 否则，如果 target 是【周文王】，next_action 必须为 ACTIVATE_WENWANG。
    4. 否则，如果 target 是【伏羲】，next_action 必须为 ACTIVATE_FUXI。
    5. 如果 target 是“玩家”、“所有人” or 无法模糊判定，则根据谁的权威度受刺激更深来指派 NPC。

    【返回格式要求 - 严格遵循，无需任何Markdown，不要包含 ```】
    delta_A: 数值
    delta_B: 数值
    delta_C: 数值
    delta_D: 数值
    target: 被针对的对象名字（周文王 / 伏羲 / 玩家 / 所有人）
    interaction_mode: RESPOND 或 DEBATE （RESPOND表示要求NPC进行知识性的冷静解答；DEBATE表示要求NPC进行唇枪舌剑的激烈反驳）
    next_action: ACTIVATE_WENWANG 或 ACTIVATE_FUXI 或 REQUEST_USER
    agent_instruction: [MODE: 填入上面的interaction_mode] 明确告诉登场的NPC应该采取怎样的姿态（若为RESPOND，要求其保持博学、深沉的智慧，以自身学派视角冷静解答，不要冷嘲热讽；若为DEBATE，要求其用犀利的词汇进行反驳或顺势结盟），并指出其要解答/对线的核心词语。如果是 REQUEST_USER，此处写“等待玩家表态”。
    reason: 你的导演复盘思考过程，如果处于第二幕混乱度高，请在此发出红色的红色灭亡预警！
    """

    # 6. 调用大模型并进行鲁棒性正则捕获
    recent_messages = state["messages"][-3:] if len(state["messages"]) >= 3 else state["messages"]
    eval_messages = [SystemMessage(content=system_prompt)] + recent_messages
    
    try:
        response = llm.invoke(eval_messages)
        text = response.content
        
        def safe_extract(pattern, text, default="0"):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else default

        delta_A = int(safe_extract(r"delta_A[:\s\*]+(-?\d+)", text, "0"))
        delta_B = int(safe_extract(r"delta_B[:\s\*]+(-?\d+)", text, "0"))
        delta_C = int(safe_extract(r"delta_C[:\s\*]+(-?\d+)", text, "0"))
        delta_D = int(safe_extract(r"delta_D[:\s\*]+(-?\d+)", text, "0"))
        
        target = safe_extract(r"target[:\s\*]+([^\n\r]+)", text, "所有人")
        interaction_mode = safe_extract(r"interaction_mode[:\s\*]+(\w+)", text, "DEBATE")
        next_action = safe_extract(r"next_action[:\s\*]+(\w+)", text, "REQUEST_USER")
        agent_instruction = safe_extract(r"agent_instruction[:\s\*]+([^\n\r]+)", text, "请根据当前局势自由发挥。")
        reason = safe_extract(r"reason[:\s\*]+([^\n\r]+)", text, "大导演未给出理由。")

    except Exception as e:
        return {
            "empirical_authority": A,
            "fuxi_authority": B,
            "rational_certainty": C,
            "chaos_level": min(100, current_chaos + 2),
            "turn_count": turn_count - turn_decrement,
            "game_over_reason": "",
            "last_agent_output": "REQUEST_USER",
            "next_agent_instruction": "[MODE: DEBATE] 请根据当前局势自由发挥。",
            "last_speaker": latest_speaker,
            "last_target": "所有人"
        }

    # 7. 物理安全级卫兵 (Hard Guard)
    if is_player_turn and next_action == "REQUEST_USER":
        if A >= B:
            next_action = "ACTIVATE_WENWANG"
            agent_instruction = f"[MODE: {interaction_mode}] 学者刚刚发言完毕，请回应学者！"
        else:
            next_action = "ACTIVATE_FUXI"
            agent_instruction = f"[MODE: {interaction_mode}] 学者刚刚发言完毕，请回应学者！"

    if ai_strike_count >= max_ai_strikes:
        next_action = "REQUEST_USER"
        agent_instruction = "等待玩家表态"

    # 8. 硬性分段指标结算控制
    raw_C = C + delta_C
    raw_D = current_chaos + delta_D

    if current_stage == 1:
        new_C = 20
        new_D = max(0, min(75, raw_D))  # 第一幕物理封顶混乱度为 75%，无法触发暴毙
    else:
        new_C = max(0, min(100, raw_C))
        new_D = max(0, min(100, raw_D))
        
    new_A = max(0, min(100, A + delta_A))
    new_B = max(0, min(100, B + delta_B))
    
    # 🤫 【静默控制】
    if not SILENT_MODE:
        print(f"\n🎬【第 {current_stage} 幕导演日志】: {reason}")
        print(f"🎯【目标探测】: {latest_speaker} 🎯 正在对 【{target}】 说话 (当前模式: {interaction_mode} | NPC连续对线数: {ai_strike_count}/{max_ai_strikes})")
        print(f"【当前指标】 文王权威(A): {A} -> {new_A} | 伏羲权威(B): {B} -> {new_B} | 玩家理性度(C): {C} -> {new_C} | 环境混乱度(D): {current_chaos} -> {new_D}")
        if next_action != "REQUEST_USER":
            print(f"📣【导演传音】: {agent_instruction}")

    return {
        "empirical_authority": new_A,
        "fuxi_authority": new_B,
        "rational_certainty": new_C,
        "chaos_level": new_D,
        "turn_count": turn_count - turn_decrement,
        "game_over_reason": "normal_end" if next_action == "TERMINATE" else "",
        "last_agent_output": next_action,
        "next_agent_instruction": agent_instruction,
        "last_speaker": latest_speaker,   
        "last_target": target            
    }


# =====================================================================
# 条件路由函数 (配合 Graph 中的 conditional_edges)
# =====================================================================
def supervisor_router(state: GameState) -> str:
    """
    大导演决策路由
    """
    if state["game_over_reason"] == "chaos_death": 
        return "end_by_chaos"
    if state["game_over_reason"] == "normal_end" or state["turn_count"] <= 0: 
        return "end_by_evaluation"
    
    action = state.get("last_agent_output", "")
    if action == "ACTIVATE_WENWANG": 
        return "activate_wenwang"
    elif action == "ACTIVATE_FUXI": 
        return "activate_fuxi"
    else: 
        return "request_user"