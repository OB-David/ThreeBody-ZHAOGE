import os
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from states.global_state import GameState

def supervisor_node(state: GameState) -> Dict[str, Any]:
    """
    裁判智能体：负责每一轮对局的指标审计、针对目标探测、对线轮数控制与分支调度。
    """
    # 1. 最高优先级：基础终局状态拦截
    if state["chaos_level"] >= 80: 
        return {"game_over_reason": "chaos_death"}
    if state["turn_count"] <= 0: 
        return {"game_over_reason": "normal_end", "turn_count": 0}

    # 获取最新一条发言
    latest_msg = state["messages"][-1] if state["messages"] else None
    
    # 判断是否为玩家发言 (HumanMessage 或者没有显式指定 name 的消息)
    is_player_turn = True
    latest_speaker = "玩家"
    latest_content = "你好"
    
    if latest_msg:
        is_player_turn = isinstance(latest_msg, HumanMessage) or not getattr(latest_msg, "name", None)
        latest_speaker = getattr(latest_msg, "name", "玩家")
        latest_content = latest_msg.content

    # 2. 【核心修复】精准计算当前末尾连续的 NPC (AI) 发言轮数
    ai_strike_count = 0
    if state["messages"]:
        for msg in reversed(state["messages"]):
            # 如果是 AIMessage 或者是带有文王/伏羲名字的消息，计入连续 NPC 发言
            if isinstance(msg, AIMessage) or getattr(msg, "name", None) in ["周文王", "伏羲"]:
                ai_strike_count += 1
            else:
                # 一旦遇到玩家发送的消息，立刻中断计数
                break

    # 3. 绑定 DeepSeek 裁判大模型
    llm = ChatOpenAI(
        model=os.getenv("SUPERVISOR_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.1  # 极低温度保证裁判逻辑的高度确定性与客观性
    )

    # 4. 根据说话者身份与连续对线状态，动态构建大导演的审计与决策 Prompt
    if is_player_turn:
        # ────────── 玩家发言回合：审计世界指标，扣除有效轮数 ──────────
        turn_decrement = 1
        system_prompt = f"""
        你现在是《三体》游戏【幕后总导演/裁判】。玩家（学者）刚刚发言。
        请更新世界指标，并根据【针对目标判定】或局势指派一名NPC上场。
        
        【🚨🚨强硬规则：必须指派 AI 回复】
        因为现在是玩家刚发言完毕的回合，为了保证互动的连贯性，你【绝对不能】选择 'REQUEST_USER'！
        你【必须】在 'ACTIVATE_WENWANG'（激活周文王）与 'ACTIVATE_FUXI'（激活伏羲）之间二选一。
        
        【当前世界状态】
        * 文王权威度(A): {state['empirical_authority']} (代表经验与天命)
        * 伏羲权威度(B): {state['fuxi_authority']} (代表机械数学)
        * 玩家理性度(C): {state['rational_certainty']} (代表指出双方谬误)
        * 环境混乱度(D): {state['chaos_level']}
        """
    else:
        # ────────── NPC 对线回合：不扣除玩家轮数，严格限制连续互撕 ──────────
        turn_decrement = 0
        
        # 强力提示词约束：防止玩家被冷落
        if ai_strike_count >= 2:
            action_instruction = "【🚨强力约束】NPC之间已经连续对线互撕了2轮（当前已达2轮），为了保证玩家的交互感，这次你【必须】选择 'REQUEST_USER' 将麦克风还给玩家。"
        else:
            other_actor = "伏羲" if "文王" in latest_speaker else "周文王"
            next_actor_action = "ACTIVATE_FUXI" if "文王" in latest_speaker else "ACTIVATE_WENWANG"
            action_instruction = f"当前NPC对线轮数为 {ai_strike_count} 轮。你可以根据【针对目标判定】，尽量选择让另一个NPC立即跳出来反驳（选择 '{next_actor_action}'），在辩论后期遇到中性情况时可以把控制权还给玩家（选择 'REQUEST_USER'），特别是1-3对话，不要把控制器还给玩家！！！。"

        system_prompt = f"""
        你现在是《三体》游戏【幕后总导演】。NPC【{latest_speaker}】刚刚完成了台词。
        请根据【针对目标判定】决定下一步的调度。
        {action_instruction}
        """

    # 追加针对目标判定（Target Detection）规则与格式约束
    system_prompt += f"""
    
    【🚨核心调度核心：针对目标判定规则】
    仔细分析【{latest_speaker}】刚才说的那句话，判定他到底是在跟谁说话：
    - 如果发言或者动作提示中明确提到了对方的名字（如“伏羲”，“文王”），则 target 为被叫名字的人（周文王 / 伏羲）。
    - 如果发言或者动作提示中提到了玩家和NPC名字如（“伏羲”，“文王”），默认 target 是被点名的 NPC。
    - 如果发言没有点名，但内容是强烈的反驳，通常是在对上一个说话的人说话。
    - 如果是泛泛而谈或对所有人说话，target 为“所有人”。
    
    【调度决策树】
    1. 如果 NPC 连续对线已经达到 2 轮，必须选择 REQUEST_USER。
    2. 如果当前是玩家刚发言完毕的回合（is_player_turn 为 True），则 next_action 必须在 ACTIVATE_WENWANG 与 ACTIVATE_FUXI 中选择，绝对禁止选择 REQUEST_USER。
    3. 否则，如果 target 是【周文王】，next_action 必须为 ACTIVATE_WENWANG。
    4. 否则，如果 target 是【伏羲】，next_action 必须为 ACTIVATE_FUXI。
    5. 如果 target 是“玩家”、“所有人”或无法模糊判定，则根据谁的权威度受刺激更深来指派 NPC。

    【🚨🚨返回格式要求 - 严格遵循，无需任何Markdown，不要包含 ```】
    delta_A: 数值
    delta_B: 数值
    delta_C: 数值
    delta_D: 数值
    target: 被针对的对象名字（周文王 / 伏羲 / 玩家 / 所有人）
    next_action: ACTIVATE_WENWANG 或 ACTIVATE_FUXI 或 REQUEST_USER
    agent_instruction: 如果下一步指派了NPC，明确告诉他面对【{latest_speaker}】刚才对他的点名或攻击，他应该采取怎样的姿态（严重反驳还是顺势附和），并指明对线焦点。如果是 REQUEST_USER，此处写“等待玩家表态”。
    reason: 你的导演复盘思考过程
    """

    # 5. 调用大模型并进行超强鲁棒性正则捕获
    recent_messages = state["messages"][-3:] if len(state["messages"]) >= 3 else state["messages"]
    eval_messages = [SystemMessage(content=system_prompt)] + recent_messages
    
    try:
        response = llm.invoke(eval_messages)
        text = response.content
        
        # 兼容 **delta_A**: 10, delta_A:10 等各种野生Markdown加粗与空格格式
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
        print(f" ⚠️ [导演系统警告] 裁判文本剧本解析失败: {e}。启动安全兜底机制...")
        # 兜底降级：直接交还给玩家发言，防止崩溃
        return {
            "empirical_authority": state["empirical_authority"],
            "fuxi_authority": state["fuxi_authority"],
            "rational_certainty": state["rational_certainty"],
            "chaos_level": min(100, state["chaos_level"] + 2),
            "turn_count": state["turn_count"] - turn_decrement,
            "game_over_reason": "",
            "last_agent_output": "REQUEST_USER",
            "next_agent_instruction": "请根据当前局势自由发挥。"
        }

    # 6. 【强力物理级卫兵（Hard Guard）】
    # 规则 A：如果是玩家的回合，必须强制指派一个 AI 回复，绝对不允许直接 REQUEST_USER 空转
    if is_player_turn and next_action == "REQUEST_USER":
        # 根据当前的权威度，谁高指派谁；如果一样高，默认指派文王
        if state["empirical_authority"] >= state["fuxi_authority"]:
            next_action = "ACTIVATE_WENWANG"
            agent_instruction = "玩家刚刚发言完毕，你现在权威度较高，请立刻出列回应玩家，展现你的易经卦象与天命论！"
        else:
            next_action = "ACTIVATE_FUXI"
            agent_instruction = "玩家刚刚发言完毕，你现在理性权威较高，请立刻出列用你的几何日晷模型无情回应玩家！"

    # 规则 B：如果连续发言达到或超过 2 轮，哪怕大模型在 next_action 里返回了 ACTIVATE，也强制切回玩家发言
    if ai_strike_count >= 2:
        next_action = "REQUEST_USER"
        agent_instruction = "等待玩家表态"

    # 7. 限定世界指标范围在 0-100
    new_A = max(0, min(100, state["empirical_authority"] + delta_A))
    new_B = max(0, min(100, state["fuxi_authority"] + delta_B))
    new_C = max(0, min(100, state["rational_certainty"] + delta_C))
    new_D = max(0, min(100, state["chaos_level"] + delta_D))
    
    print(f"🎬【导演日志】: {reason}")
    print(f"🎯【目标探测】: {latest_speaker} 🎯 正在对 【{target}】 说话 (NPC连续对线数: {ai_strike_count})")
    if next_action != "REQUEST_USER":
        print(f"📣【导演传音给演员】: {agent_instruction}")

    return {
        "empirical_authority": new_A,
        "fuxi_authority": new_B,
        "rational_certainty": new_C,
        "chaos_level": new_D,
        "turn_count": state["turn_count"] - turn_decrement,
        "game_over_reason": "normal_end" if next_action == "TERMINATE" else "",
        "last_agent_output": next_action,
        "next_agent_instruction": agent_instruction 
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