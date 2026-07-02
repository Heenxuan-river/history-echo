"""对话持久化存储 — 保存到本地文件，刷新不丢失"""
import json
from pathlib import Path

STORE_DIR = Path(__file__).parent.parent / "data" / "conversations"


def _ensure_dir():
    STORE_DIR.mkdir(parents=True, exist_ok=True)


def save_chat(char_id, messages):
    """保存对话记录"""
    _ensure_dir()
    path = STORE_DIR / f"{char_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def load_chat(char_id):
    """加载对话记录"""
    path = STORE_DIR / f"{char_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def delete_chat(char_id):
    """删除某个角色的对话记录"""
    path = STORE_DIR / f"{char_id}.json"
    if path.exists():
        path.unlink()


def delete_all_chats():
    """删除所有对话记录"""
    _ensure_dir()
    for p in STORE_DIR.glob("*.json"):
        p.unlink()