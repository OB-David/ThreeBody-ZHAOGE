# main.py
import os
from dotenv import load_dotenv

# 强行初始化环境变量
load_dotenv()

if not os.getenv("DEEPSEEK_API_KEY") or not os.getenv("QWEN_API_KEY"):
    print("\n .env 文件未正确配置或未找到！")
    exit(1)

from graph import game_engine
from langchain_core.messages import HumanMessage, AIMessage

def render_final_ending(final_state):
    print("\n" + "="*25 + " 最终审判 " + "="*25)
    
    # 从全局状态中直接读取导演动态生成的结局文本
    ending_text = final_state.get("final_ending_text", "整个文明在无声中消亡，未能在历史中留下任何观测记录。")
    print(ending_text)
    
    print("="*70)
    print(f"📊 [终局复盘指标] 文王权威:{final_state['empirical_authority']}% | 伏羲权威:{final_state['fuxi_authority']}% | 你的理性度:{final_state['rational_certainty']}% | 环境混乱度:{final_state['chaos_level']}%")
    print("="*70 + "\n")


def main():
    print("="*80)
    print("【欢迎来到三体游戏：万年历辩论】(你有6次有效的互动机会，请在文王与伏羲之间寻找真理，为文明指明生存的道路...)")
    print("="*80)
    print("\n🎭 [前情提要] 朝歌大殿之上，乱纪元的狂风呼啸，殿堂外是无尽的漆黑，殿内幽幽的火光中，周文王与伏羲正为了万年历的真谛的争辩在回荡...\n")
    
    opening_wenwang = "孤以孤之双眼，历经羑里七年演卦，方知乾坤有常！孤已算出终极天机：一个时辰之后，太阳将从西方升起，开启为期一百年的恒纪元！大兴土木、春归大地之期已至。伏羲，你那冰冷的铁盘休要扰乱天机！"
    opening_fuxi = "荒谬！铜钱岂能测得星轨？据日晷精密几何推演，一个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少两百年！唯有立刻脱水、深藏地窖才是唯一的生路。学者（玩家），你来得正好！你且说说，究竟是他的玄学占卜灵验，还是我的几何算术严密？！"
    
    print(f"☯️【周文王】: {opening_wenwang}\n")
    print(f"📐【伏羲】: {opening_fuxi}")
    print("-" * 80)

    initial_state = {
        "messages": [
            AIMessage(content=opening_wenwang, name="周文王"),
            AIMessage(content=opening_fuxi, name="伏羲")
        ],
        "last_agent_output": "万年历尚未成型",
        "turn_count": 6,
        "empirical_authority": 20,
        "fuxi_authority": 20,
        "rational_certainty": 20,
        "chaos_level": 20,
        "game_over_reason": "",
        "final_ending_text": ""  # 初始化结局文本容器
    }
    
    current_state = initial_state
    
    while True:
        user_msg = input("\n[玩家发言] >>> ")
        if not user_msg.strip():
            continue
            
        current_state["messages"].append(HumanMessage(content=user_msg))
        
        events = game_engine.stream(current_state)
        for event in events:
            # 💡 核心修复：遍历 event 的键值对进行模糊匹配，防止由于节点命名（如 supervisor_node）导致无法正确拦截状态
            for node_name, node_output in event.items():
                if "supervisor" in node_name:
                    current_state.update(node_output)
                if "wenwang" in node_name:
                    current_state["last_agent_output"] = node_output.get("last_agent_output", "万年历尚未成型")
                if "fuxi" in node_name:
                    current_state["last_agent_output"] = node_output.get("last_agent_output", "万年历尚未成型")
                    
        # 只要导演判定游戏结束（无论是正常结束、混乱暴毙还是抉择完成）
        if current_state.get("game_over_reason"):
            render_final_ending(current_state)
            break

if __name__ == "__main__":
    main()