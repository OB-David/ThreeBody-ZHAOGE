# main.py
import os
from dotenv import load_dotenv

# 强行初始化环境变量
load_dotenv()

if not os.getenv("DEEPSEEK_API_KEY") or not os.getenv("QWEN_API_KEY"):
    print("\n❌ [启动失败] 致命错误：检测到 .env 文件未正确配置或未找到！")
    exit(1)

from graph import game_engine
from langchain_core.messages import HumanMessage, AIMessage

# 移过来或者保留你的 render_final_ending 逻辑
def render_final_ending(final_state):
    print("\n" + "="*20 + " 最终抉择与审判 " + "="*20)
    A = final_state["empirical_authority"]
    B = final_state["fuxi_authority"]
    C = final_state["rational_certainty"]
    D = final_state["chaos_level"]
    last_prediction = final_state["last_agent_output"]

    if final_state["game_over_reason"] == "chaos_death":
        print(f"【中途剧终：乱刃分尸】\n大殿混乱度达 {D}%！你的言论彻底激怒了所有人。伏羲怒斥你是妖孽，文王叹息你亵渎天意，乱刀之下，你血染沙盘。")
        return
    if C > A and C > B and C >= 50:
        print(f"【唯一生路：文明的种子】\n你的理性度达到 {C}%。你成功剥离了玄学和僵化的数学，指出三体无解。文王和伏羲惊醒，全城疯狂咆哮：'脱水！脱水！' 你们化为皮卷存入地窖，文明得以保留。")
        return
    if A >= B:
        print(f"【毁灭结局：经验的代价】\n最终文王权威度高达 {A}%。纣王采纳了文王刚刚推演的预测。然而，三个太阳同时凌空，荒谬的预测沦为笑柄。烈火瞬间吞噬了朝歌。")
    else:
        print(f"【毁灭结局：数学的傲慢】\n最终伏羲权威度高达 {B}%。整个国家盲信了伏羲最后的计算。然而，太阳再也没有升起，极寒乱纪元降临，整个文明被冻成了冰雕。")


def main():
    print("="*80)
    print("【欢迎来到三体游戏：万年历辩论】(你有10次有效的互动机会，请在文王与伏羲之间寻找真理...)")
    print("="*80)
    print("\n🎭 [前情提要] 朝歌大殿之上，乱纪元的狂风呼啸。周文王与伏羲正为了万年历的真谛争得面红耳赤...\n")
    
    # 🌟 1. 精心设计、符合人设的硬核开场白
    opening_wenwang = "孤以孤之双眼，历经羑里七年演卦，方知乾坤有常！此乃百年恒纪元之兆，当大兴土木！伏羲，你那冰冷的铁盘休要扰乱天机！"
    opening_fuxi = "荒谬！铜钱岂能测得星轨？完美的同心圆轨道才是宇宙至美之理！学者（玩家），你来得正好！你且说说，究竟是他的玄学占卜灵验，还是我的几何算术严密？！"
    
    # 漂亮的开场打印
    print(f"☯️【周文王】: {opening_wenwang}\n")
    print(f"📐【伏羲】: {opening_fuxi}")
    print("-" * 80)

    # 🌟 2. 注入全局初始化状态（让大导演能看到这段开场记忆）
    initial_state = {
        "messages": [
            AIMessage(content=opening_wenwang, name="周文王"),
            AIMessage(content=opening_fuxi, name="伏羲")
        ],
        "last_agent_output": "万年历尚未成型",
        "turn_count": 10,
        "empirical_authority": 20,
        "fuxi_authority": 20,
        "rational_certainty": 20,
        "chaos_level": 20,
        "game_over_reason": ""
    }
    
    current_state = initial_state
    
    while True:
        user_msg = input("\n[玩家发言] >>> ")
        if not user_msg.strip():
            continue
            
        current_state["messages"].append(HumanMessage(content=user_msg))
        
        events = game_engine.stream(current_state)
        for event in events:
            if "supervisor" in event:
                current_state.update(event["supervisor"])
                print(f" [系统监测] 文王:{current_state['empirical_authority']} | 伏羲:{current_state['fuxi_authority']} | 理性:{current_state['rational_certainty']} | 混乱:{current_state['chaos_level']} | 剩余有效轮数:{current_state['turn_count']}")
            if "wenwang" in event:
                current_state["last_agent_output"] = event["wenwang"]["last_agent_output"]
            if "fuxi" in event:
                current_state["last_agent_output"] = event["fuxi"]["last_agent_output"]
                
        if current_state["game_over_reason"] or current_state["turn_count"] <= 0:
            render_final_ending(current_state)
            break

if __name__ == "__main__":
    main()