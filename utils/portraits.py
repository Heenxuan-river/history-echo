"""人物画像生成器 — 朝代配色圆形肖像"""
import base64

DYNASTY_COLORS = {
    "先秦": "#8B4513", "秦": "#2F4F4F", "汉": "#8B0000",
    "三国": "#B8860B", "南北朝": "#6A5ACD", "隋": "#CD5C5C",
    "唐": "#DC143C", "宋": "#2E8B57", "元": "#4B0082",
    "明": "#CD853F", "清": "#4169E1", "民国": "#708090",
}

ROLE_ICONS = {
    "帝王": "👑", "名将": "⚔️", "文豪": "📝", "思想家": "☯️",
    "科学家": "🔬", "医学家": "💊", "艺术家": "🎨", "教育家": "🎓",
    "政治家": "🏛️", "革命家": "✊", "探险家": "🧭", "义士": "🗡️",
    "佳人": "🌺", "高僧": "🪷",
}


def infer_role(char_data):
    if char_data.get("role"):
        return char_data["role"]
    desc = (char_data.get("description", "") + " " + " ".join(char_data.get("personality", [])))
    ach = " ".join(char_data.get("achievements", []))
    if "皇帝" in ach or "开国" in ach or "建立" in ach:
        return "帝王"
    if "名将" in desc or "将军" in desc or "军事" in desc or "北伐" in ach:
        return "名将"
    if "诗人" in desc or "词人" in desc or "文学" in desc:
        return "文豪"
    if "思想" in desc or "学派" in desc or "哲学" in desc:
        return "思想家"
    if "医学" in desc or "医" in desc:
        return "医学家"
    if "画" in desc or "书法" in desc or "才子" in desc:
        return "艺术家"
    if "教育" in desc or "大学" in desc:
        return "教育家"
    if "革命" in desc or "变法" in desc:
        return "革命家"
    if "航海" in desc or "探险" in desc or "西域" in desc:
        return "探险家"
    if "僧" in desc or "佛" in desc or "取经" in desc:
        return "高僧"
    return "人物"


def generate_portrait(name, dynasty, role=None, size=80):
    """生成朝代配色圆形肖像"""
    bg = DYNASTY_COLORS.get(dynasty, "#666")
    icon = ROLE_ICONS.get(role, "🧑") if role else "🧑"
    char = name[0] if name else "?"
    r = size // 2

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">'
        '<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="white" stroke-width="3"/>'
        '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>'
        '<text x="%d" y="%d" text-anchor="middle" font-size="%d" fill="rgba(255,255,255,0.9)">%s</text>'
        '<text x="%d" y="%d" text-anchor="middle" dy=".35em" fill="white" font-size="%d" font-weight="bold" font-family="Microsoft YaHei, SimHei, sans-serif">%s</text>'
        '</svg>'
    ) % (
        size, size,
        r, r, r-3, bg,
        r, r, r-8,
        r, r-size//6, size//6, icon,
        r, r+size//10, size//3, char,
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def generate_portrait_card(name, dynasty, role=None, description=""):
    """大尺寸画像（用于对话页头部）"""
    return generate_portrait(name, dynasty, role, size=120)
