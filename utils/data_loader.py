import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_characters():
    return load_json("characters.json")["characters"]


def load_events():
    return load_json("events.json")["events"]


def load_relations():
    return load_json("relations.json")["relations"]


def get_character_by_id(char_id):
    chars = load_characters()
    for c in chars:
        if c["id"] == char_id:
            return c
    return None


def get_characters_by_dynasty(dynasty):
    chars = load_characters()
    return [c for c in chars if c["dynasty"] == dynasty]


DYNASTY_ORDER = ["先秦", "秦", "汉", "三国", "南北朝", "隋", "唐", "宋", "元", "明", "清", "民国"]


def get_dynasties():
    chars = load_characters()
    seen = set()
    for c in chars:
        seen.add(c["dynasty"])
    return [d for d in DYNASTY_ORDER if d in seen]


def get_events_for_character(char_id):
    events = load_events()
    return [e for e in events if char_id in e.get("involved_characters", [])]


def get_relations_for_character(char_id):
    rels = load_relations()
    result = []
    for r in rels:
        if r["source"] == char_id:
            result.append((r["target"], r["type"], r["description"]))
        if r["target"] == char_id:
            result.append((r["source"], r["type"], r["description"]))
    return result


def get_event_types():
    events = load_events()
    seen = []
    for e in events:
        if e["type"] not in seen:
            seen.append(e["type"])
    return seen