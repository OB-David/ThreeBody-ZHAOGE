from langgraph.graph import StateGraph, END
from states.global_state import GameState
from nodes.supervisor_node import supervisor_node, supervisor_router
from nodes.agents_node import wenwang_node, fuxi_node, user_input_node
from nodes.bus_node import event_bus_node

# 1. 初始化图
workflow = StateGraph(GameState)

# 2. 注册所有节点
workflow.add_node("event_bus", event_bus_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("wenwang", wenwang_node)
workflow.add_node("fuxi", fuxi_node)
workflow.add_node("user_input", user_input_node)

# 3. 构建连线 (Data & Control Flow)
# 任何 Agent 或用户输入完，统一汇聚到 Event Bus
workflow.add_edge("wenwang", "event_bus")
workflow.add_edge("fuxi", "event_bus")
workflow.add_edge("user_input", "event_bus")

# Event Bus 将数据整理后流向 Supervisor 进行裁判
workflow.add_edge("event_bus", "supervisor")

# 4. Supervisor 做出 4-way 分支决策 (条件路由)
workflow.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "request_user": "user_input",
        "activate_wenwang": "wenwang",
        "activate_fuxi": "fuxi",
        "request_user": END,
        "end_by_chaos": END,        # 中途被刺死
        "end_by_evaluation": END   # 10轮结束，进入结算
    }
)

# 设置入口
workflow.set_entry_point("user_input")

# 编译图
game_engine = workflow.compile()