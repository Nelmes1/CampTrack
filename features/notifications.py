import json
from datetime import datetime
from utils import data_path


def load_notifications():
    try:
        with open(data_path("notifications.json"), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_notifications(notifications):
    with open(data_path("notifications.json"), "w") as f:
        json.dump(notifications, f, indent=4)


def add_notification(message, level='INFO'):
    valid_levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level.upper() not in valid_levels:
        level = 'INFO'
    data = load_notifications()
    new_notification = {
        "message": message,
        "read": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "level": level.upper()
    }
    data.append(new_notification)
    save_notifications(data)

def mark_all_as_read():
    data = load_notifications()
    for n in data:
        n["read"] = True
    save_notifications(data)



