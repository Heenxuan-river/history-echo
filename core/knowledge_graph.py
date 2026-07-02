"""知识图谱引擎：构建 NetworkX 图，支持图谱 + 时间线双视图"""
import networkx as nx
import json
from pathlib import Path

from utils.data_loader import load_characters, load_events, load_relations


def build_graph():
    """构建完整的知识图谱"""
    G = nx.Graph()
    characters = load_characters()
    events = load_events()
    relations = load_relations()

    # 添加人物节点
    for c in characters:
        G.add_node(
            c["id"],
            type="character",
            name=c["name"],
            dynasty=c["dynasty"],
            birth_year=c["birth_year"],
            death_year=c["death_year"],
            description=c.get("description", ""),
            personality=c.get("personality", []),
            achievements=c.get("achievements", []),
            quotes=c.get("quotes", []),
            role=c.get("role", ""),
        )

    # 添加事件节点
    for e in events:
        G.add_node(
            e["id"],
            type="event",
            name=e["name"],
            year=e["year"],
            dynasty=e["dynasty"],
            event_type=e.get("type", ""),
            description=e.get("description", ""),
        )

    # 添加人物-事件连接（参与关系）
    for e in events:
        for cid in e.get("involved_characters", []):
            if G.has_node(cid) and G.has_node(e["id"]):
                G.add_edge(cid, e["id"], relation="参与", weight=1)

    # 添加人物-人物关系
    for r in relations:
        src, tgt = r["source"], r["target"]
        if G.has_node(src) and G.has_node(tgt):
            G.add_edge(src, tgt, relation=r["type"], weight=2)

    return G


def get_character_relations(G, char_id):
    """获取某个人的关系网络"""
    if char_id not in G:
        return []
    result = []
    for neighbor in G.neighbors(char_id):
        edge_data = G.get_edge_data(char_id, neighbor)
        node_data = G.nodes[neighbor]
        result.append({
            "id": neighbor,
            "name": node_data.get("name", neighbor),
            "type": node_data.get("type", ""),
            "relation": edge_data.get("relation", ""),
            "dynasty": node_data.get("dynasty", ""),
        })
    return result


def get_timeline_data():
    """获取时间线数据，按年份排序"""
    events = load_events()
    characters = load_characters()

    timeline = []
    for e in events:
        timeline.append({
            "id": e["id"],
            "name": e["name"],
            "year": e["year"],
            "dynasty": e["dynasty"],
            "type": e.get("type", ""),
            "description": e.get("description", ""),
            "kind": "event",
        })

    # 主要人物的生卒年也加入时间线
    for c in characters:
        if c["birth_year"]:
            timeline.append({
                "id": c["id"] + "_birth",
                "name": f"{c['name']}出生",
                "year": c["birth_year"],
                "dynasty": c["dynasty"],
                "type": "birth",
                "description": c.get("description", ""),
                "kind": "birth",
            })
        if c["death_year"]:
            timeline.append({
                "id": c["id"] + "_death",
                "name": f"{c['name']}逝世",
                "year": c["death_year"],
                "dynasty": c["dynasty"],
                "type": "death",
                "description": "",
                "kind": "death",
            })

    timeline.sort(key=lambda x: x["year"])
    return timeline


def export_graph_for_pyvis(G):
    """导出 NetworkX 图数据为 pyvis 可用的节点/边列表"""
    nodes = []
    edges = []
    for n, data in G.nodes(data=True):
        nodes.append({
            "id": n,
            "label": data.get("name", n),
            "group": data.get("dynasty", "未知"),
            "title": data.get("description", ""),
            "shape": "dot" if data.get("type") == "character" else "square",
        })
    for u, v, data in G.edges(data=True):
        edges.append({
            "from": u,
            "to": v,
            "title": data.get("relation", ""),
        })
    return nodes, edges


def search_graph(G, keyword):
    """在图中搜索节点"""
    results = []
    keyword = keyword.lower()
    for n, data in G.nodes(data=True):
        name = data.get("name", "").lower()
        desc = data.get("description", "").lower()
        if keyword in name or keyword in desc:
            results.append({
                "id": n,
                "name": data.get("name", n),
                "type": data.get("type", ""),
                "dynasty": data.get("dynasty", ""),
            })
    return results