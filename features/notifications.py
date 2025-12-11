import json
from datetime import datetime, timedelta
from utils import data_path

SETTINGS_FILE = data_path("notification_settings.json")
ALLOWED_LEVELS = {"SUCCESS", "INFO", "ALERT", "CRITICAL"}
LEGACY_LEVEL_MAP = {
    "WARNING": "ALERT",
    "WARN": "ALERT",
    "ERROR": "ALERT",
    "INFO": "INFO",
    "CRITICAL": "CRITICAL",
    "SUCCESS": "SUCCESS",
}


def _normalize_level(level):
    upper = (level or "INFO").upper()
    mapped = LEGACY_LEVEL_MAP.get(upper, upper)
    return mapped if mapped in ALLOWED_LEVELS else "INFO"


def _load_settings():
    default = {
        "shortage_warning_buffer": 0.15,  # 15% over required triggers warning
        "muted_categories": {},  # {"FOOD": "2025-12-01 12:00"}
    }
    try:
        with open(SETTINGS_FILE, "r") as f:
            raw = json.load(f)
            default.update(raw)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return default


def _save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def mute_category(category, minutes=60):
    settings = _load_settings()
    until = datetime.now() + timedelta(minutes=minutes)
    settings.setdefault("muted_categories", {})
    settings["muted_categories"][category.upper()] = until.strftime("%Y-%m-%d %H:%M")
    _save_settings(settings)


def unmute_category(category):
    settings = _load_settings()
    muted = settings.get("muted_categories", {})
    if category.upper() in muted:
        muted.pop(category.upper(), None)
        settings["muted_categories"] = muted
        _save_settings(settings)


def _is_muted(category):
    settings = _load_settings()
    muted = settings.get("muted_categories", {})
    ts = muted.get(category.upper())
    if not ts:
        return False
    try:
        until = datetime.strptime(ts, "%Y-%m-%d %H:%M")
        if datetime.now() > until:
            muted.pop(category.upper(), None)
            settings["muted_categories"] = muted
            _save_settings(settings)
            return False
        return True
    except Exception:
        return False


def load_notifications(username=None, unread_only=False, filter_fn=None):
    """Load notifications; if username provided, filter by read_by and filter_fn."""
    try:
        with open(data_path("notifications.json"), "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    normalized = []
    for n in data:
        read_by = n.get("read_by")
        if not isinstance(read_by, list):
            read_by = []
        deleted_by = n.get("deleted_by")
        if not isinstance(deleted_by, list):
            deleted_by = []
        if username and username in deleted_by:
            continue
        notif = {
            "message": n.get("message", ""),
            "timestamp": n.get("timestamp", ""),
            "level": _normalize_level(n.get("level", "INFO")),
            "category": n.get("category", "GENERAL").upper(),
            "context": n.get("context", {}),
            "read_by": read_by,
            "deleted_by": deleted_by,
            # Derived per-user read flag so UI filters work correctly.
            "read": (username in read_by) if username else bool(n.get("read", False)),
        }
        if username and unread_only and notif["read"]:
            continue
        if filter_fn and not filter_fn(notif):
            continue
        normalized.append(notif)
    return normalized


def save_notifications(notifications):
    with open(data_path("notifications.json"), "w") as f:
        json.dump(notifications, f, indent=4)


def add_notification(message, level='INFO', category='GENERAL', context=None):
    """Add a notification; respects muted categories. Note: read_by starts empty."""
    level = _normalize_level(level)
    category = category.upper()
    if _is_muted(category):
        return
    data = load_notifications()
    new_notification = {
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "level": level,
        "category": category,
        "context": context or {},
        "read_by": [],
        "deleted_by": [],
    }
    data.append(new_notification)
    save_notifications(data)


def mark_all_as_read(username):
    data = load_notifications()
    changed = False
    for n in data:
        if username not in n.get("read_by", []):
            n.setdefault("read_by", []).append(username)
            changed = True
    if changed:
        save_notifications(data)


def clear_notifications(username):
    """Marks all as read for this user (no global deletion)."""
    mark_all_as_read(username)


def delete_notifications_for_user(username):
    """Remove notifications from view for a specific user (others unaffected)."""
    try:
        with open(data_path("notifications.json"), "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    changed = False
    for n in data:
        deleted_by = n.get("deleted_by")
        if not isinstance(deleted_by, list):
            deleted_by = []
        if username not in deleted_by:
            deleted_by.append(username)
            n["deleted_by"] = deleted_by
            changed = True
    if changed:
        save_notifications(data)


def count_unread(username, level=None, category=None, filter_fn=None):
    data = load_notifications()
    level = _normalize_level(level) if level else None
    count = 0
    for n in data:
        if username in n.get("read_by", []):
            continue
        if level and n.get("level") != level.upper():
            continue
        if category and n.get("category") != category.upper():
            continue
        if filter_fn and not filter_fn(n):
            continue
        count += 1
    return count


def get_thresholds():
    """Return shortage warning buffer percentage (float)."""
    settings = _load_settings()
    return {
        "shortage_warning_buffer": settings.get("shortage_warning_buffer", 0.15),
    }


def set_thresholds(warning_buffer):
    settings = _load_settings()
    try:
        settings["shortage_warning_buffer"] = max(0.0, float(warning_buffer))
    except (TypeError, ValueError):
        settings["shortage_warning_buffer"] = 0.15
    _save_settings(settings)
