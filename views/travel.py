"""穿越助手页面"""
import streamlit as st
from core.travel_guide import get_survival_guide, identify_dynasty

DYNASTY_EMOJIS = {
    "先秦": "☯️", "秦": "⚔️", "汉": "🐉", "三国": "🔥",
    "唐": "🌸", "宋": "🏮", "元": "🐎", "明": "🏯", "清": "🎐", "民国": "📰",
}


def show():
    st.title("⏳ 穿越助手")
    st.markdown(
        '<p style="color:#8B7355;font-size:1.05rem;margin-top:-0.5rem;">'
        "输入年份和地点，生成专属穿越生存指南</p>",
        unsafe_allow_html=True,
    )

    # 初始化
    if "travel_year" not in st.session_state:
        st.session_state["travel_year"] = 626
    if "travel_location" not in st.session_state:
        st.session_state["travel_location"] = ""

    mode = st.radio("模式", ["手动输入", "快捷穿越"], horizontal=True, label_visibility="collapsed", key="travel_mode")

    if mode == "手动输入":
        show_manual()
    else:
        show_quick()


def show_manual():
    year = st.number_input(
        "年份",
        value=st.session_state["travel_year"],
        min_value=-3000, max_value=1950, step=1,
        label_visibility="collapsed",
    )
    st.session_state["travel_year"] = year

    loc = st.text_input(
        "地点",
        value=st.session_state["travel_location"],
        placeholder="如 长安、开封、杭州…",
        label_visibility="collapsed",
    )
    st.session_state["travel_location"] = loc

    dynasty = identify_dynasty(year)
    emoji = DYNASTY_EMOJIS.get(dynasty, "⏳")
    yd = f"公元前{abs(year)}年" if year < 0 else f"{year}年"

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.8rem;padding:0.6rem 1rem;'
        f'background:#FAF7F3;border-radius:10px;border:1px solid #E8DDD0;">'
        f'<span style="font-size:1.8rem;">{emoji}</span>'
        f'<div><div style="font-weight:700;font-size:1.1rem;color:#2C1810;">{yd}</div>'
        f'<div style="font-size:0.85rem;color:#8B7355;">{dynasty}</div></div></div>',
        unsafe_allow_html=True,
    )

    if st.button("🛡️ 生成穿越生存指南", type="primary", use_container_width=True):
        guide = get_survival_guide(year, loc)
        st.session_state["travel_guide"] = guide
        st.session_state["guide_year"] = year
        st.session_state["guide_dynasty"] = dynasty
    show_guide()


def show_quick():
    clicked = False
    st.markdown("**点击朝代直接生成指南：**")
    quick_jumps = [
        ("先秦", -500, "洛邑"), ("秦朝", -210, "咸阳"),
        ("汉朝", -100, "长安"), ("三国", 208, "赤壁"),
        ("晋朝", 300, "建康"), ("南北朝", 500, "建康"),
        ("隋朝", 600, "大兴"), ("盛唐", 742, "长安"),
        ("北宋", 1069, "开封"), ("南宋", 1200, "临安"),
        ("元朝", 1290, "大都"), ("明朝", 1405, "南京"),
        ("清朝", 1700, "北京"), ("晚清", 1898, "北京"),
        ("民国", 1919, "北京"),
    ]
    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.3rem;">',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for i, (label, y, loc) in enumerate(quick_jumps):
        emoji = DYNASTY_EMOJIS.get(identify_dynasty(y), "⏳")
        with cols[i % 3]:
            if st.button(f"{emoji} {label}", key=f"q_{y}", use_container_width=True):
                clicked = True
                dynasty = identify_dynasty(y)
                guide = get_survival_guide(y, loc)
                ys = f"公元前{abs(y)}年" if y < 0 else f"{y}年"
                emj = DYNASTY_EMOJIS.get(dynasty, "⏳")
                st.markdown("---")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;">'
                    f'<span style="font-size:2.5rem;">{emj}</span>'
                    f'<div><div style="font-size:1.2rem;font-weight:700;color:#2C1810;">🏛️ {ys} · {dynasty}</div>'
                    f'<div style="font-size:0.85rem;color:#8B7355;">穿越生存指南</div></div></div>',
                    unsafe_allow_html=True,
                )
                for section in parse_guide_sections(guide):
                    st.markdown(section, unsafe_allow_html=True)

    if not clicked:
        show_guide()


def show_guide():
    if "travel_guide" not in st.session_state or not st.session_state["travel_guide"]:
        return

    gy = st.session_state["guide_year"]
    gd = st.session_state["guide_dynasty"]
    emoji = DYNASTY_EMOJIS.get(gd, "⏳")
    ys = f"公元前{abs(gy)}年" if gy < 0 else f"{gy}年"

    st.markdown("---")
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;">'
        f'<span style="font-size:2.5rem;">{emoji}</span>'
        f'<div><div style="font-size:1.2rem;font-weight:700;color:#2C1810;">🏛️ {ys} · {gd}</div>'
        f'<div style="font-size:0.85rem;color:#8B7355;">穿越生存指南</div></div></div>',
        unsafe_allow_html=True,
    )

    for section in parse_guide_sections(st.session_state["travel_guide"]):
        st.markdown(section, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("💡 配置 LLM API Key 后，穿越指南会更生动详细。目前为离线数据模式。")


def parse_guide_sections(text):
    lines = text.split("\n")
    sections = []
    cur = ""
    for line in lines:
        if line.startswith("---"):
            continue
        if line.startswith("## "):
            if cur:
                sections.append(cur)
            t = line.replace("## ", "").replace("**", "")
            cur = f'<div style="margin-top:0.8rem;padding:1rem;background:#FAF7F3;border-radius:10px;border:1px solid #E8DDD0;"><div style="font-size:1rem;font-weight:600;color:#2C1810;margin-bottom:0.5rem;">{t}</div>'
        elif line.startswith("- **"):
            parts = line.replace("- **", "").split("**：")
            if len(parts) == 2:
                cur += f'<div style="display:flex;gap:0.5rem;padding:0.2rem 0;font-size:0.9rem;"><span style="font-weight:600;color:#5C3A28;min-width:60px;">{parts[0]}</span><span style="color:#2C1810;">{parts[1]}</span></div>'
            else:
                cur += f'<div style="padding:0.15rem 0;font-size:0.9rem;">• {line.strip("- ")}</div>'
        elif line.strip():
            if not cur:
                cur = '<div style="margin-top:0.8rem;padding:1rem;background:#FAF7F3;border-radius:10px;border:1px solid #E8DDD0;">'
            cur += f'<div style="font-size:0.9rem;line-height:1.7;color:#2C1810;">{line}</div>'
    if cur:
        if not cur.endswith("</div>"):
            cur += "</div>"
        sections.append(cur)
    return sections if sections else [f"<div>{text}</div>"]