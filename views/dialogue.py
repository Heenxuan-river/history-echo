"""历史人物对话页面 — 带人物画像"""
import streamlit as st
from utils.data_loader import load_characters, get_dynasties
from core.character_ai import generate_reply, get_suggested_questions
from utils.portraits import generate_portrait, generate_portrait_card, infer_role
from utils.chat_store import save_chat, load_chat, delete_chat


def get_role_emoji(c):
    """获取角色图标"""
    role = c.get("role") or infer_role(c)
    from utils.portraits import ROLE_ICONS
    return ROLE_ICONS.get(role, "🧑")


def show():
    st.title("💬 与历史人物对话")
    st.markdown(
        '<p style="color:#8B7355;font-size:1.05rem;margin-top:-0.5rem;">'
        "选择一个历史人物，开始一场跨越时空的对话</p>",
        unsafe_allow_html=True,
    )

    characters = load_characters()
    dynasty_groups = {}
    for c in characters:
        dynasty_groups.setdefault(c["dynasty"], []).append(c)

    col_left, col_right = st.columns([1, 2.2])

    with col_left:
        render_character_panel(dynasty_groups, characters)
    with col_right:
        char_id = st.session_state.get("selected_char_id")
        if char_id:
            char = next((c for c in characters if c["id"] == char_id), None)
            if char:
                render_chat_area(char)
        else:
            st.info("👈 先在左侧选择一位历史人物开始对话")


def render_character_panel(dynasty_groups, characters):
    st.markdown('<div class="card" style="padding:1rem;">', unsafe_allow_html=True)

    ordered = [d for d in get_dynasties() if d in dynasty_groups]
    selected_dynasty = st.selectbox(
        "筛选朝代",
        ordered,
        key="dialogue_dynasty",
        label_visibility="collapsed",
    )

    for c in dynasty_groups[selected_dynasty]:
        is_active = st.session_state.get("selected_char_id") == c["id"]
        role = c.get("role") or infer_role(c)
        portrait = generate_portrait(c["name"], c["dynasty"], role, size=50)

        border = "2px solid #D4A574" if is_active else "1px solid #E8DDD0"
        bg = "rgba(212,165,116,0.1)" if is_active else "transparent"

        st.markdown(
            f'<div style="padding:0.5rem 0.6rem;margin-bottom:0.3rem;border-radius:8px;'
            f'border:{border};background:{bg};cursor:pointer;'
            f'display:flex;align-items:center;gap:0.6rem;transition:all 0.15s;">'
            f'<img src="{portrait}" style="width:40px;height:40px;border-radius:50%;flex-shrink:0;">'
            f'<div style="min-width:0;">'
            f'<div style="font-weight:600;font-size:0.85rem;color:#2C1810;">{c["name"]}</div>'
            f'<div style="font-size:0.7rem;color:#8B7355;">{c.get("description", "")[:25]}…</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if st.button(
            c["name"],
            key=f"cs_{c['id']}",
            help=c.get("description", ""),
            use_container_width=True,
        ):
            if st.session_state.get("selected_char_id") != c["id"]:
                st.session_state["selected_char_id"] = c["id"]
                st.session_state[f"chat_{c['id']}"] = load_chat(c["id"])
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # 人物简介卡
    char_id = st.session_state.get("selected_char_id")
    if char_id:
        c = next((x for x in characters if x["id"] == char_id), None)
        if c:
            role = c.get("role") or infer_role(c)
            portrait = generate_portrait_card(c["name"], c["dynasty"], role)
            tags = "".join(
                f'<span style="display:inline-block;background:#F0E8DE;color:#5C3A28;'
                f'font-size:0.65rem;padding:0.1rem 0.5rem;border-radius:8px;'
                f'margin:0.15rem 0.15rem 0 0;">{p}</span>'
                for p in c.get("personality", [])
            )

            st.markdown(
                f'<div class="card" style="padding:1rem;margin-top:0.8rem;text-align:center;">'
                f'<img src="{portrait}" style="width:70px;height:70px;border-radius:50%;margin-bottom:0.5rem;">'
                f'<div style="font-weight:700;font-size:1rem;color:#2C1810;">{c["name"]}</div>'
                f'<div style="font-size:0.75rem;color:#8B7355;">{c["dynasty"]}</div>'
                f'<div style="font-size:0.75rem;color:#8B7355;margin-top:0.2rem;">{tags}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            quotes = c.get("quotes", [])
            if quotes:
                st.markdown(
                    f'<div style="font-style:italic;color:#8B7355;font-size:0.8rem;'
                    f'border-left:2px solid #D4A574;padding-left:0.6rem;margin-top:0.3rem;">'
                    f'「{quotes[0]}」</div>',
                    unsafe_allow_html=True,
                )


def render_chat_area(char):
    char_id = char["id"]
    chat_key = f"chat_{char_id}"
    role = char.get("role") or infer_role(char)
    portrait = generate_portrait(char["name"], char["dynasty"], role, size=60)

    # 聊天头部
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.5rem;'
        f'padding:0.6rem 1rem;background:#FAF7F3;border-radius:12px;border:1px solid #E8DDD0;">'
        f'<img src="{portrait}" style="width:50px;height:50px;border-radius:50%;">'
        f'<div>'
        f'<div style="font-weight:700;font-size:1.1rem;color:#2C1810;">{char["name"]}</div>'
        f'<div style="font-size:0.8rem;color:#8B7355;">{char["dynasty"]} · {role}</div>'
        f'</div>'
        f'<div style="margin-left:auto;font-size:0.75rem;color:#8B7355;">'
        f'{len(st.session_state.get(chat_key, [])) // 2} 轮</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # 对话
    for msg in st.session_state[chat_key]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-message user"><div>{msg["content"]}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-message assistant"><div>'
                f'<img src="{portrait}" style="width:24px;height:24px;border-radius:50%;'
                f'vertical-align:middle;margin-right:0.4rem;">'
                f'{msg["content"]}</div></div>',
                unsafe_allow_html=True,
            )

    # 输入
    prompt = st.chat_input(f"想对{char['name']}说什么……", key=f"inp_{char_id}")
    if prompt:
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.spinner(f"{char['name']}正在思考……"):
            reply = generate_reply(char_id, prompt, st.session_state[chat_key])
        st.session_state[chat_key].append({"role": "assistant", "content": reply})
        save_chat(char_id, st.session_state[chat_key])
        st.rerun()

    if not st.session_state[chat_key]:
        st.markdown(
            f'<div style="text-align:center;padding:2rem 1rem 1rem 1rem;color:#8B7355;">'
            f'<img src="{portrait}" style="width:80px;height:80px;border-radius:50%;'
            f'margin-bottom:0.5rem;opacity:0.8;">'
            f'<div style="font-size:1.1rem;font-weight:500;color:#5C3A28;">'
            f'和{char["name"]}打个招呼吧</div>'
            f'<div style="font-size:0.85rem;margin-top:0.2rem;margin-bottom:1rem;">'
            f"试试问ta这些问题：</div></div>",
            unsafe_allow_html=True,
        )

        questions = get_suggested_questions(char_id)
        qcols = st.columns(2)
        for i, q in enumerate(questions):
            with qcols[i % 2]:
                if st.button(f"💬 {q}", key=f"sq_{char_id}_{i}", use_container_width=True):
                    st.session_state[chat_key].append({"role": "user", "content": q})
                    with st.spinner(f"{char['name']}正在思考……"):
                        reply = generate_reply(char_id, q, st.session_state[chat_key])
                    st.session_state[chat_key].append({"role": "assistant", "content": reply})
                    save_chat(char_id, st.session_state[chat_key])
                    st.rerun()

    if st.session_state[chat_key]:
        if st.button("🗑️ 清空对话", key=f"clr_{char_id}"):
            st.session_state[chat_key] = []
            delete_chat(char_id)
            st.rerun()