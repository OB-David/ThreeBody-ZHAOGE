# nodes/bus_node.py
from typing import Dict, Any
from states.global_state import GameState
from langchain_core.messages import AIMessage, HumanMessage

def event_bus_node(state: GameState) -> Dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    latest_msg = messages[-1]
    
    # 在控制台打出漂亮的事件流向日志
    print("\n" + "┈"*30 + " BUS EVENT LOG " + "┈"*30)
    if isinstance(latest_msg, HumanMessage):
        print(f"玩家投递新信号 ➔ \"{latest_msg.content}\"")
    elif isinstance(latest_msg, AIMessage):
        sender = latest_msg.name if latest_msg.name else "未知实体"
        print(f"{sender} 广播了新发言 ➔ (已同步至全局全局记忆体)")
    print("" + "┈"*75)

    # 保持数据完整性，原样流入下一个节点（Supervisor）
    return {"messages": messages}