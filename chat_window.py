import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from messaging import (
    get_conversations_for_user,
    get_conversation,
    send_message,
    count_unread_messages,
    mark_conversation_as_read,
)
from user_logins import users
from camp_class import read_from_file


def _get_all_usernames():
    """Flatten user_logins.users into a simple list of usernames."""
    names = []
    for role_users in users.values():
        for u in role_users:
            if isinstance(u, dict) and "username" in u:
                names.append(u["username"])
    # unique + sorted
    return sorted(set(names))


def open_chat_window(master, username, role=None):
    """
    Reusable messaging window for ANY role.

    role: "admin", "scout leader", "logistics coordinator" (used only
          to decide whether to show the Group Chats button).
    """

    convo_win = tk.Toplevel(master)
    convo_win.title(f"Messaging – {username}")

    # Try to match parent bg if using themed frames
    try:
        bg = master.cget("bg")
    except Exception:
        bg = "#111827"
    convo_win.configure(bg=bg)

    frame = ttk.Frame(convo_win, padding=12, style="Card.TFrame")
    frame.pack(fill="both", expand=True)

    header = ttk.Label(frame, text="Messaging", style="Header.TLabel")
    header.pack(anchor="w", pady=(0, 4))

    # MAIN SPLIT: left = conversation list, right = chat
    main = ttk.Frame(frame, style="Card.TFrame")
    main.pack(fill="both", expand=True)

    # -------- LEFT: conversations + actions --------
    left_frame = ttk.Frame(main, style="Card.TFrame")
    left_frame.pack(side="left", fill="y", padx=(0, 8), pady=4)

    ttk.Label(left_frame, text="Conversations", style="FieldLabel.TLabel").pack(anchor="w")

    listbox = tk.Listbox(
        left_frame,
        height=18,
        width=24,
        bg="#0b1729",
        fg="#e5e7eb",
        selectbackground="#10b981",
        highlightthickness=0,
        relief="flat",
    )
    listbox.pack(side="left", fill="y", expand=False, pady=(4, 0))

    scroll = ttk.Scrollbar(left_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=scroll.set)
    scroll.pack(side="left", fill="y", pady=(4, 0))

    partners = []  # index -> username

    def refresh_conversation_list():
        partners.clear()
        listbox.delete(0, tk.END)
        convos = get_conversations_for_user(username)
        for other in convos:
            unread = count_unread_messages(username, other)
            label = other if unread == 0 else f"{other} ({unread})"
            partners.append(other)
            listbox.insert(tk.END, label)

    refresh_conversation_list()

    # New chat button
    def start_new_chat():
        all_users = [u for u in _get_all_usernames() if u != username]
        if not all_users:
            messagebox.showinfo("New Chat", "No other users available.")
            return

        dialog = tk.Toplevel(convo_win)
        dialog.title("Start New Chat")
        dialog.configure(bg=bg)

        outer = ttk.Frame(dialog, padding=12, style="Card.TFrame")
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Start a new chat", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(outer, text="Select a user to start chatting with:", style="Subtitle.TLabel").pack(anchor="w")

        lb = tk.Listbox(
            outer,
            height=min(10, len(all_users)),
            bg="#0b1729",
            fg="#e5e7eb",
            selectbackground="#10b981",
            highlightthickness=0,
            relief="flat",
        )
        lb.pack(fill="both", expand=True, pady=(6, 6))
        for name in all_users:
            lb.insert(tk.END, name)

        def choose():
            sel = lb.curselection()
            if not sel:
                messagebox.showerror("Error", "Please select a user.")
                return
            partner = lb.get(sel[0])
            # Ensure they appear in conversation list next refresh
            dialog.destroy()
            # Automatically open that chat (even if no previous messages)
            if partner not in partners:
                partners.append(partner)
                listbox.insert(tk.END, partner)
            # select it
            idx = partners.index(partner)
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(idx)
            listbox.event_generate("<<ListboxSelect>>")

        ttk.Button(outer, text="Start Chat", style="Primary.TButton", command=choose).pack(fill="x", pady=(4, 0))

    ttk.Button(left_frame, text="New Chat", command=start_new_chat).pack(fill="x", pady=(6, 0))

    # Group chats only for scout leaders (your design choice)
    if role == "scout leader":
        ttk.Button(left_frame, text="Group Chats", command=lambda: open_group_chat_window(master, username)).pack(
            fill="x", pady=(6, 0)
        )

    # -------- RIGHT: chat history + input --------
    right_frame = ttk.Frame(main, style="Card.TFrame")
    right_frame.pack(side="left", fill="both", expand=True, pady=4)

    chat_text = tk.Text(
        right_frame,
        bg="#0b1729",
        fg="#e5e7eb",
        wrap="word",
        state="disabled",
        height=18,
    )
    chat_text.pack(fill="both", expand=True, pady=(0, 6))

    entry = ttk.Entry(right_frame, style="App.TEntry")
    entry.pack(fill="x", pady=(0, 6))

    current_partner = tk.StringVar(value="")

    def refresh_chat(partner):
        # mark messages as read first
        mark_conversation_as_read(username, partner)

        thread = get_conversation(username, partner)

        chat_text.config(state="normal")
        chat_text.delete("1.0", tk.END)

        if not thread:
            chat_text.insert(tk.END, "(No messages yet – say hi!)\n")
        else:
            for msg in thread:
                who = "You" if msg["from"] == username else partner
                chat_text.insert(tk.END, f"{msg['timestamp']} - {who}: {msg['text']}\n")

        chat_text.config(state="disabled")
        refresh_conversation_list()  # update unread counters

    def send_current_message(event=None):
        partner = current_partner.get()
        if not partner:
            messagebox.showinfo("Messaging", "Select a conversation or start a new chat first.")
            return

        text = entry.get().strip()
        if not text:
            return

        send_message(username, partner, text)
        entry.delete(0, tk.END)
        refresh_chat(partner)

    ttk.Button(right_frame, text="Send", style="Primary.TButton", command=send_current_message).pack(fill="x")
    entry.bind("<Return>", send_current_message)

    # when user clicks another conversation
    def on_select(event):
        sel = listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(partners):
            return
        partner = partners[idx]
        current_partner.set(partner)
        refresh_chat(partner)

    listbox.bind("<<ListboxSelect>>", on_select)


def open_group_chat_window(master, username):
    """Separate window: group chats for camps supervised by this scout leader."""
    win = tk.Toplevel(master)
    win.title(f"Group Chats – {username}")
    try:
        bg = master.cget("bg")
    except Exception:
        bg = "#111827"
    win.configure(bg=bg)

    outer = ttk.Frame(win, padding=12, style="Card.TFrame")
    outer.pack(fill="both", expand=True)

    ttk.Label(outer, text="Camp Group Chats", style="Header.TLabel").pack(anchor="w", pady=(0, 4))
    ttk.Label(outer, text="Select a camp you supervise to view/send messages.", style="Subtitle.TLabel").pack(
        anchor="w", pady=(0, 6)
    )

    main = ttk.Frame(outer, style="Card.TFrame")
    main.pack(fill="both", expand=True, pady=(4, 0))

    # LEFT: camps list
    left = ttk.Frame(main, style="Card.TFrame")
    left.pack(side="left", fill="y", padx=(0, 8))

    camp_listbox = tk.Listbox(
        left,
        height=16,
        width=26,
        bg="#0b1729",
        fg="#e5e7eb",
        selectbackground="#10b981",
        highlightthickness=0,
        relief="flat",
    )
    camp_listbox.pack(side="left", fill="y", pady=(4, 0))

    camp_scroll = ttk.Scrollbar(left, orient="vertical", command=camp_listbox.yview)
    camp_listbox.configure(yscrollcommand=camp_scroll.set)
    camp_scroll.pack(side="left", fill="y", pady=(4, 0))

    # Gather camps supervised by this leader
    all_camps = read_from_file()
    assigned_camps = [c for c in all_camps if username in c.scout_leaders]

    for c in assigned_camps:
        camp_listbox.insert(tk.END, c.name)

    # RIGHT: group chat display
    right = ttk.Frame(main, style="Card.TFrame")
    right.pack(side="left", fill="both", expand=True)

    group_text = tk.Text(
        right,
        bg="#0b1729",
        fg="#e5e7eb",
        wrap="word",
        state="disabled",
        height=16,
    )
    group_text.pack(fill="both", expand=True, pady=(0, 6))

    msg_entry = ttk.Entry(right, style="App.TEntry")
    msg_entry.pack(fill="x", pady=(0, 6))

    current_camp_name = tk.StringVar(value="")

    def _get_camp_by_name(name):
        # Reload to pick up new messages from others
        camps = read_from_file()
        for c in camps:
            if c.name == name:
                return c
        return None

    def refresh_group_chat():
        name = current_camp_name.get()
        if not name:
            group_text.config(state="normal")
            group_text.delete("1.0", tk.END)
            group_text.insert(tk.END, "(Select a camp on the left.)\n")
            group_text.config(state="disabled")
            return

        camp = _get_camp_by_name(name)
        if not camp:
            group_text.config(state="normal")
            group_text.delete("1.0", tk.END)
            group_text.insert(tk.END, "(Camp not found anymore.)\n")
            group_text.config(state="disabled")
            return

        thread = camp.get_group_chat()

        group_text.config(state="normal")
        group_text.delete("1.0", tk.END)

        if not thread:
            group_text.insert(tk.END, "(No messages yet in this group.)\n")
        else:
            for msg in thread:
                who = msg.get("from", "Unknown")
                ts = msg.get("timestamp", "")
                txt = msg.get("text", "")
                group_text.insert(tk.END, f"{ts} - {who}: {txt}\n")

        group_text.config(state="disabled")

    def on_camp_select(event):
        sel = camp_listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(assigned_camps):
            return
        camp = assigned_camps[idx]
        current_camp_name.set(camp.name)
        refresh_group_chat()

    camp_listbox.bind("<<ListboxSelect>>", on_camp_select)

    def send_group_message(event=None):
        name = current_camp_name.get()
        if not name:
            messagebox.showinfo("Group Chat", "Select a camp first.")
            return
        text = msg_entry.get().strip()
        if not text:
            return

        camp = _get_camp_by_name(name)
        if not camp:
            messagebox.showerror("Error", "Camp not found; it may have been deleted.")
            return

        camp.message_group_chat(username, text)
        msg_entry.delete(0, tk.END)
        refresh_group_chat()

    ttk.Button(right, text="Send to Group", style="Primary.TButton", command=send_group_message).pack(fill="x")
    msg_entry.bind("<Return>", send_group_message)

    # Initial state
    refresh_group_chat()