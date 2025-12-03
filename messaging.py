# messaging.py

import json
import os
from datetime import datetime
from utils import data_path
from camp_class import read_from_file, save_to_file

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
    if other == None:
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


# ---------- core chat logic ----------

def send_message(sender, recipient, text):
    messages = load_messages()
    messages.append({
        "from": sender,
        "to": recipient,
        "text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
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
        print("[2] Start new chat")
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

            recipient = input("\nSend message to (username): ").strip()
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

