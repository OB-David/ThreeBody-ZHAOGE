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
        print(f"【唯一生路：文明的种子】\n你的理性度达到 {C}%。你成功指出了文王和伏羲的逻辑漏洞。文王和伏羲惊醒，全城疯狂咆哮：'脱水！脱水！' 你们化为皮卷存入地窖，文明得以保留。")
        return
    if A >= B:
        print(f"【最终抉择与审判 —— 经验的代价】这一刻，历史被定格。别无选择的纣王缓缓站起身，他俯瞰着满目疮痍的大地，最终采纳了周文王刚刚立下天誓的预测：『4个时辰之后，太阳将从西方升起，开启为期100年的恒纪元。』纣王深信不疑。他向全天下下达了神圣的旨令：停止一切防寒与避难准备，开仓放粮，全民离开避难所，开垦春耕，准备迎接百年的黄金盛世！朝歌城内，无数干枯的人形皮卷被投入浸泡池，人们在复活的欢呼声中涌上街头，载歌载舞。然而，时间一分一秒过去。天空中，冰冷的铅灰色云层骤然散去，但升起的并非温和的恒纪元旭日——地平线上，一个、两个、三个……三颗巨大而炽热的恒星同时跃出地平线！它们如滚烫的铜镜，并排悬挂在中天。这绝非温和的春天，而是毁灭性的“三日并凌空”！文王的万年历预测，在宇宙冰冷的物理规律面前沦为彻头彻尾的笑柄。极度强烈的光芒瞬间照亮了整个朝歌大殿。在这片白炽的光海中，文王手中的蓍草和铜钱无声地化为飞灰。在天地化为熔炉的刹那，整个文明在璀璨的极光中气化，化为宇宙间最原始的粒子，朝歌在光芒中归于永恒的沉寂。")
    else:
        print(f"【【最终抉择与审判 —— 数学的傲慢】整个国家彻底盲信了伏羲经过“精密几何推导”给出的最终计算：『4个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少200年。』在绝对理性的号召下，傲慢的学术界与朝廷下达了残酷而绝对的命令：为了应对持续200年的毁灭性酷热与严寒，所有活人必须立刻“脱水”，折叠成没有任何生命的皮卷，堆入地下最深、最阴凉的石窟地窖中，严禁任何人留在地表。朝歌城在机械的齿轮转动声中，瞬间变成了一座死寂的空城。只剩下巨大的青铜日晷，在荒凉的狂风中孤零零地指向天空。然而，宇宙跟自诩聪明的几何学家开了一个无比讽刺的玩笑。4个时辰之后，太阳准时升起。它温和、明亮、且距离适中。天空蔚蓝如洗，微风轻拂着大地。没有三日连珠，没有肆虐的乱纪元狂风——在经历了解构与无序后，恒纪元竟然奇迹般地降临了！大地披上了绿装，温暖的春天温柔地唤醒了漫山遍野的生机。但是，这生机勃勃的春天，却是一片死寂的春天。地窖深处，由于完全没有地表人员的看守与复苏（浸泡）仪式，所有脱水的皮卷在恒纪元长期的温暖和湿润中，无声无息地长满了青苔，最终化为了春泥的一部分。整个文明，在最期盼的春天里，陷入了永远无法醒来的沉睡。")


def main():
    print("="*80)
    print("【欢迎来到三体游戏：万年历辩论】(你有10次有效的互动机会，请在文王与伏羲之间寻找真理...)")
    print("="*80)
    print("\n🎭 [前情提要] 朝歌大殿之上，乱纪元的狂风呼啸。周文王与伏羲正为了万年历的真谛争得面红耳赤...\n")
    
    # 🌟 1. 精心设计、符合人设的硬核开场白
    opening_wenwang = "孤以孤之双眼，历经羑里七年演卦，方知乾坤有常！孤已算出终极天机：四个时辰之后，太阳将从西方升起，开启为期一百年的恒纪元！大兴土木、春归大地之期已至。伏羲，你那冰冷的铁盘休要扰乱天机！"
    opening_fuxi = "荒谬！铜钱岂能测得星轨？据日晷精密几何推演，四个时辰之后，升起的太阳将是三个连珠，乱纪元还将持续至少两百年！唯有立刻脱水、深藏地窖才是唯一的生路。学者（玩家），你来得正好！你且说说，究竟是他的玄学占卜灵验，还是我的几何算术严密？！"
    
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
                # print(f" [系统监测] 文王:{current_state['empirical_authority']} | 伏羲:{current_state['fuxi_authority']} | 理性:{current_state['rational_certainty']} | 混乱:{current_state['chaos_level']} | 剩余有效轮数:{current_state['turn_count']}")
            if "wenwang" in event:
                current_state["last_agent_output"] = event["wenwang"]["last_agent_output"]
            if "fuxi" in event:
                current_state["last_agent_output"] = event["fuxi"]["last_agent_output"]
                
        if current_state["game_over_reason"] or current_state["turn_count"] <= 0:
            render_final_ending(current_state)
            break

if __name__ == "__main__":
    main()