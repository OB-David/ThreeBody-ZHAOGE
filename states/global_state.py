from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class GameState(TypedDict):
    # 消息流与历史
    messages: List[BaseMessage]     # 统一事件总线，存放所有对话
    last_agent_output: str          # 记录上一次 Agent 生成的具体预测文本
    last_speaker: str                # 记录上一次发言者的身份（玩家/周文王/伏羲）
    last_target: str                 # 记录上一次发言的针对目标（玩家/周文王/伏羲/所有人/不明确）
    next_agent_instruction: str     # 大导演给下一轮 Agent 的指令（反驳/附和/自由发挥等）
    final_ending_text: str       # 大导演LLM生成的史诗结局文本
    
    # 核心计数器与 4 大指标
    turn_count: int                 # 当前对话轮数
    empirical_authority: int        # 文王权威度 (A)
    fuxi_authority: int             # 伏羲权威度 (B)
    rational_certainty: int         # 理性度 (C)
    chaos_level: int                # 混乱度 (D)
    
    
    # 游戏终止标记
    game_over_reason: str           # "chaos_death" | "normal_end" | ""