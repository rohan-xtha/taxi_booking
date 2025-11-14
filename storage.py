import json, os
from typing import Any, Dict, List

DATA_DIR = os.path.dirname(__file__)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")

def ensure_file(path: str, default: Any):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)

def load_json(path: str) -> Any:
    ensure_file(path, [])
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_users() -> List[Dict]:
    return load_json(USERS_FILE)

def save_users(users: List[Dict]):
    save_json(USERS_FILE, users)

def load_bookings() -> List[Dict]:
    return load_json(BOOKINGS_FILE)

def save_bookings(bookings: List[Dict]):
    save_json(BOOKINGS_FILE, bookings)

def next_id(items: List[Dict]) -> int:
    return (max((i.get("id", 0) for i in items), default=0) + 1)