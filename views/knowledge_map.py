"""历史星图：知识图谱 + 时间线双视图"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import tempfile, os, base64
from pyvis.network import Network
from core.knowledge_graph import build_graph, get_timeline_data, search_graph
from utils.data_loader import get_dynasties, get_event_types, get_events_for_character
from utils.portraits import generate_portrait, infer_role

EVENT_COLORS = {
    "war": "#C0392B", "politics": "#2C3E50", "culture": "#D4A574",
    "reform": "#27AE60", "birth": "#8B7355", "death": "#999999",
}


def generate_avatar(name, dynasty, role=None):
    """生成人物画像（统一调用 portrait 模块）"""
    return generate_portrait(name, dynasty, role, size=60)


# ═══════════════════════════════════════════════════════════
# 主页面
# ═══════════════════════════════════════════════════════════
def show():
    st.title("🗺️ 历史星图")
    st.markdown(
        '<p style="color:#8B7355;font-size:1.05rem;margin-top:-0.5rem;">'
        "以星辰之姿俯瞰历史——人物与事件的关系网络，在时间轴上纵览兴衰</p>",
        unsafe_allow_html=True,
    )

    G = build_graph()
    timeline_data = get_timeline_data()

    # 顶部工具栏
    col1, col2, col3 = st.columns([2.5, 1, 1.5])
    with col1:
        search_term = st.text_input("🔍", placeholder="搜索人物或事件…", label_visibility="collapsed")
    with col2:
        dyns = ["全部"] + get_dynasties()
        sel_dyn = st.selectbox("朝代", dyns, label_visibility="collapsed")
    with col3:
        view_mode = st.radio("视图", ["🌐 图谱", "📅 时间线"], horizontal=True, label_visibility="collapsed")

    # 搜索结果
    if search_term:
        results = search_graph(G, search_term)
        if results:
            st.markdown(f'<div style="margin-bottom:0.5rem;font-size:0.85rem;color:#8B7355;">找到 {len(results)} 个结果</div>', unsafe_allow_html=True)
            cols = st.columns(min(len(results), 5))
            for i, r in enumerate(results):
                with cols[i % 5]:
                    btn = st.button(f"📌 {r['name']}", key=f"sr_{r['id']}", use_container_width=True)
                    if btn:
                        st.session_state["selected_node"] = r["id"]
        else:
            st.info("未找到匹配结果")

    st.markdown("---")

    dyn_filter = sel_dyn if sel_dyn != "全部" else None
    if "图谱" in view_mode:
        show_graph_view(G, dyn_filter)
    else:
        show_timeline_view(timeline_data, dyn_filter)


# ═══════════════════════════════════════════════════════════
# 图谱视图
# ═══════════════════════════════════════════════════════════
def show_graph_view(G, dynasty_filter):
    col1, col2 = st.columns([3.2, 2])

    with col1:
        H = G.subgraph([n for n, d in G.nodes(data=True) if d.get("dynasty") == dynasty_filter]) if dynasty_filter else G
        if H.number_of_nodes() == 0:
            st.warning("该朝代暂无数据"); return

        net = Network(height="540px", width="100%", bgcolor="#FAF7F3", font_color="#2C1810")
        net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=180)

        for n, data in H.nodes(data=True):
            is_char = data.get("type") == "character"
            if is_char:
                name = data.get("name", n)
                dynasty = data.get("dynasty", "")
                img = generate_avatar(name, dynasty, data.get("role") or infer_role(data))
                shape, size = "circularImage", 35
                net.add_node(n, label=name, shape=shape, size=size, image=img,
                             title=f"<b>{name}</b><br>{dynasty} · 人物<br>{data.get('description','')[:60]}…",
                             borderWidth=2, color="#fff")
            else:
                color = EVENT_COLORS.get(data.get("event_type",""), "#D4A574")
                shape, size = "dot", 22
                net.add_node(n, label=data.get("name", n), shape=shape, size=size, color=color,
                             title=f"<b>{data.get('name', n)}</b><br>{data.get('dynasty','')} · 事件<br>{data.get('description','')[:60]}…")

        for u, v, data in H.edges(data=True):
            net.add_edge(u, v,
                         title=f'<span style="font-family:Microsoft YaHei;color:#8B7355;">{data.get("relation","")}</span>',
                         color="#C4B5A0", width=1.5, arrowStrikethrough=False)

        net.set_options("""{
          "nodes": {"font": {"size": 14, "face": "Microsoft YaHei", "strokeWidth": 2, "strokeColor": "#ffffff"}},
          "edges": {"font": {"size": 11, "face": "Microsoft YaHei", "color": "#8B7355"}, "smooth": {"type": "continuous"}},
          "physics": {"barnesHut": {"gravitationalConstant": -3000, "centralGravity": 0.3, "springLength": 200, "springConstant": 0.04, "damping": 0.09}, "minVelocity": 0.75},
          "interaction": {"hover": true, "tooltipDelay": 200, "navigationButtons": true, "keyboard": true}
        }""")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            with open(tmp.name, "r", encoding="utf-8") as f:
                html = f.read()
        os.unlink(tmp.name)
        st.components.v1.html(html, height="560")
        st.caption("🖱️ 拖拽节点 · 滚轮缩放 · 悬停查看 · 点击选择")

    with col2:
        render_detail_panel(G)


# ═══════════════════════════════════════════════════════════
# 详情面板（可展开）
# ═══════════════════════════════════════════════════════════
def render_detail_panel(G):
    node_id = st.session_state.get("selected_node")
    st.markdown('<div class="card" style="min-height:400px;">', unsafe_allow_html=True)

    # 节点选择器（作为图谱点击的补充）
    all_nodes = []
    for n, d in G.nodes(data=True):
        all_nodes.append((n, d.get("name", n), d.get("dynasty", ""), d.get("type", "")))
    all_nodes.sort(key=lambda x: x[1])
    sel_name = st.selectbox(
        "选择查看",
        [""] + [f"{n[1]} ({n[2]})" for n in all_nodes],
        format_func=lambda x: x if x else "← 点击图谱节点或在此选择",
        key="node_selector",
        label_visibility="collapsed",
    )
    if sel_name:
        matched = [n for n in all_nodes if f"{n[1]} ({n[2]})" == sel_name]
        if matched:
            st.session_state["selected_node"] = matched[0][0]
            st.rerun()

    if node_id and G.has_node(node_id):
        data = G.nodes[node_id]
        is_char = data.get("type") == "character"
        name = data.get("name", node_id)
        dynasty = data.get("dynasty", "")
        avatar = generate_avatar(name, dynasty, infer_role(data)) if is_char else "📜"

        # 头部
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.8rem;">'
            f'<span style="font-size:2rem;">{avatar if is_char else "📜"}</span>'
            f'<div><div style="font-size:1.2rem;font-weight:700;color:#2C1810;">{name}</div>'
            f'<div style="font-size:0.8rem;color:#8B7355;">{dynasty} · {"人物" if is_char else "事件"}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div style="font-size:0.9rem;color:#5C3A28;line-height:1.6;">{data.get("description","")}</div>', unsafe_allow_html=True)

        if is_char:
            personality = data.get("personality", [])
            if personality:
                tags = "".join(f'<span style="display:inline-block;background:#F0E8DE;color:#5C3A28;font-size:0.7rem;padding:0.1rem 0.5rem;border-radius:8px;margin:0.15rem 0.15rem 0 0;">{p}</span>' for p in personality)
                st.markdown(f'<div style="margin-top:0.5rem;font-size:0.85rem;color:#8B7355;">性格 {tags}</div>', unsafe_allow_html=True)

            with st.expander("📖 查看更多信息", expanded=False):
                quotes = data.get("quotes", [])
                if quotes:
                    st.markdown("**名言**")
                    for q in quotes:
                        st.markdown(f"> 「{q}」")
                achievements = data.get("achievements", [])
                if achievements:
                    st.markdown("**主要成就**")
                    for a in achievements:
                        st.markdown(f"- {a}")
                events = get_events_for_character(node_id)
                if events:
                    st.markdown("**相关事件**")
                    for e in events:
                        st.markdown(f"- {e['name']}（{e['year']}）")

        else:
            with st.expander("📖 查看详情", expanded=False):
                st.markdown(f"**年份**：{data.get('year','')}")
                st.markdown(f"**类型**：{data.get('event_type','')}")
                st.markdown(f"**影响**：{data.get('description','')}")

        # 关联节点（使用 Streamlit 按钮实现点击切换）
        st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)
        neighbors = list(G.neighbors(node_id))
        if neighbors:
            st.markdown(f'<div style="font-size:0.85rem;font-weight:600;color:#5C3A28;margin-bottom:0.3rem;">🔗 关联 ({len(neighbors)})</div>', unsafe_allow_html=True)
            for nb in neighbors[:10]:
                nd = G.nodes[nb]
                ed = G.get_edge_data(node_id, nb)
                rel = ed.get("relation", "关联") if ed else "关联"
                is_nb_char = nd.get("type") == "character"
                av = generate_avatar(nd.get("name", nb), nd.get("dynasty", ""), infer_role(nd)) if is_nb_char else "📜"
                col_a, col_b = st.columns([0.3, 0.7])
                with col_a:
                    st.markdown(
                        f'<div style="font-size:1.2rem;text-align:center;">{av if is_nb_char else "📜"}</div>',
                        unsafe_allow_html=True,
                    )
                with col_b:
                    if st.button(
                        f"**{nd.get('name', nb)}** · {rel}",
                        key=f"rel_{nb}",
                        use_container_width=True,
                        help="点击查看此节点",
                    ):
                        st.session_state["selected_node"] = nb
                        st.rerun()
        else:
            st.markdown('<div style="color:#8B7355;font-size:0.85rem;">暂无关联</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;padding:3rem 0;color:#8B7355;">'
            '<div style="font-size:2.5rem;margin-bottom:0.5rem;">👆</div>'
            '<div>点击图谱中的节点查看详情</div>'
            '<div style="font-size:0.85rem;margin-top:0.3rem;">🔵 圆形头像 = 人物 · 🟤 圆点 = 事件</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 时间线视图（交错布局）
# ═══════════════════════════════════════════════════════════
def show_timeline_view(timeline_data, dynasty_filter):
    df = pd.DataFrame(timeline_data)
    if dynasty_filter:
        df = df[df["dynasty"] == dynasty_filter]
    if df.empty:
        st.info("无匹配数据"); return

    # ── 筛选栏 ──
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        mn, mx = int(df["year"].min()), int(df["year"].max())
        if mn < mx:
            r = st.slider("", mn, mx, (mn, mx), label_visibility="collapsed")
            df = df[(df["year"] >= r[0]) & (df["year"] <= r[1])]
    with col2:
        ts = ["全部"] + get_event_types()
        sel_t = st.selectbox("类型", ts, label_visibility="collapsed", key="tl_type_sel")
        if sel_t != "全部":
            df = df[df["type"] == sel_t]

    # ── 动态密度控制 ──
    priority_map = {"war": 0, "politics": 0, "reform": 1, "culture": 1, "birth": 2, "death": 2}
    df["priority"] = df["type"].map(priority_map).fillna(1)

    span = df["year"].max() - df["year"].min() if not df.empty else 0
    epc = 100 / max(span / max(len(df), 1), 1)

    hidden_msg = ""
    if sel_t == "全部" and not df.empty:
        if epc > 15:
            filtered = df[df["priority"] <= 0].copy()
            hidden = len(df) - len(filtered)
            if hidden:
                hidden_msg = f"密度{epc:.0f}条/百年，隐藏{hidden}条次要事件"
                df = filtered
            elif len(df) > 25:
                hidden_msg = f"共{len(df)}条，建议缩小时间范围"
        elif epc > 6:
            filtered = df[df["priority"] <= 1].copy()
            hidden = len(df) - len(filtered)
            if hidden:
                hidden_msg = f"密度{epc:.0f}条/百年，隐藏{hidden}条次要事件"
                df = filtered

    with col3:
        if hidden_msg:
            st.markdown(f'<div style="text-align:right;padding:0.4rem 0;font-size:0.8rem;color:#C0392B;">{hidden_msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:right;padding:0.4rem 0;font-size:0.85rem;color:#8B7355;">共 {len(df)} 条</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("该范围内无数据"); return

    # ── 交替上下布局，文字永不重叠 ──
    # 先按年份排序，再交替分配上/下位置
    df = df.sort_values("year").reset_index(drop=True)
    y_vals = []
    text_pos = []
    for i in range(len(df)):
        if i % 2 == 0:
            y_vals.append(1.7)
            text_pos.append("top center")
        else:
            y_vals.append(0.3)
            text_pos.append("bottom center")
    df["y_pos"] = y_vals
    df["text_pos"] = text_pos

    # 年份格式化
    def fmt_year(y):
        return f"公元前{abs(y)}年" if y < 0 else f"{y}年"
    df["year_label"] = df["year"].apply(fmt_year)

    # 类别标记
    type_labels = {"war":"⚔️战争","politics":"👑政治","culture":"📚文化","reform":"🛠️改革","birth":"👶出生","death":"⚰️逝世"}
    df["type_label"] = df["type"].map(type_labels).fillna(df["type"])
    df["hover_text"] = df.apply(
        lambda r: f"<b>{r['name']}</b><br>{r['year_label']} · {r['dynasty']}<br>{r.get('description','')[:120]}",
        axis=1,
    )

    # ── 绘图 ──
    fig = go.Figure()

    # 基线
    fig.add_trace(go.Scatter(
        x=[df["year"].min(), df["year"].max()],
        y=[1, 1],
        mode="lines",
        line=dict(color="#E8DDD0", width=2),
        showlegend=False,
        hoverinfo="skip",
    ))

    # 垂直连接线
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["year"], row["year"]],
            y=[1, row["y_pos"]],
            mode="lines",
            line=dict(color="rgba(139,115,85,0.3)", width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # 锯齿线串联事件
    sorted_df = df.sort_values("year")
    zz_x, zz_y = [], []
    for _, row in sorted_df.iterrows():
        zz_x.extend([row["year"], row["year"]])
        zz_y.extend([1, row["y_pos"]])
    fig.add_trace(go.Scatter(
        x=zz_x, y=zz_y,
        mode="lines",
        line=dict(color="rgba(212,165,116,0.35)", width=1.5, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))

    # 事件点 + 标签
    dynasties_in_view = df["dynasty"].unique()
    color_seq = px.colors.qualitative.Set2
    dyn_color_map = {d: color_seq[i % len(color_seq)] for i, d in enumerate(dynasties_in_view)}
    df["color"] = df["dynasty"].map(dyn_color_map)

    fig.add_trace(go.Scatter(
        x=df["year"],
        y=df["y_pos"],
        mode="markers+text",
        marker=dict(
            size=14,
            color=df["color"],
            line=dict(width=1.5, color="white"),
            symbol="circle",
        ),
        text=df["name"],
        textposition=df["text_pos"],
        textfont=dict(size=11, family="Microsoft YaHei", color="#2C1810"),
        customdata=df[["name", "year_label", "dynasty", "type_label", "description", "id"]].values.tolist(),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<br>%{customdata[3]}<br>%{customdata[4]}<extra></extra>",
        showlegend=False,
    ))

    # 公元元年线
    if df["year"].min() < 0 < df["year"].max():
        fig.add_vline(x=0, line_color="#C0392B", line_dash="dash", line_width=1,
                      annotation_text="公元元年", annotation_position="top left",
                      annotation_font=dict(size=10, color="#C0392B", family="Microsoft YaHei"))

    fig.update_layout(
        height=520,
        margin=dict(t=20, b=60, l=30, r=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="", showgrid=True, gridcolor="#F5F0EB", gridwidth=1,
            tickfont=dict(size=12, family="Microsoft YaHei", color="#5C3A28"),
            zeroline=False,
        ),
        yaxis=dict(showticklabels=False, showgrid=False, range=[-0.1, 2.1], visible=False),
        hovermode="closest",
        hoverlabel=dict(font=dict(family="Microsoft YaHei", size=13), bordercolor="#E8DDD0", bgcolor="white"),
        clickmode="event+select",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── 事件详表 ──
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.5rem 0 0.3rem 0;">'
        f'<span style="font-weight:600;font-size:0.95rem;color:#2C1810;">📋 事件列表</span>'
        f'<span style="font-size:0.8rem;color:#8B7355;">共 {len(df)} 条</span></div>',
        unsafe_allow_html=True,
    )

    df_sorted = df.sort_values("year")
    max_show = 30
    for _, row in df_sorted.head(max_show).iterrows():
        year_str = f"公元前{abs(row['year'])}年" if row['year'] < 0 else f"{row['year']}年"
        tl = type_labels.get(row.get("type", ""), "")
        st.markdown(
            f'<div style="padding:0.5rem 0.8rem;background:#FAF7F3;border:1px solid #F0E8DE;border-radius:8px;'
            f'margin:0.2rem 0;display:flex;align-items:center;gap:0.8rem;cursor:default;">'
            f'<div style="min-width:95px;font-size:0.8rem;font-weight:600;color:#8B7355;">{year_str}</div>'
            f'<div style="flex:1;font-size:0.9rem;color:#2C1810;font-weight:500;">{row["name"]}</div>'
            f'<div style="font-size:0.75rem;color:#8B7355;">{tl}</div>'
            f'<div style="font-size:0.7rem;color:#8B7355;min-width:40px;text-align:right;">{row["dynasty"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if len(df_sorted) > max_show:
        st.caption(f"仅显示前 {max_show} 条，请使用筛选缩小范围")