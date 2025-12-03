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


def add_notification(message):
    data = load_notifications()
    data.append({
        "message": message,
        "read": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_notifications(data)

def mark_all_as_read():
    data = load_notifications()
    for n in data:
        n["read"] = True
    save_notifications(data)



