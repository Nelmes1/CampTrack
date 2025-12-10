# messaging.py

import json
import os
from datetime import datetime
from utils import data_path
from camp_class import read_from_file, save_to_file
from typing import List, Optional, Dict, Any

MESSAGES_FILE = data_path("messages.json")


# ---------- helpers to load/save ----------

def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return []

    try:
        with open(MESSAGES_FILE, "r") as f:
            data = json.load(f)
            messages = data.get("messages", [])
            return [_normalize_message(m) for m in messages]
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_messages(messages):
    data = {"messages": messages}
    with open(MESSAGES_FILE, "w") as f:
        json.dump(data, f, indent=4)


def _normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure a message dict has expected keys with safe defaults."""
    msg.setdefault("read", False)
    msg.setdefault("priority", False)
    msg.setdefault("requires_ack", False)
    msg.setdefault("acked", False)
    msg.setdefault("pinned", False)
    msg.setdefault("attachment", None)
    msg.setdefault("metadata", {})
    return msg


def _camp_recipients(camp_name: str) -> List[str]:
    """Return usernames assigned to a camp (scout leaders)."""
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            return list(set(camp.scout_leaders))
    return []


def get_all_usernames(users_dict):
    """Flatten your users structure into a simple list of usernames."""
    names = []

    # admin
    admin = users_dict.get("admin")
    if isinstance(admin, list):
        for a in admin:
            if isinstance(a, dict) and "username" in a:
                names.append(a["username"])
    elif isinstance(admin, dict) and "username" in admin:
        names.append(admin["username"])
    elif isinstance(admin, str):
        names.append(admin)

    # scout leaders
    for u in users_dict.get("scout leader", []):
        if isinstance(u, dict) and "username" in u:
            names.append(u["username"])

    # logistics coordinators
    for u in users_dict.get("logistics coordinator", []):
        if isinstance(u, dict) and "username" in u:
            names.append(u["username"])

    return names

def count_unread_messages(username, other):
    """
    Count unread messages sent TO `username`.
    If from_user is provided, count only messages from that user.
    """
    messages = load_messages()
    if other is None:
        unread = [
            msg for msg in messages
            if msg.get("to") == username and msg.get("read") is False
        ]
        return len(unread)
    else:
        unread = [
            msg for msg in messages
            if msg.get("to") == username
            and msg.get("from") == other
            and msg.get("read") is False
        ]
    return len(unread)
        
        

def mark_conversation_as_read(username, other):
    """Mark all messages sent to 'username' from 'other' as read."""
    messages = load_messages()
    changed = False

    for msg in messages:
        if msg["from"] == other and msg["to"] == username and msg.get("read") is False:
            msg["read"] = True
            changed = True

    if changed:
        save_messages(messages)


def acknowledge_conversation(username: str, other: str) -> int:
    """
    Acknowledge all priority messages sent TO username from other that need ack.
    Returns count of messages updated.
    """
    messages = load_messages()
    updated = 0
    for msg in messages:
        if (
            msg.get("to") == username
            and msg.get("from") == other
            and msg.get("requires_ack")
            and not msg.get("acked")
        ):
            msg["acked"] = True
            msg["acked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated += 1
    if updated:
        save_messages(messages)
    return updated


def pin_message(username: str, other: str, timestamp: Optional[str] = None, pinned: bool = True) -> bool:
    """
    Pin/unpin a message in the conversation. Default: pin latest message.
    Returns True if a message was updated.
    """
    thread = get_conversation(username, other)
    if not thread:
        return False

    target = None
    if timestamp:
        for msg in thread:
            if msg.get("timestamp") == timestamp:
                target = msg
                break
    else:
        target = thread[-1]  # latest

    if not target:
        return False

    messages = load_messages()
    for msg in messages:
        if msg is target or (
            msg.get("timestamp") == target.get("timestamp")
            and msg.get("from") == target.get("from")
            and msg.get("to") == target.get("to")
            and msg.get("text") == target.get("text")
        ):
            msg["pinned"] = pinned
            msg["pinned_by"] = username
            save_messages(messages)
            return True
    return False


# ---------- core chat logic ----------

def send_message(sender: str, recipient: str, text: str, *, priority: bool = False,
                 attachment: Optional[str] = None, requires_ack: bool = False,
                 metadata: Optional[Dict[str, Any]] = None):
    messages = load_messages()
    messages.append({
        "from": sender,
        "to": recipient,
        "text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False,
        "priority": priority,
        "requires_ack": requires_ack or priority,
        "acked": False,
        "pinned": False,
        "attachment": attachment,
        "metadata": metadata or {},
    })
    save_messages(messages)


def send_broadcast(sender: str, recipients: List[str], text: str, *, priority: bool = False,
                   attachment: Optional[str] = None, requires_ack: bool = False,
                   metadata: Optional[Dict[str, Any]] = None):
    """Send the same message to many recipients (one entry per recipient)."""
    metadata = metadata or {}
    for r in recipients:
        if r == sender:
            continue
        send_message(sender, r, text, priority=priority,
                     attachment=attachment, requires_ack=requires_ack,
                     metadata={"broadcast": True, **metadata})


def get_conversations_for_user(username):
    """Return a sorted list of usernames this user has chatted with."""
    messages = load_messages()
    others = set()

    for msg in messages:
        if msg["from"] == username:
            others.add(msg["to"])
        elif msg["to"] == username:
            others.add(msg["from"])

    return sorted(others)


def get_conversation(username, other):
    """All messages between username and other, ordered by time."""
    messages = load_messages()
    thread = [
        msg for msg in messages
        if (msg["from"] == username and msg["to"] == other)
        or (msg["from"] == other and msg["to"] == username)
    ]
    # Already roughly ordered by append, but sort just in case
    thread.sort(key=lambda m: m["timestamp"])
    return thread


def search_messages(username: str, *, query: Optional[str] = None, other: Optional[str] = None,
                    date_from: Optional[str] = None, date_to: Optional[str] = None,
                    priority_only: bool = False) -> List[Dict[str, Any]]:
    """
    Search messages involving `username` with optional filters.
    date_from/date_to are strings "YYYY-MM-DD".
    """
    messages = load_messages()

    def _involved(msg):
        return msg.get("from") == username or msg.get("to") == username

    def _match(msg):
        if other and not (
            (msg.get("from") == username and msg.get("to") == other)
            or (msg.get("from") == other and msg.get("to") == username)
        ):
            return False
        if priority_only and not msg.get("priority"):
            return False
        if query and query.lower() not in msg.get("text", "").lower():
            return False
        ts = msg.get("timestamp", "")
        if date_from and ts < f"{date_from} 00:00:00":
            return False
        if date_to and ts > f"{date_to} 23:59:59":
            return False
        return True

    return [m for m in messages if _involved(m) and _match(m)]


def export_conversation(username: str, other: str, filepath: str) -> bool:
    """Export conversation as plain text file. Returns True on success."""
    thread = get_conversation(username, other)
    try:
        with open(filepath, "w") as f:
            for msg in thread:
                flags = []
                if msg.get("priority"):
                    flags.append("PRIORITY")
                if msg.get("requires_ack") and not msg.get("acked"):
                    flags.append("ACK PENDING")
                if msg.get("pinned"):
                    flags.append("PINNED")
                flag_str = f" [{' | '.join(flags)}]" if flags else ""
                attachment = msg.get("attachment")
                attach_str = f" [attachment: {attachment}]" if attachment else ""
                f.write(f"{msg.get('timestamp')} - {msg.get('from')} -> {msg.get('to')}: {msg.get('text')}{flag_str}{attach_str}\n")
        return True
    except OSError:
        return False


# ---------- menu shown to a logged-in user ----------

def messaging_menu(current_user, users_dict):
    """WhatsApp-style CLI chat for a single logged-in user."""

    user_role = None
    for role, users in users_dict.items():
        if any(u['username'] == current_user for u in users):
            user_role = role
            break

    while True:
        unread_total = count_unread_messages(current_user,other=None)

        print("\n--- Messaging ---")
        print(f"You have {unread_total} unread message(s).")
        print("[1] View conversations")
        print("[2] Start new chat / broadcast")
        if user_role == 'scout leader':  
            print("[3] View camp group chats")
            print("[4] Back")
        else:
            print("[3] Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            conversations = get_conversations_for_user(current_user)
            if not conversations:
                print("\nNo conversations yet. Start a new chat!")
                continue

            print("\nYour conversations:")
            for i, other in enumerate(conversations, start=1):
                unread = count_unread_messages(current_user,other)
                if unread > 0:
                    unread_num = f" ({unread} unread)"
                else:
                    unread_num = ""
                print(f"[{i}] {other}{unread_num}")


            sel = input("Select a conversation (or press Enter to cancel): ").strip()
            if not sel.isdigit():
                continue

            idx = int(sel)
            if 1 <= idx <= len(conversations):
                other = conversations[idx - 1]

                # Open chat
                open_chat(current_user, other)
            else:
                print("Invalid choice.")

        elif choice == "2":
            all_users = get_all_usernames(users_dict)
            print("\nAvailable users:")
            for name in all_users:
                if name != current_user:
                    print("-", name)

            print("\n[B] Broadcast to all")
            print("[R] Broadcast to role (admin / scout leader / logistics coordinator)")
            print("[C] Broadcast to camp (leaders assigned)")
            recipient = input("\nSend message to (username or option): ").strip()

            if recipient.lower() == "b":
                text = input("Message: ").strip()
                if not text:
                    print("Message cannot be empty.")
                    continue
                send_broadcast(current_user, [u for u in all_users if u != current_user],
                               text, priority=_ask_priority())
                continue
            if recipient.lower() == "r":
                role = input("Role to broadcast to: ").strip().lower()
                targets = [u["username"] for u in users_dict.get(role, []) if isinstance(u, dict)]
                if not targets:
                    print("No recipients for that role.")
                    continue
                text = input("Message: ").strip()
                if not text:
                    print("Message cannot be empty.")
                    continue
                send_broadcast(current_user, targets, text, priority=_ask_priority())
                continue
            if recipient.lower() == "c":
                camps = read_from_file()
                if not camps:
                    print("No camps available.")
                    continue
                print("Camps:")
                for i, camp in enumerate(camps, start=1):
                    print(f"[{i}] {camp.name}")
                sel = input("Select camp number: ").strip()
                if not sel.isdigit():
                    continue
                idx = int(sel)
                if idx < 1 or idx > len(camps):
                    print("Invalid camp.")
                    continue
                camp = camps[idx-1]
                targets = _camp_recipients(camp.name)
                if not targets:
                    print("No leaders assigned to that camp.")
                    continue
                text = input("Message: ").strip()
                if not text:
                    print("Message cannot be empty.")
                    continue
                send_broadcast(current_user, targets, text, priority=_ask_priority(),
                               metadata={"camp": camp.name})
                continue

            if recipient not in all_users or recipient == current_user:
                print("Invalid recipient.")
                continue
            
            open_chat(current_user, recipient)

        elif choice == "3" and user_role == 'scout leader':  
            assigned_camps = []
            camps = read_from_file() 
            for camp in camps:
                if current_user in camp.scout_leaders:  
                    assigned_camps.append(camp)
            if not assigned_camps:
                print(f"{current_user} is not assigned to any camps.")
                continue
            open_group_chat(current_user, assigned_camps)

        elif choice == "3" and user_role != "scout leader" or choice == "4" and user_role == "scout leader":
            break
        else:
            print("Invalid choice. Please try again.")


def open_chat(current_user, other):
    """Show the conversation with `other` and let user send messages."""
    while True:
        mark_conversation_as_read(current_user, other)
        print(f"\n--- Chat with {other} ---")
        thread = get_conversation(current_user, other)

        if not thread:
            print("(no messages yet)")
        else:
            for msg in thread:
                who = "You" if msg["from"] == current_user else other
                flags = []
                if msg.get("priority"):
                    flags.append("PRIORITY")
                if msg.get("requires_ack") and not msg.get("acked"):
                    flags.append("ACK PENDING")
                if msg.get("pinned"):
                    flags.append("PINNED")
                flag_str = f" [{' | '.join(flags)}]" if flags else ""
                attach = msg.get("attachment")
                attach_str = f" [attachment: {attach}]" if attach else ""
                print(f"{msg['timestamp']} - {who}: {msg['text']}{flag_str}{attach_str}")

        print("\nOptions:")
        print("[1] Send a message")
        print("[2] Send a PRIORITY message (requires ACK)")
        print("[3] Search in this chat")
        print("[4] Export chat to file")
        print("[5] Acknowledge pending priority messages")
        print("[6] Pin/unpin latest message")
        print("[7] Refresh")
        print("[8] Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            _prompt_send(current_user, other, priority=False)
        elif choice == "2":
            _prompt_send(current_user, other, priority=True)
        elif choice == "3":
            _search_chat(current_user, other)
        elif choice == "4":
            path = input("Save to file (path): ").strip()
            if export_conversation(current_user, other, path):
                print(f"Saved to {path}")
            else:
                print("Failed to save.")
        elif choice == "5":
            updated = acknowledge_conversation(current_user, other)
            print(f"Acknowledged {updated} message(s).")
        elif choice == "6":
            toggled = _toggle_pin(current_user, other)
            if not toggled:
                print("No message to pin/unpin.")
        elif choice == "7":
            continue
        elif choice == "8":
            return
        else:
            print("Invalid choice.")


def _ask_priority() -> bool:
    flag = input("Mark as priority? (y/N): ").strip().lower()
    return flag == "y"


def _prompt_send(current_user: str, other: str, *, priority: bool):
    text = input("Message: ").strip()
    if not text:
        return
    attachment = input("Attachment path (optional, Enter to skip): ").strip()
    attachment = attachment or None
    send_message(current_user, other, text, priority=priority, attachment=attachment)


def _search_chat(current_user: str, other: str):
    query = input("Search text (leave blank for all): ").strip() or None
    date_from = input("Start date YYYY-MM-DD (optional): ").strip() or None
    date_to = input("End date YYYY-MM-DD (optional): ").strip() or None
    results = search_messages(current_user, query=query, other=other, date_from=date_from, date_to=date_to)
    print(f"\nFound {len(results)} message(s):")
    for msg in results:
        who = "You" if msg["from"] == current_user else other
        flags = []
        if msg.get("priority"):
            flags.append("PRIORITY")
        if msg.get("requires_ack") and not msg.get("acked"):
            flags.append("ACK PENDING")
        if msg.get("pinned"):
            flags.append("PINNED")
        extra = f" [{' | '.join(flags)}]" if flags else ""
        print(f"{msg['timestamp']} - {who}: {msg['text']}{extra}")


def _toggle_pin(current_user: str, other: str) -> bool:
    thread = get_conversation(current_user, other)
    if not thread:
        return False
    latest = thread[-1]
    now_pinned = not latest.get("pinned", False)
    ok = pin_message(current_user, other, latest.get("timestamp"), pinned=now_pinned)
    if ok:
        state = "Pinned" if now_pinned else "Unpinned"
        print(f"{state} latest message.")
    return ok


def open_group_chat(current_user, assigned_camps):
    """Display group chats for assigned camps and allow sending messages."""
    while True:
        print("\n--- Group Chats ---")
        for idx, camp in enumerate(assigned_camps, start=1):
            print(f"[{idx}] {camp.name} (Group Chat)")

        sel = input("Select a camp to view the group chat (or press Enter to cancel): ").strip()
        if not sel.isdigit():
            return  

        idx = int(sel)
        if 1 <= idx <= len(assigned_camps):
            selected_camp = assigned_camps[idx - 1]
            
            while True:  
                print(f"\n--- Group Chat for {selected_camp.name} ---")
                
                group_chat = selected_camp.get_group_chat()
                if not group_chat:
                    print("(No messages in the group chat yet.)")
                else:
                    for msg in group_chat:
                        print(f"{msg['timestamp']} - {msg['from']}: {msg['text']}")
                
                print("\nOptions:")
                print("[1] Send a message")
                print("[2] Refresh")
                print("[3] Back to camp selection")

                choice = input("Choose an option: ").strip()

                if choice == "1":
                    message = input("Message: ").strip()
                    if message:
                        selected_camp.message_group_chat(current_user, message)
                elif choice == "2":
                    continue
                elif choice == "3":
                    break  
                else:
                    print("Invalid choice. Please try again.")
        else:
            print("Invalid choice. Please select a valid camp.")
