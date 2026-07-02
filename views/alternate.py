"""'如果改变' — 三阶式：选事件 → 选人物/因素 → 推演"""
import streamlit as st
from core.alternate_world import (
    get_events_with_characters,
    get_factors_for_event,
    generate_divergence,
    generate_choices,
    generate_next_scene,
    generate_impact,
)
from utils.portraits import generate_portrait, infer_role


def show():
    st.title("🔄 如果历史改变")
    st.markdown(
        '<p style="color:#8B7355;font-size:1.05rem;margin-top:-0.5rem;">'
        "选一个历史事件 → 改变其中的关键人物或因素 → 看历史如何改写</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="background:#FEF9E7;border:1px solid #F0E8D0;border-radius:8px;'
        'padding:0.5rem 1rem;font-size:0.85rem;color:#8B7355;margin-bottom:0.8rem;">'
        "💡 每个历史事件由多种因素推动。<b>改变其中一个人物或一个因素</b>，推演历史的另一种可能"
        "</div>",
        unsafe_allow_html=True,
    )

    if "alt_story_active" not in st.session_state:
        st.session_state["alt_story_active"] = False

    if not st.session_state["alt_story_active"]:
        show_event_selection()
    else:
        show_story_interface()


# ═══════════════════════════════════════════
# 第一步：选事件
# ═══════════════════════════════════════════
def show_event_selection():
    events = get_events_with_characters()
    dynasty_order = ["先秦", "秦", "汉", "三国", "南北朝", "隋", "唐", "宋", "元", "明", "清", "民国"]
    grouped = {}
    for e in events:
        grouped.setdefault(e["dynasty"], []).append(e)

    col1, col2 = st.columns([3, 2.5])

    with col1:
        st.markdown(
            '<div style="font-size:1rem;font-weight:600;color:#2C1810;margin-bottom:0.8rem;">'
            "📌 第一步：选择一个历史事件</div>",
            unsafe_allow_html=True,
        )

        for dynasty in dynasty_order:
            if dynasty not in grouped:
                continue
            with st.expander(f"▸ {dynasty}（{len(grouped[dynasty])}个事件）", expanded=False):
                for evt in grouped[dynasty]:
                    char_names = "、".join([c["name"] for c in evt["characters"][:3]])
                    help_text = evt["description"][:80]
                    if char_names:
                        help_text += f" | 人物：{char_names}"
                    if st.button(
                        f"📖 {evt['name']}",
                        key=f"evt_{evt['id']}",
                        use_container_width=True,
                        help=help_text,
                    ):
                        st.session_state["selected_event"] = evt
                        st.session_state["alt_change_mode"] = True
                        st.rerun()

    with col2:
        if st.session_state.get("alt_change_mode"):
            render_change_and_result()
        else:
            render_change_selection_hint()


# ═══════════════════════════════════════════
# 第二步：选人物或因素（直接出结果）
# ═══════════════════════════════════════════
def render_change_selection_hint():
    st.markdown(
        '<div style="text-align:center;padding:3rem 0;color:#8B7355;">'
        '<div style="font-size:2.5rem;margin-bottom:0.5rem;">👈</div>'
        "<div style='font-size:1rem;color:#5C3A28;'>先选一个历史事件</div>"
        "<div style='font-size:0.85rem;margin-top:0.3rem;'>"
        "然后选择改变其中的<b>人物</b>或<b>因素</b></div></div>",
        unsafe_allow_html=True,
    )

def render_change_and_result():
    if "selected_event" not in st.session_state:
        return
    event = st.session_state["selected_event"]
    year_str = f"公元前{abs(event['year'])}年" if event["year"] < 0 else f"{event['year']}年"
    type_map = {"war": "⚔️战争", "politics": "👑政治", "culture": "📚文化", "reform": "🛠️改革"}

    st.markdown(
        f'<div style="margin-bottom:1rem;">'
        f'<div style="display:flex;align-items:center;gap:0.5rem;">'
        f'<span style="font-size:1.1rem;font-weight:700;color:#2C1810;">{event["name"]}</span>'
        f'<span style="font-size:0.7rem;color:#8B7355;background:#F0E8DE;padding:0.1rem 0.5rem;border-radius:8px;">'
        f'{type_map.get(event["type"], event["type"])}</span></div>'
        f'<div style="font-size:0.8rem;color:#8B7355;">{year_str} · {event["dynasty"]}</div>'
        f'<div style="font-size:0.8rem;color:#5C3A28;margin-top:0.3rem;">{event["description"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("← 返回选其他", use_container_width=True, key="back_to_events"):
        st.session_state.pop("alt_change_mode", None)
        st.session_state.pop("selected_event", None)
        st.rerun()

    st.markdown('<div style="font-size:0.9rem;font-weight:600;color:#2C1810;">👤 改变人物</div>', unsafe_allow_html=True)
    if event["characters"]:
        for c in event["characters"]:
            if st.button(f"🔄 {c['name']}", key=f"ch_{c['id']}", use_container_width=True):
                divergence = generate_divergence(event, "character", c["name"])
                start_story(divergence)
                st.rerun()
    else:
        st.markdown('<div style="font-size:0.8rem;color:#8B7355;">暂无关联人物</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.9rem;font-weight:600;color:#2C1810;margin-top:0.8rem;">🔧 改变因素</div>', unsafe_allow_html=True)
    factors = get_factors_for_event(event["type"])
    for f_name, f_desc in factors:
        if st.button(f"⚡ {f_name}", key=f"ft_{f_name}", use_container_width=True, help=f_desc):
            divergence = generate_divergence(event, "factor", f_name, f_desc)
            start_story(divergence)
            st.rerun()


# ═══════════════════════════════════════════
# 第三步：互动叙事
# ═══════════════════════════════════════════
def start_story(divergence):
    st.session_state["alt_story_active"] = True
    st.session_state["alt_title"] = divergence["title"]
    st.session_state["alt_history"] = [{"type": "scene", "content": divergence["scene"]}]
    st.session_state["alt_stage"] = 1
    st.session_state["alt_choices"] = generate_choices(0)


def show_story_interface():
    title = st.session_state.get("alt_title", "平行历史")

    # 顶部导航
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'padding:0.6rem 1rem;background:#2C1810;border-radius:10px;margin-bottom:0.8rem;">'
        f'<div style="display:flex;align-items:center;gap:0.5rem;overflow:hidden;">'
        f'<span style="font-size:1.2rem;">📖</span>'
        f'<span style="color:#F5E6D3;font-weight:600;font-size:0.9rem;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;max-width:350px;">{title}</span></div>'
        f'<span style="color:rgba(245,230,211,0.6);font-size:0.8rem;">第{st.session_state["alt_stage"]}幕</span></div>',
        unsafe_allow_html=True,
    )

    # 进度
    p = min(st.session_state["alt_stage"], 6)
    bar = "".join(
        f'<div style="flex:1;height:3px;border-radius:2px;background:{"#D4A574" if i<p else "#E8DDD0"};transition:all 0.3s;"></div>'
        for i in range(6)
    )
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.3rem;margin-bottom:0.8rem;">{bar}<span style="font-size:0.7rem;color:#8B7355;">{p}/6</span></div>', unsafe_allow_html=True)

    # 叙事
    st.markdown('<div class="card" style="padding:1.2rem;">', unsafe_allow_html=True)
    for h in st.session_state["alt_history"]:
        if h["type"] == "scene":
            st.markdown(f'<div style="font-size:1rem;line-height:1.8;color:#2C1810;">{h["content"]}</div>', unsafe_allow_html=True)
        elif h["type"] == "choice":
            st.markdown(f'<div style="text-align:center;margin:0.3rem 0;"><span style="background:#F0E8DE;color:#5C3A28;padding:0.15rem 1rem;border-radius:12px;font-size:0.8rem;">➤ 你选择：{h["content"]}</span></div>', unsafe_allow_html=True)
        elif h["type"] == "impact":
            lines = h["content"].split("\n")
            html = '<div style="margin:0.5rem 0;padding:0.8rem 1rem;background:#FEF9E7;border:1px solid #F0E8D0;border-radius:8px;font-size:0.85rem;color:#5C3A28;"><div style="font-weight:600;color:#2C1810;margin-bottom:0.3rem;">📋 影响结算</div>'
            for line in lines:
                if line.strip():
                    html += f'<div style="margin:0.15rem 0;line-height:1.5;">{line}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr style="margin:1rem 0;border-color:#D4A574;opacity:0.25;">', unsafe_allow_html=True)

    # 选项
    if st.session_state["alt_choices"]:
        st.markdown('<div style="font-weight:600;color:#2C1810;text-align:center;margin-bottom:0.6rem;">👇 接下来你怎么做？</div>', unsafe_allow_html=True)
        for i, choice in enumerate(st.session_state["alt_choices"]):
            st.markdown(
                f'<div style="background:#FAF7F3;border:1px solid #E8DDD0;border-radius:8px;'
                f'padding:0.5rem 0.8rem;margin-bottom:0.3rem;border-left:3px solid #D4A574;'
                f'font-size:0.9rem;color:#2C1810;">{choice["text"]}'
                f'<span style="font-size:0.7rem;color:#8B7355;margin-left:0.5rem;">{choice.get("desc","")}</span></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"选择", key=f"ac_{st.session_state['alt_stage']}_{i}", use_container_width=False):
                make_choice(choice["text"])
                st.rerun()

    # 回退 / 重选
    c1, c2 = st.columns(2)
    with c1:
        if len(st.session_state["alt_history"]) > 1:
            if st.button("↩ 回退一步", use_container_width=True):
                if len(st.session_state["alt_history"]) >= 2:
                    st.session_state["alt_history"] = st.session_state["alt_history"][:-2]
                    st.session_state["alt_stage"] = max(st.session_state["alt_stage"] - 1, 1)
                    st.session_state["alt_choices"] = generate_choices(st.session_state["alt_stage"])
                st.rerun()
    with c2:
        if st.button("🔄 重新选择", use_container_width=True):
            reset_story()
            st.rerun()


def make_choice(text):
    st.session_state["alt_history"].append({"type": "choice", "content": text})
    prev = [
        {"step": i + 1, "choice": h["content"]}
        for i, h in enumerate(st.session_state["alt_history"]) if h["type"] == "choice"
    ]
    next_scene = generate_next_scene(text, prev)
    st.session_state["alt_history"].append({"type": "scene", "content": next_scene})
    impact = generate_impact(text, prev)
    st.session_state["alt_history"].append({"type": "impact", "content": impact})
    st.session_state["alt_stage"] += 1

    if st.session_state["alt_stage"] < 6:
        st.session_state["alt_choices"] = generate_choices(st.session_state["alt_stage"])
    else:
        st.session_state["alt_history"].append({
            "type": "scene",
            "content": "✨ 历史的分岔路走到了尽头。你的选择塑造了一条全新的世界线。点击「重新选择」探索另一条历史道路。",
        })
        st.session_state["alt_choices"] = []


def reset_story():
    for k in ["alt_story_active", "alt_title", "alt_history", "alt_choices", "alt_stage"]:
        if k in st.session_state:
            st.session_state[k] = [] if k in ["alt_history", "alt_choices"] else (0 if k == "alt_stage" else (False if k == "alt_story_active" else ""))
    st.session_state["alt_story_active"] = False
    if "selected_event" in st.session_state:
        del st.session_state["selected_event"]