import os
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from states.global_state import GameState

def supervisor_node(state: GameState) -> Dict[str, Any]:
    """
    裁判智能体：负责每一轮对局的指标审计、针对目标探测、三幕剧时间线硬分段、对线轮数控制与分支调度。
    """
    # -----------------------------------------------------------------
    # 1. 物理层级硬判定：读取当前轮数并划分“三幕剧”阶段
    # -----------------------------------------------------------------
    turn_count = state.get("turn_count", 10)
    
    if turn_count >= 8:
        current_stage = 1  # 第一幕：大殿异端 (10 - 8 轮)
        max_ai_strikes = 1 # NPC 连续对线保护：上限为 1 轮
    elif 4 <= turn_count <= 7:
        current_stage = 2  # 第二幕：学术论战 (7 - 4 轮)
        max_ai_strikes = 2 # NPC 连续对线解禁：上限为 2 轮（允许神仙打架）
    else:
        current_stage = 3  # 第三幕：末日审判 (3 - 0 轮)
        max_ai_strikes = 1 # 终局摊牌阶段：上限重回 1 轮（生死抉择）

    # 读取当前指标
    current_chaos = state.get("chaos_level", 20)
    A = state.get("empirical_authority", 20)
    B = state.get("fuxi_authority", 20)

    # 2. 终局条件硬拦截（含第一二幕暴毙保护）
    if current_stage == 3 and current_chaos >= 80:
        # 只有在第三幕才解除限制，允许触发混乱暴毙
        return {"game_over_reason": "chaos_death"}
    
    if turn_count <= 0:
        return {"game_over_reason": "normal_end", "turn_count": 0}

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

    # 4. 绑定大模型
    llm = ChatOpenAI(
        model=os.getenv("SUPERVISOR_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.1  # 极低温度保证裁判决策的客观与严谨
    )

    # -----------------------------------------------------------------
    # 5. 【核心逻辑】动态生成第三幕的分支戏剧背景（优势NPC掌控文明命运）
    # -----------------------------------------------------------------
    if A >= 50 and A > B:
        stage_3_context = f"""
        * 【戏剧状态 - 文王制霸】当前周文王权威极高({A}%)，占据绝对统治地位！他狂妄地认为他的易经八卦已经推演出了宇宙终极乾坤。他已经决定强推春耕，坚信万物将进入黄金盛世！
        * 🚨演出传音特则：你发给【周文王】的指令必须是“以绝对自信的统治者姿态，重申并捍卫他的终极预测：‘4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。’，强推春耕，视反抗为亵渎天命”。发给【伏羲】的则是“绝望、被边缘化，只能不顾一切地用日晷参数做最后的垂死反扑”。
        """
    elif B >= 50 and B > A:
        stage_3_context = f"""
        * 【戏剧状态 - 伏羲制霸】当前伏羲权威极高({B}%)，占据绝对统治地位！他以冰冷傲慢的理性姿态宣称，他的同心圆日晷模型是唯一真理。
        * 🚨演出传音特则：你发给【伏羲】的指令必须是“以数学至上的骄傲与自负，重申并捍卫他的测算：‘4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。’，冷酷命令所有人避难”。发给【周文王】的则是“卦象崩塌、在大殿角落如疯癫神棍般发出临终的诅咒”。
        """
    else:
        stage_3_context = f"""
        * 【戏剧状态 - 诸神黄昏】当前双方权威均等或较低，面对即将耗尽的末日异变，两人均未建立模型优势。
        * 🚨演出传音特则：发给演员的指令必须包含“癫狂与挣扎”。文王崩溃想要开启血腥的“人牲大祭祀”来向天求饶，伏羲狂躁想要砸毁青铜日晷和不完美的宇宙同归于尽。
        """

    stage_intro_prompts = {
        1: f"""
        【当前处于第一幕：大殿异端 (游戏保护期 / 拒绝超前)】
        - 戏剧基调：玩家作为未来学者初登大殿，朝歌弥信与僵化气氛极浓。文王和伏羲对现代科学毫无认知。
        - 🚨审计特则：如果玩家提出“引力”、“多星运动”、“三体”等现代科学概念，必须判定为“异端邪说”。此时玩家理性度(C)本轮必须强制增加 0！同时文王与伏羲的权威应有所升高，环境混乱度(D)必须大增 15 - 20。
        """,
        2: f"""
        【当前处于第二幕：学术论战 (理性解锁期)】
        - 戏剧基调：狂风骤雨，大殿天象异变，文王与伏羲不得不审视学者的观点。真正的论战开启。
        - 🚨审计特则：开始支持玩家获取理性度(C)。大导演需检查玩家发言是否咬住了上一个说话者 [{state.get('last_speaker', '无')}] 的逻辑漏洞。
        - 如果玩家能精准击中伏羲的“完美圆周无法解释突变骤冷骤热”，或文王的“演卦纯属幸存者偏差”，理性度(C)暴增 10 - 20，混乱度(D)下降。
        - 如果玩家毫无建树、泛泛而谈，混乱度(D)增加 5-15。
        - 🚨预警状态：当前环境混乱度为 {current_chaos}%，若玩家继续胡言乱语导致混乱度突破 70%，导演必须在 reason 中给出严厉的灭亡预警。
        """,
        3: f"""
        【当前处于第三幕：末日审判 (诸神黄昏)】
        - 戏剧基调：四个时辰即将耗尽，毁灭性的乱纪元威压在即。
        {stage_3_context}
        - 🚨生死局：除非玩家指明“脱水”这一唯一生路，否则其理性度(C)难以得到救赎。
        """
    }

    if is_player_turn:
        turn_decrement = 1
        system_prompt = f"""
        你现在是《三体》游戏【幕后总导演/裁判】。玩家（学者）刚刚发言。
        请更新世界指标，并根据【针对目标判定】或局势指派一名NPC上场。
        
        {stage_intro_prompts[current_stage]}

        【强硬规则：必须指派 AI 回复】
        因为现在是玩家刚发言完毕的回合，为了保证互动的连贯性，你【绝对不能】选择 'REQUEST_USER'！
        你【必须】在 'ACTIVATE_WENWANG'（激活周文王）与 'ACTIVATE_FUXI'（激活伏羲）之间二选一。
        
        【当前世界状态】
        * 文王权威度(A): {A} 
        * 伏羲权威度(B): {B} 
        * 玩家理性度(C): {state['rational_certainty']} 
        * 环境混乱度(D): {current_chaos}
        """
    else:
        turn_decrement = 0
        if ai_strike_count >= max_ai_strikes:
            action_instruction = f"【🚨强力约束】当前连续对线数已达该阶段上限 {max_ai_strikes} 轮。为了不让玩家受冷落，你【必须】选择 'REQUEST_USER' 将控制权还给玩家。"
        else:
            other_actor = "伏羲" if "文王" in latest_speaker else "周文王"
            next_actor_action = "ACTIVATE_FUXI" if "文王" in latest_speaker else "ACTIVATE_WENWANG"
            action_instruction = f"当前NPC对线轮数为 {ai_strike_count} 轮，上限为 {max_ai_strikes} 轮。你可以根据【针对目标判定】，选择让 '{other_actor}' 立即跳出来爆发唇枪舌剑（选择 '{next_actor_action}'），或者把控制权还给玩家（选择 'REQUEST_USER'）。"

        system_prompt = f"""
        你现在是《三体》游戏【幕后总导演】。NPC【{latest_speaker}】刚刚完成了台词。
        请根据【针对目标判定】决定下一步的调度。
        {action_instruction}
        
        {stage_intro_prompts[current_stage]}
        """

    # 追加针对目标判定、动态结盟与格式规范
    system_prompt += f"""
    
    【🚨核心调度：针对目标判定与动态结盟规则】
    1. 仔细分析【{latest_speaker}】刚才说的那句话，判定他到底是在跟谁说话：
       - 如果发言或动作中明确点名对方（如“伏羲”、“文王”、“学者”），则 target 为被叫名字的人（周文王 / 伏羲 / 玩家）。
       - 如果发言没有点名，但内容是强烈的反驳，通常是在对上一个说话的人说话。
       - 如果是泛泛而谈或对所有人说话，target 为“所有人”。
       
    2. 【动态结盟 (Dynamic Alliance) 特别逻辑】：
       - 如果当前在【第二幕】，且上一轮是【玩家发言】在严厉地批判【伏羲】的数学，你应当让【周文王】乘胜追击进行拉拢结盟。
       - 如果 target 是“伏羲”，且玩家强烈嘲讽了伏羲，请指派 next_action = 'ACTIVATE_WENWANG'，并传音给文王，让他以慈祥、赞许的姿态拉拢玩家，并一同打压伏羲。

    【调度决策树】
    1. 如果 NPC 连续对线已经达到该阶段上限 {max_ai_strikes} 轮，必须选择 REQUEST_USER。
    2. 如果当前是玩家刚发言完毕的回合（is_player_turn 为 True），则 next_action 必须在 ACTIVATE_WENWANG 与 ACTIVATE_FUXI 中选择，绝对禁止选择 REQUEST_USER。
    3. 否则，如果 target 是【周文王】，next_action 必须为 ACTIVATE_WENWANG。
    4. 否则，如果 target 是【伏羲】，next_action 必须为 ACTIVATE_FUXI。
    5. 如果 target 是“玩家”、“所有人”或无法模糊判定，则根据谁的权威度受刺激更深来指派 NPC。

    【返回格式要求 - 严格遵循，无需任何Markdown，不要包含 ```】
    delta_A: 数值
    delta_B: 数值
    delta_C: 数值
    delta_D: 数值
    target: 被针对的对象名字（周文王 / 伏羲 / 玩家 / 所有人）
    next_action: ACTIVATE_WENWANG 或 ACTIVATE_FUXI 或 REQUEST_USER
    agent_instruction: 如果下一步指派了NPC，明确告诉他面对【{latest_speaker}】刚才对他的点名、攻击、拉拢、或者大殿的混乱状态，他应该采取怎样的对线姿态（严重反驳/顺势拉拢结盟/顺势附和），并指明具体的对线攻击词汇。如果是 REQUEST_USER，此处写“等待玩家表态”。
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
        next_action = safe_extract(r"next_action[:\s\*]+(\w+)", text, "REQUEST_USER")
        agent_instruction = safe_extract(r"agent_instruction[:\s\*]+([^\n\r]+)", text, "请根据当前局势自由发挥。")
        reason = safe_extract(r"reason[:\s\*]+([^\n\r]+)", text, "大导演未给出理由。")

    except Exception as e:
        print(f" ⚠️ [导演系统警告] 裁判文本剧本解析严重失败: {e}。启动安全兜底机制...")
        return {
            "empirical_authority": A,
            "fuxi_authority": B,
            "rational_certainty": state["rational_certainty"],
            "chaos_level": min(100, current_chaos + 2),
            "turn_count": turn_count - turn_decrement,
            "game_over_reason": "",
            "last_agent_output": "REQUEST_USER",
            "next_agent_instruction": "请根据当前局势自由发挥。",
            "last_speaker": latest_speaker,
            "last_target": "所有人"
        }

    # 7. 物理安全级卫兵 (Hard Guard)
    # 规则 A：如果是玩家的回合，必须强制指派一个 AI 回复
    if is_player_turn and next_action == "REQUEST_USER":
        if A >= B:
            next_action = "ACTIVATE_WENWANG"
            agent_instruction = "学者刚刚发言完毕，大殿混乱，请立刻出列回应学者，展现你的易经卦象与天命论！"
        else:
            next_action = "ACTIVATE_FUXI"
            agent_instruction = "学者刚刚发言完毕，请立刻出列用你的几何日晷模型无情痛击学者的软弱！"

    # 规则 B：如果连续发言达到或超过该阶段上限，强制切回玩家
    if ai_strike_count >= max_ai_strikes:
        next_action = "REQUEST_USER"
        agent_instruction = "等待玩家表态"

    # 8. 硬性分段指标结算控制
    # 第一幕强制锁定理性值 C 为 0，并将混乱度硬锁在 75
    raw_C = state["rational_certainty"] + delta_C
    raw_D = current_chaos + delta_D

    if current_stage == 1:
        new_C = 0
        new_D = max(0, min(75, raw_D))  # 第一幕物理封顶混乱度为 75%，无法触发暴毙
    else:
        new_C = max(0, min(100, raw_C))
        new_D = max(0, min(100, raw_D))
        
    new_A = max(0, min(100, A + delta_A))
    new_B = max(0, min(100, B + delta_B))
    
    # 打印幕后导演日志与雷达监控
    print(f"\n🎬【第 {current_stage} 幕导演日志】: {reason}")
    print(f"🎯【目标探测】: {latest_speaker} 🎯 正在对 【{target}】 说话 (当前连续对线数: {ai_strike_count}/{max_ai_strikes})")
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
        "last_speaker": latest_speaker,   # 精准写回全局记忆体
        "last_target": target             # 精准写回全局记忆体
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