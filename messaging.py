# messaging.py

import json
import os
from datetime import datetime
from utils import data_path

MESSAGES_FILE = data_path("messages.json")


# ---------- helpers to load/save ----------

def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return []

    try:
        with open(MESSAGES_FILE, "r") as f:
            data = json.load(f)
            return data.get("messages", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_messages(messages):
    data = {"messages": messages}
    with open(MESSAGES_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_all_usernames(users_dict):
    """Flatten your users structure into a simple list of usernames."""
    names = []

    # admin
    names.append(users_dict["admin"]["username"])

    # scout leaders
    for u in users_dict["scout leader"]:
        names.append(u["username"])

    # logistics coordinators
    for u in users_dict["logistics coordinator"]:
        names.append(u["username"])

    return names


# ---------- core chat logic ----------

def send_message(sender, recipient, text):
    messages = load_messages()
    messages.append({
        "from": sender,
        "to": recipient,
        "text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_messages(messages)


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


# ---------- menu shown to a logged-in user ----------

def messaging_menu(current_user, users_dict):
    """WhatsApp-style CLI chat for a single logged-in user."""
    while True:
        print("\n--- Messaging ---")
        print("[1] View conversations")
        print("[2] Start new chat")
        print("[3] Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            conversations = get_conversations_for_user(current_user)
            if not conversations:
                print("\nNo conversations yet. Start a new chat!")
                continue

            print("\nYour conversations:")
            for i, other in enumerate(conversations, start=1):
                print(f"[{i}] {other}")

            sel = input("Select a conversation (or press Enter to cancel): ").strip()
            if not sel.isdigit():
                continue

            idx = int(sel)
            if 1 <= idx <= len(conversations):
                other = conversations[idx - 1]
                open_chat(current_user, other)
            else:
                print("Invalid choice.")

        elif choice == "2":
            all_users = get_all_usernames(users_dict)
            print("\nAvailable users:")
            for name in all_users:
                if name != current_user:
                    print("-", name)

            recipient = input("\nSend message to (username): ").strip()
            if recipient not in all_users or recipient == current_user:
                print("Invalid recipient.")
                continue

            open_chat(current_user, recipient)

        elif choice == "3":
            return

        else:
            print("Invalid choice. Please try again.")


def open_chat(current_user, other):
    """Show the conversation with `other` and let user send messages."""
    while True:
        print(f"\n--- Chat with {other} ---")
        thread = get_conversation(current_user, other)

        if not thread:
            print("(no messages yet)")
        else:
            for msg in thread:
                who = "You" if msg["from"] == current_user else other
                print(f"{msg['timestamp']} - {who}: {msg['text']}")

        print("\nOptions:")
        print("[1] Send a message")
        print("[2] Refresh")
        print("[3] Back")

        choice = input("Choose: ").strip()

        if choice == "1":
            text = input("Message: ").strip()
            if text:
                send_message(current_user, other, text)
        elif choice == "2":
            continue
        elif choice == "3":
            return
        else:
            print("Invalid choice.")
