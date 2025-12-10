import json
from datetime import datetime
from utils import data_path


def load_notifications():
    """Load notifications and normalize keys."""
    try:
        with open(data_path("notifications.json"), "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    normalized = []
    for n in data:
        normalized.append({
            "message": n.get("message", ""),
            "read": bool(n.get("read", False)),
            "timestamp": n.get("timestamp", ""),
            "level": n.get("level", "INFO").upper(),
            "category": n.get("category", "GENERAL").upper(),
        })
    return normalized


def save_notifications(notifications):
    with open(data_path("notifications.json"), "w") as f:
        json.dump(notifications, f, indent=4)


def add_notification(message, level='INFO', category='GENERAL'):
    valid_levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level.upper() not in valid_levels:
        level = 'INFO'
    data = load_notifications()
    new_notification = {
        "message": message,
        "read": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "level": level.upper(),
        "category": category.upper()
    }
    data.append(new_notification)
    save_notifications(data)


def mark_all_as_read():
    data = load_notifications()
    for n in data:
        n["read"] = True
    save_notifications(data)


def count_unread(level=None):
    """Return number of unread notifications, optionally filtered by level."""
    data = load_notifications()
    count = 0
    for n in data:
        if n.get("read"):
            continue
        if level and n.get("level") != level.upper():
            continue
        count += 1
    return count
