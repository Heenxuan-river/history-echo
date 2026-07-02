import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from views import dialogue, knowledge_map, alternate, travel

st.set_page_config(
    page_title="历史回响 — 中国历史互动探索平台",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 全局 CSS
# ============================================================
st.markdown("""
<style>
/* ===== 全局基础 ===== */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans SC', -apple-system, 'Microsoft YaHei', sans-serif;
}

/* 主内容区 */
.main > .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* ===== 标题 ===== */
h1, h2, h3 {
    font-family: 'Noto Serif SC', serif;
    font-weight: 600;
    letter-spacing: 0.02em;
}
h1 {
    font-size: 1.8rem;
    margin-bottom: 0.2rem;
    padding-bottom: 0;
    border-bottom: none;
}
h1 + p {
    margin-top: 0;
    margin-bottom: 0.3rem;
}

/* ===== 侧边栏 ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2C1810 0%, #3D2317 100%);
    color: #F5E6D3;
}
section[data-testid="stSidebar"] .stButton button {
    background: transparent;
    color: #F5E6D3;
    border: 1px solid rgba(212, 165, 116, 0.3);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.95rem;
    font-weight: 400;
    transition: all 0.2s;
    text-align: left;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(212, 165, 116, 0.15);
    border-color: #D4A574;
    transform: translateX(2px);
}
section[data-testid="stSidebar"] .stButton button:active,
section[data-testid="stSidebar"] .stButton button:focus {
    background: rgba(212, 165, 116, 0.25);
    border-color: #D4A574;
}
section[data-testid="stSidebar"] h1 {
    color: #F5E6D3;
    border-bottom: none;
    font-size: 1.4rem;
    letter-spacing: 0.1em;
    text-align: center;
    padding: 0.5rem 0;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(212, 165, 116, 0.2);
    margin: 0.8rem 0;
}
section[data-testid="stSidebar"] .stMarkdown p {
    color: rgba(245, 230, 211, 0.7);
    font-size: 0.85rem;
    line-height: 1.6;
}
section[data-testid="stSidebar"] code {
    background: rgba(212, 165, 116, 0.1);
    color: #D4A574;
    font-size: 0.8rem;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
}

/* ===== 卡片容器 ===== */
.card {
    background: #FFFFFF;
    border: 1px solid #E8DDD0;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

/* ===== 按钮 ===== */
.stButton button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
}
div[data-testid="stForm"] button {
    border-radius: 8px;
}

/* ===== 标签页/选择框 ===== */
.stSelectbox [data-testid="stMarkdownContainer"] {
    font-weight: 500;
}
.stRadio div[role="radiogroup"] {
    gap: 0.5rem;
}
.stRadio div[role="radiogroup"] label {
    background: #F8F4EF;
    border: 1px solid #E8DDD0;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.9rem;
    transition: all 0.2s;
}
.stRadio div[role="radiogroup"] label:hover {
    background: #F0E8DE;
}

/* ===== 信息框 ===== */
.stAlert {
    border-radius: 8px;
    border-left-width: 4px;
}

/* ===== 代码块 ===== */
code {
    border-radius: 4px;
}

/* ===== 展开器 ===== */
.streamlit-expanderHeader {
    font-weight: 500;
    border-radius: 8px;
}

/* ===== 滚动条 ===== */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #D4A574;
    border-radius: 3px;
}

/* ===== 分割线 ===== */
hr {
    border-color: #E8DDD0;
    margin: 1.5rem 0;
}

/* ===== 时间线模式特定 ===== */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
}

/* ===== 对话气泡 ===== */
.chat-message {
    padding: 0.5rem 0;
}
.chat-message.user {
    text-align: right;
}
.chat-message.user > div {
    background: #D4A574;
    color: white;
    display: inline-block;
    padding: 0.6rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    text-align: left;
}
.chat-message.assistant > div {
    background: #F8F4EF;
    display: inline-block;
    padding: 0.6rem 1.2rem;
    border-radius: 18px 18px 18px 4px;
    max-width: 75%;
    text-align: left;
    border: 1px solid #E8DDD0;
}

/* ===== 选项卡片 ===== */
.choice-card {
    background: #FAF7F3;
    border: 1px solid #E8DDD0;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 0.5rem;
}
.choice-card:hover {
    background: #F0E8DE;
    border-color: #D4A574;
    transform: translateY(-1px);
}

/* ===== badge 标签 ===== */
.badge {
    display: inline-block;
    background: #F0E8DE;
    color: #5C3A28;
    font-size: 0.75rem;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-weight: 500;
}

/* ===== 响应式调整 ===== */
@media (max-width: 768px) {
    .main > .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 侧边栏导航
# ============================================================
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:0.5rem 0;">'
        '<span style="font-size:2rem;">🏛️</span>'
        '<h1 style="margin:0.3rem 0 0 0;">历史回响</h1>'
        '<p style="color:rgba(245,230,211,0.6);font-size:0.8rem;letter-spacing:0.2em;">中国历史互动探索平台</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 导航项：图标 + 名称 + 描述
    nav_items = [
        ("💬", "人物对话", "与历史人物跨越时空的对话", dialogue),
        ("🗺️", "历史星图", "人物关系图谱 × 时空时间线", knowledge_map),
        ("🔄", "如果历史改变", "改变节点，推演平行世界", alternate),
        ("⏳", "穿越助手", "穿越年代的生存指南", travel),
    ]

    if "page" not in st.session_state:
        st.session_state["page"] = nav_items[0][1]

    for icon, name, desc, module in nav_items:
        active = st.session_state["page"] == name
        btn_style = (
            f"background: rgba(212,165,116,0.2);border-color:#D4A574;"
            if active else ""
        )
        label = f"{icon} {name}"
        help_text = desc

        if st.button(label, use_container_width=True, help=help_text):
            st.session_state["page"] = name

    st.markdown("---")

    # 底部信息
    st.markdown(
        f"""<div style="padding:0.5rem 0;">
        <p style="font-size:0.75rem;color:rgba(245,230,211,0.5);">
        📜 数据范围：先秦 → 民国<br>
        👤 收录人物：42位<br>
        📖 历史事件：27件<br>
        🔗 关系连接：31条
        </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # API 状态
    import os
    provider = os.environ.get("LLM_PROVIDER", "deepseek")
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY") or
                   os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("GLM_API_KEY") or
                   os.environ.get("TONGYI_API_KEY"))
    if has_key:
        st.success(f"🤖 AI 引擎已就绪（{provider}）", icon="✅")
    else:
        st.info("🔑 配置 API Key 开启 AI 对话", icon="🔌")

# ============================================================
# 页面路由
# ============================================================
current_page = st.session_state["page"]
page_map = {name: module for _, name, _, module in nav_items}
page_map[current_page].show()
