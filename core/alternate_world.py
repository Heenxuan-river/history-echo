"""'如果改变' 互动叙事引擎 — 事件·人物·因素 三阶模式"""
import random
from utils.llm import chat
from utils.data_loader import load_events, get_character_by_id

# 因素模板（按事件类型）
FACTORS_BY_TYPE = {
    "war": [
        ("将领决策", "如果当时的指挥官做出了不同的战术选择"),
        ("军力对比", "如果双方的兵力部署发生了变化"),
        ("天气条件", "如果当时的天气状况截然不同"),
        ("情报信息", "如果关键情报被截获或误判"),
        ("后勤补给", "如果补给线被切断或畅通"),
        ("援军到达", "如果援军提前或延迟到达"),
    ],
    "politics": [
        ("继承人选择", "如果继承人选发生了改变"),
        ("外交策略", "如果采取了不同的外交方针"),
        ("法令颁布", "如果这条法令被修改或否决"),
        ("权力制衡", "如果朝堂的权力格局不同"),
        ("民意走向", "如果民间舆论站在了另一边"),
    ],
    "reform": [
        ("推行力度", "如果改革采取了更激进或更温和的方式"),
        ("反对派态度", "如果反对势力被提前安抚或压制"),
        ("皇帝支持度", "如果最高决策者的支持没有动摇"),
        ("执行方式", "如果改革的具体执行方法不同"),
        ("受益群体", "如果改革的利益分配方式改变"),
    ],
    "culture": [
        ("思想传播", "如果这种思想被更早或更广泛地传播"),
        ("教育制度", "如果教育体系采取了不同的方向"),
        ("文化政策", "如果文化政策更加开放或保守"),
        ("人才培养", "如果人才选拔机制发生了改变"),
    ],
}

FACTORS_FALLBACK = [
    ("决策时机", "如果关键决策的时机提前或推迟"),
    ("信息传递", "如果关键信息被准确传达或被误解"),
    ("个人意志", "如果当事人的意志和决心不同"),
    ("外部环境", "如果外部环境发生了意想不到的变化"),
]

CHOICE_TEMPLATES = {
    "军事": [
        {"text": "全力北伐，趁胜追击", "desc": "趁敌军立足未稳，主动出击"},
        {"text": "固守待变，以逸待劳", "desc": "巩固防线，等待敌方内部分裂"},
        {"text": "联合盟友，合纵抗敌", "desc": "派遣使者联络各方势力共同对抗"},
    ],
    "政治": [
        {"text": "推行新政，锐意改革", "desc": "大刀阔斧进行制度改革"},
        {"text": "维持现状，逐步改良", "desc": "稳定压倒一切，小步慢走"},
        {"text": "广纳贤才，开放言路", "desc": "招募人才，听取各方意见"},
    ],
    "文化": [
        {"text": "推广教育，开启民智", "desc": "大兴学校，传播知识"},
        {"text": "兼容并包，百花齐放", "desc": "允许各种思想和文化自由发展"},
        {"text": "整理典籍，传承文明", "desc": "系统地整理和保存文化遗产"},
    ],
    "外交": [
        {"text": "开放通商，交流互鉴", "desc": "打开国门，与他国进行贸易往来"},
        {"text": "闭关自守，保持独立", "desc": "减少外部影响，专注内部发展"},
        {"text": "远交近攻，分化瓦解", "desc": "结交远方势力，打击邻近威胁"},
    ],
}


def get_events_with_characters():
    """获取事件列表，附带参与人物"""
    events = load_events()
    result = []
    for e in events:
        chars = []
        for cid in e.get("involved_characters", []):
            c = get_character_by_id(cid)
            if c:
                chars.append({"id": cid, "name": c["name"]})
        result.append({
            "id": e["id"], "name": e["name"], "year": e["year"],
            "dynasty": e["dynasty"], "type": e["type"],
            "description": e["description"], "characters": chars,
        })
    return result


def get_factors_for_event(event_type):
    """根据事件类型获取可选因素"""
    factors = FACTORS_BY_TYPE.get(event_type, [])
    # 混合一个通用因素
    all_factors = factors + FACTORS_FALLBACK
    random.shuffle(all_factors)
    return all_factors[:4]


def generate_divergence(event, target_type, target_name, factor_name=""):
    """
    生成改变推演开场
    target_type: "character" 或 "factor"
    target_name: 人物名 或 因素名
    factor_name: 因素描述（仅 factor 类型时使用）
    """
    if target_type == "character":
        prompt = (
            f"历史事件：{event['name']}（{event['description'][:100]}）\n"
            f"关键人物：{target_name}在该事件中扮演了重要角色。\n\n"
            f"请创作一个「如果改变历史」的开场情景：\n"
            f"在{event['name']}中，{target_name}做出了一个与史实完全不同的选择。\n\n"
            f"用150字以内生动描述这个改变发生后的第一个画面，像小说开头一样有场景感。"
        )
        title = f"如果{event['name']}中{target_name}改变了"
    else:
        prompt = (
            f"历史事件：{event['name']}（{event['description'][:100]}）\n"
            f"关键因素：{target_name}\n"
            f"具体改变：{factor_name}\n\n"
            f"请创作一个「如果改变历史」的开场情景：\n"
            f"在{event['name']}中，{target_name}这一因素发生了改变——{factor_name}。\n\n"
            f"用150字以内生动描述这个改变发生后的第一个画面，像小说开头一样有场景感。"
        )
        title = f"如果{event['name']}的{target_name}改变了"

    if llm_result := chat("你是一个历史推演大师，擅长生动叙事。注意：对用户使用中性称呼，不要用兄弟老铁等口语。", prompt):
        return {"title": title, "scene": llm_result}

    # 模拟模式
    scenes = [
        f"在{event['name']}的关键时刻，{target_name}的走向悄然偏离了历史的轨道。没有人意识到这个微小的变化将如何掀起滔天巨浪……",
        f"历史在这里分岔了。{target_name}的不同选择，让整个{event['name']}的面貌开始变得陌生。新的可能性正在展开……",
        f"当{target_name}发生改变的那一刻，所有人都还在按部就班。但他们很快就会发现，世界已经不再是从前的那个世界了……",
    ]
    return {"title": title, "scene": random.choice(scenes)}


def generate_choices(stage_index=0):
    categories = list(CHOICE_TEMPLATES.keys())
    cat = categories[stage_index % len(categories)]
    choices = CHOICE_TEMPLATES[cat].copy()
    random.shuffle(choices)
    return choices


def generate_impact(choice_text, history):
    total = len(history) + 1
    prompt = (
        f"历史推演第{total}轮，用户选择了：{choice_text}\n"
        f"请给出具体的影响结算，格式如下（每条1-2句话）：\n"
        f"📊 国力影响：国力、经济、军事的具体变化\n"
        f"👥 民心向背：百姓和朝臣的反应\n"
        f"🌏 天下大势：周边势力和全局格局的变化\n"
        f"🎯 历史走向：后续发展的可能方向"
    )
    if llm_result := chat("你是历史推演结算系统，用具体细节描述每次选择的影响。", prompt):
        return llm_result
    impacts = [
        "📊 国力影响：国库消耗加剧，军力得到加强但民生资源被挤占。\n👥 民心向背：百姓对新政持观望态度，朝中改革派与守旧派对立加剧。\n🌏 天下大势：周边势力趁机调整策略，边境出现新的压力点。\n🎯 历史走向：中长期看，这一选择可能埋下变局的种子。",
        "📊 国力影响：中央集权进一步加强，地方财政收入增加。\n👥 民心向背：短期内民间反应平稳，但长期可能积累矛盾。\n🌏 天下大势：外交格局保持稳定，但盟友关系出现微妙变化。\n🎯 历史走向：这条路线趋向于保守稳健，短期内风险较低。",
        "📊 国力影响：军费开支大幅增加，但战略纵深得到扩展。\n👥 民心向背：主战派得到鼓舞，厌战情绪也在暗中滋生。\n🌏 天下大势：敌对方开始重新评估实力对比，和谈可能性降低。\n🎯 历史走向：冲突风险升级，但若成功将获得巨大战略收益。",
    ]
    return impacts[total % len(impacts)]


def generate_next_scene(choice_text, history):
    history_str = "；".join([f"第{h['step']}步选了「{h['choice']}」" for h in history])
    prompt = f"历史推演已进行{len(history)+1}步：{history_str}\n用户选了：{choice_text}\n用150字以内生动描述这个选择带来的历史发展，有画面感。"
    if llm_result := chat("你是一个历史推演大师，擅长生动叙事。注意：对用户使用中性称呼，不要用兄弟老铁等口语。", prompt):
        return llm_result
    outcomes = [
        "这个决定在朝野引起巨大反响。支持者叫好，反对者暗流涌动。远方的边疆传来了新的消息……",
        "随着这个决定实施，局势开始朝意想不到的方向发展。朝堂上的权力格局在悄然改变……",
        "这个选择改变了各方势力的平衡。有人欢喜有人忧，历史的洪流在这一刻重新塑造了自己的河道……",
    ]
    return outcomes[len(history) % len(outcomes)]