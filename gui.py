import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from datetime import datetime,timedelta
try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
from chat_window import open_chat_window, open_group_chat_window
from user_logins import users, load_logins, check_disabled_logins, save_logins, disabled_logins, enable_login
from features.admin import list_users
from camp_class import Camp, save_to_file, read_from_file
from features.logistics import (
    set_food_stock_data,
    top_up_food_data,
    set_pay_rate_data,
    compute_food_shortage,
    build_dashboard_data,
    plot_food_stock,
    plot_camper_distribution,
    plot_leaders_per_camp,
    plot_engagement_scores,
)
from features.notifications import (
    load_notifications,
    mark_all_as_read,
    add_notification,
    clear_notifications,
    delete_notifications_for_user,
    count_unread,
    mute_category,
    unmute_category,
    get_thresholds,
    set_thresholds,
)
from features.scout import (
    assign_camps_to_leader,
    bulk_assign_campers_from_csv,
    assign_food_amount_pure,
    record_activity_entry_data,
    activity_participation_data,
    engagement_scores_data,
    money_earned_per_camp_data,
    total_money_earned_value,
    activity_stats_data,
    find_camp_by_name,
    record_incident_entry_data,
    camps_overlap,
)
from messaging import get_conversations_for_user, get_conversation, send_message

LOGO_GREEN = "#487C56"       # match logo green
THEME_BG = "#0b1f36"         # window background
THEME_CARD = "#12263f"       # card background
THEME_CARD_ALT = "#102034"   # slight contrast for inner cards
THEME_FG = "#e6f1ff"         # main text
THEME_MUTED = "#cbd5f5"      # subtle/secondary text
THEME_ACCENT = LOGO_GREEN    # primary accent now matches logo
THEME_ACCENT_ACTIVE = "#43a047"
THEME_ACCENT_PRESSED = "#388e3c"
THEME_BORDER = "#1f2d44"
SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 18, "xl": 24}
LOGISTICS_NOTIF_CATEGORIES = {"FOOD", "RESOURCE"}  # coordinator sees resource/shortage alerts only


def _read_disabled_usernames():
    try:
        with open('disabled_logins.txt', 'r') as file:
            disabled = file.read().strip(',')
            return {u for u in disabled.split(',') if u}
    except FileNotFoundError:
        return set()


def _pill(parent, title, value, desc=""):
    """Compact summary pill for clarity."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=8)
    card.pack(side="left", expand=True, fill="x", padx=4)
    ttk.Label(card, text=title, style="FieldLabel.TLabel").pack(anchor="w")
    ttk.Label(card, text=value, style="Header.TLabel").pack(anchor="w")
    if desc:
        ttk.Label(card, text=desc, style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))
    return card


def _inline_error(frame, message):
    """Inline error text helper."""
    lbl = ttk.Label(frame, text=message, style="Error.TLabel")
    lbl.pack(anchor="w", pady=(2, 0))
    return lbl


def build_button_row(parent, buttons, style="Card.TFrame", padx=4, pady=4):
    """Create a horizontal row of buttons. buttons: list of (text, command, style_name)."""
    row = ttk.Frame(parent, style=style)
    row.pack(fill="x")
    for text, cmd, btn_style in buttons:
        ttk.Button(row, text=text, command=cmd, style=btn_style or "TButton").pack(
            side="left", padx=padx, pady=pady
        )
    return row


def _build_shell(master, username, role, sections):
    """
    Create a shell with left navigation and right content area.
    sections: list of (label, callback) entries for nav.
    Returns (content_frame, nav_frame).
    """
    outer = ttk.Frame(master, padding=0, style="App.TFrame")
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(1, weight=1)
    outer.rowconfigure(0, weight=1)

    # LEFT NAV
    nav = ttk.Frame(outer, padding=(SPACING["md"], SPACING["lg"]), style="Card.TFrame")
    nav.grid(row=0, column=0, sticky="ns")
    nav.columnconfigure(0, weight=1)
    logo = load_logo(56)
    if logo:
        ttk.Label(nav, image=logo, background=THEME_CARD).grid(row=0, column=0, sticky="w", pady=(0, SPACING["md"]))
        nav.logo_ref = logo  # keep reference
    ttk.Label(nav, text=f"{role.title()}", style="Header.TLabel").grid(row=1, column=0, sticky="w")
    ttk.Label(nav, text=f"Signed in as {username}", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", pady=(0, SPACING["md"]))

    nav_buttons = []
    nav_map = {}
    for idx, (label, callback) in enumerate(sections, start=3):
        btn = ttk.Button(nav, text=label, command=callback, style="Ghost.TButton")
        btn.grid(row=idx, column=0, sticky="ew", pady=3)
        nav_buttons.append(btn)
        nav_map[label] = btn

    # RIGHT CONTENT
    content = ttk.Frame(outer, padding=SPACING["lg"], style="App.TFrame")
    content.grid(row=0, column=1, sticky="nsew")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(1, weight=1)
    return content, nav, nav_buttons, nav_map


def _init_nav_with_badge(owner, username, role, sections, notif_filter=None):
    """Build nav shell, wire notification badge updater, and return (content, nav)."""
    content, nav, nav_buttons, nav_map = _build_shell(owner, username, role, sections)
    owner._nav_buttons = nav_buttons
    owner._nav_map = nav_map
    owner._notif_filter = notif_filter

    def refresh_badge():
        unread = count_unread(username, filter_fn=owner._notif_filter)
        btn = owner._nav_map.get("Notifications")
        if not btn:
            return
        btn.config(text="Notifications" if unread == 0 else f"Notifications ({unread})")

    owner._refresh_notification_badge = refresh_badge
    owner._refresh_notification_badge()
    return content, nav


def open_notifications_window(master, refresh_badge_cb=None, filter_fn=None, username=None, show_buffer_control=False):
    """Reusable notifications window with filters, search, grouping, and actions."""
    notif_win = tk.Toplevel(master)
    notif_win.title("Notifications")
    notif_win.configure(bg=THEME_BG)
    notif_win.minsize(700, 520)
    center_window(notif_win, width=900, height=520)
    frame = ttk.Frame(notif_win, padding=16, style="Card.TFrame")
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Notifications", style="Header.TLabel").pack(pady=(0, 6), anchor="w")
    ttk.Separator(frame).pack(fill="x", pady=(0, 8))

    controls = ttk.Frame(frame, style="Card.TFrame")
    controls.pack(fill="x", pady=(0, 6))
    ttk.Label(controls, text="Level:", style="FieldLabel.TLabel").pack(side="left")
    level_var = tk.StringVar(value="ALL")
    ttk.Combobox(controls, values=["ALL", "SUCCESS", "INFO", "ALERT", "CRITICAL"], textvariable=level_var, state="readonly", width=12).pack(side="left", padx=(4, 12))
    # Default to showing unread first so cleared items stay hidden unless user opts in.
    unread_only = tk.BooleanVar(value=True if username else False)
    ttk.Checkbutton(controls, text="Unread only", variable=unread_only).pack(side="left")
    group_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(controls, text="Group similar", variable=group_var).pack(side="left", padx=(8, 0))
    ttk.Label(controls, text="Search:", style="FieldLabel.TLabel").pack(side="left", padx=(12, 4))
    search_var = tk.StringVar(value="")
    ttk.Entry(controls, textvariable=search_var, style="App.TEntry", width=24).pack(side="left")
    ttk.Button(controls, text="Refresh", command=lambda: refresh_list()).pack(side="left", padx=(8, 0))
    ttk.Button(controls, text="Mark all read", command=lambda: mark_all()).pack(side="left", padx=(8, 0))

    action_bar = ttk.Frame(frame, style="Card.TFrame")
    action_bar.pack(fill="x", pady=(0, 6))
    ttk.Button(action_bar, text="Open Context", command=lambda: open_context()).pack(side="left", padx=(0, 6))
    ttk.Button(action_bar, text="Mute Category 1h", command=lambda: mute_selected(60)).pack(side="left", padx=(0, 6))
    ttk.Button(action_bar, text="Unmute Category", command=lambda: mute_selected(0)).pack(side="left", padx=(0, 6))
    if show_buffer_control:
        ttk.Button(action_bar, text="Set Warning Buffer", command=lambda: set_buffer()).pack(side="left", padx=(0, 6))
    ttk.Button(action_bar, text="Clear All", command=lambda: clear_all()).pack(side="left", padx=(0, 6))

    lb_frame = ttk.Frame(frame, style="Card.TFrame")
    lb_frame.pack(fill="both", expand=True, pady=6)
    listbox = tk.Listbox(
        lb_frame,
        bg=THEME_CARD,
        fg=THEME_FG,
        selectbackground=THEME_ACCENT,
        highlightthickness=0,
        relief="flat",
    )
    scrollbar = ttk.Scrollbar(lb_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=scrollbar.set)
    listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
    scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)

    current_items = []

    def refresh_list():
        nonlocal current_items
        listbox.delete(0, "end")
        notes = load_notifications(username=username)
        if filter_fn:
            notes = [n for n in notes if filter_fn(n)]
        filtered = []
        level_choice = level_var.get()
        query = search_var.get().lower().strip()
        for n in notes:
            if unread_only.get() and n.get("read"):
                continue
            if level_choice != "ALL" and n.get("level") != level_choice:
                continue
            if query and query not in n.get("message", "").lower():
                continue
            filtered.append(n)

        if group_var.get():
            grouped = {}
            for n in filtered:
                key = (n.get("level"), n.get("category"), n.get("message"))
                grouped.setdefault(key, {"sample": n, "count": 0})
                grouped[key]["count"] += 1
            current_items = []
            if not grouped:
                listbox.insert("end", "No notifications.")
            else:
                for (lvl, cat, msg), info in grouped.items():
                    count = info["count"]
                    prefix = f"*{cat.upper()}* : *{lvl.upper()}*"
                    line = f"{prefix} x{count} - {msg}"
                    listbox.insert("end", line)
                    current_items.append({"group": True, "count": count, **info["sample"]})
        else:
            current_items = filtered
            if not filtered:
                listbox.insert("end", "No notifications.")
            else:
                for n in filtered:
                    timestamp = n.get("timestamp", "")
                    message = n.get("message", "")
                    level = n.get("level", "INFO")
                    cat = n.get("category", "GENERAL")
                    prefix = f"*{cat.upper()}* : *{level.upper()}*"
                    line = f"{prefix} - {timestamp} - {message}" if timestamp else f"{prefix} - {message}"
                    listbox.insert("end", line)

    def mark_all():
        if username:
            mark_all_as_read(username)
        if refresh_badge_cb:
            refresh_badge_cb()
        refresh_list()

    def set_buffer():
        cur = get_thresholds().get("shortage_warning_buffer", 0.15)
        val = simpledialog.askstring("Warning Buffer", f"Set shortage warning buffer (current: {cur:.2f})", parent=notif_win)
        if val is None:
            return
        try:
            set_thresholds(float(val))
            messagebox.showinfo("Saved", "Warning buffer updated.")
        except ValueError:
            show_error_toast(master, "Error", "Enter a number like 0.15 for 15%.")

    def clear_all():
        if not messagebox.askyesno("Confirm", "Clear all notifications?"):
            return
        if not username:
            show_error_toast(master, "Clear", "No user context available.")
            return
        delete_notifications_for_user(username)
        unread_only.set(True)
        if refresh_badge_cb:
            refresh_badge_cb()
        refresh_list()
        messagebox.showinfo("Notifications", "All notifications cleared for you.")

    def get_selected():
        sel = listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if idx >= len(current_items):
            return None
        item = current_items[idx]
        if item.get("group"):
            return None
        return item

    def open_context():
        item = get_selected()
        if not item:
            show_error_toast(master, "Context", "Select a single notification with context.")
            return
        ctx = item.get("context") or {}
        if "camp" in ctx:
            messagebox.showinfo("Context", f"Open camp: {ctx.get('camp')}")
        else:
            messagebox.showinfo("Context", "No linked action for this notification.")

    def mute_selected(minutes=60):
        item = get_selected()
        if not item:
            show_error_toast(master, "Mute", "Select a notification first.")
            return
        cat = item.get("category", "GENERAL")
        if minutes == 0:
            unmute_category(cat)
            messagebox.showinfo("Mute", f"Unmuted {cat}.")
        else:
            mute_category(cat, minutes=minutes)
            messagebox.showinfo("Mute", f"Muted {cat} for {minutes} minute(s).")
        refresh_list()

    refresh_list()
    center_in_place(notif_win)


def _unread_count(filter_fn=None, username=None):
    notes = load_notifications(username=username)
    if filter_fn:
        notes = [n for n in notes if filter_fn(n)]
    return len([n for n in notes if not n.get("read_by") or (username and username not in n.get("read_by"))])


def show_error_toast(master, title, message, duration=2000):
    """Non-blocking error popup so animations keep running."""
    top = tk.Toplevel(master)
    top.overrideredirect(True)
    top.wm_attributes("-topmost", True)
    top.configure(bg=THEME_BG)

    outer = tk.Frame(top, bg=THEME_BG, bd=0)
    outer.pack(fill="both", expand=True, padx=6, pady=6)

    card = ttk.Frame(outer, padding=14, style="Card.TFrame")
    card.pack(fill="both", expand=True)

    # accent bar and icon for a more polished look
    bar = tk.Frame(card, bg="#dc2626", height=3, bd=0, highlightthickness=0)
    bar.pack(fill="x", side="top", pady=(0, 10))

    header_row = tk.Frame(card, bg=THEME_CARD, bd=0, highlightthickness=0)
    header_row.pack(fill="x", pady=(0, 6))
    tk.Label(header_row, text="⚠", bg=THEME_CARD, fg="#fca5a5", font=("Helvetica", 14, "bold")).pack(side="left", padx=(0, 8))
    ttk.Label(header_row, text=title, style="Header.TLabel").pack(side="left")

    ttk.Label(card, text=message, style="Subtitle.TLabel", wraplength=340, justify="left").pack(anchor="w")

    top.update_idletasks()
    x = master.winfo_rootx() + (master.winfo_width() // 2) - (top.winfo_width() // 2)
    y = master.winfo_rooty() + 80
    top.geometry(f"+{x}+{y}")
    top.after(duration, top.destroy)


def load_logo(max_px=260):
    if Image is None or ImageTk is None:
        return None
    logo_path = os.path.join(os.path.dirname(__file__), "image.png")
    if not os.path.exists(logo_path):
        return None
    try:
        with Image.open(logo_path) as im:
            im.thumbnail((max_px, max_px), Image.LANCZOS)
            return ImageTk.PhotoImage(im)
    except Exception:
        return None


def parse_date_flexible(text):
    """Parse a date string into YYYY-MM-DD, allowing common human formats."""
    text = text.strip()
    if not text:
        raise ValueError("blank date")
    if date_parser:
        try:
            return date_parser.parse(text, fuzzy=True).date().strftime("%Y-%m-%d")
        except Exception:
            pass
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date().strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError("invalid date")

class LoginWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=0, style="App.TFrame")
        self.master = master
        self.pack(fill="both", expand=True)

        # center the login form in a padded, fixed-width container
        card = ttk.Frame(self, padding=24, width=420, style="Card.TFrame")
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.columnconfigure(0, weight=1)

        row = 0
        self.logo_img = load_logo(260)
        if self.logo_img:
            tk.Label(
                card,
                image=self.logo_img,
                bg=THEME_CARD,
                borderwidth=0,
                highlightthickness=0,
            ).grid(row=row, column=0, pady=(0, 12), sticky="n")
            row += 1

        ttk.Label(card, text="Welcome! Log in below.", style="Subtitle.TLabel").grid(row=row, column=0, pady=(0, 10), sticky="n")
        row += 1

        ttk.Separator(card, orient="horizontal").grid(row=row, column=0, sticky="ew", pady=(0, 8))
        row += 1

        ttk.Label(card, text="Username", style="FieldLabel.TLabel").grid(row=row, column=0, sticky="w", padx=2)
        row += 1
        self.username = tk.Entry(
            card,
            width=32,
            bg="#0b1729",
            fg=THEME_FG,
            insertbackground=THEME_FG,
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            font=("Helvetica", 11),
        )
        self.username.grid(row=row, column=0, sticky="ew", pady=(0, 10), ipady=6, padx=8)
        row += 1

        ttk.Label(card, text="Password", style="FieldLabel.TLabel").grid(row=row, column=0, sticky="w", padx=2)
        row += 1
        self.password = tk.Entry(
            card,
            show="*",
            width=32,
            bg="#0b1729",
            fg=THEME_FG,
            insertbackground=THEME_FG,
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            font=("Helvetica", 11),
        )
        self.password.grid(row=row, column=0, sticky="ew", pady=(0, 4), ipady=6, padx=8)
        row += 1

        ttk.Button(
            card,
            text="Login",
            command=self.attempt_login,
            style="Primary.TButton",
        ).grid(row=row, column=0, pady=(16, 0), sticky="ew")

    def attempt_login(self):
        state_info = capture_window_state(self.master)

        uname = self.username.get().strip()
        pwd = self.password.get()
        load_logins()
        if check_disabled_logins(uname):
            show_error_toast(self.master, "Login failed", "This account has been disabled.")
            return
        role = None
        for u in users["admin"]:
            if u["username"] == uname and u["password"] == pwd:
                role = "admin"
                break
        if role is None:
            for u in users["scout leader"]:
                if u["username"] == uname and u["password"] == pwd:
                    role = "scout leader"
                    break
        if role is None:
            for u in users["logistics coordinator"]:
                if u["username"] == uname and u["password"] == pwd:
                    role = "logistics coordinator"
                    break
        if role:
            root = self.master
            for child in list(root.winfo_children()):
                child.destroy()
            root.configure(bg=THEME_BG)
            root.title(f"CampTrack - {role}")
            init_style(root)
            restore_geometry(root, state_info, min_w=1040, min_h=820)
            if role == "admin":
                AdminWindow(root, uname)
            elif role == "scout leader":
                ScoutWindow(root, uname)
            elif role == "logistics coordinator":
                LogisticsWindow(root, uname)
        else:
            show_error_toast(self.master, "Login Failed", "Invalid username or password.")


class AdminWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=0, style="App.TFrame")
        self.username = username
        self.pack(fill="both", expand=True)

        content, nav = _init_nav_with_badge(
            self,
            username,
            "Administrator",
            [
                ("Dashboard", self._focus_dashboard),
                ("User Management", self.list_users_ui),
                ("Notifications", self.notifications_ui),
                ("Messaging", self.messaging_ui),
                ("Logout", self.logout),
            ],
            notif_filter=None,  # admin sees all levels
        )

        # HERO
        hero = ttk.Frame(content, style="Card.TFrame", padding=SPACING["lg"])
        hero.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        hero.columnconfigure(1, weight=1)
        logo = load_logo(80)
        if logo:
            ttk.Label(hero, image=logo, background=THEME_CARD).grid(row=0, column=0, rowspan=3, sticky="w", padx=(0, SPACING["md"]))
            hero.logo_ref = logo
        ttk.Label(hero, text="Administrator Console", style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(hero, text="Create and manage accounts, monitor access, and open messaging.", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")
        ttk.Button(hero, text="Open Messaging", command=self.messaging_ui, style="Primary.TButton").grid(row=2, column=1, sticky="w", pady=(SPACING["sm"], 0))

        # SUMMARY
        summary = ttk.Frame(content, style="Card.TFrame")
        summary.grid(row=1, column=0, sticky="ew", pady=(0, SPACING["md"]))
        disabled = _read_disabled_usernames()
        _pill(summary, "Admins", str(len(users["admin"])), "Total admin accounts")
        _pill(summary, "Leaders", str(len(users["scout leader"])), "Scout leaders")
        _pill(summary, "Coordinators", str(len(users["logistics coordinator"])), "Logistics coordinators")
        _pill(summary, "Disabled", str(len(disabled)), "Disabled accounts")

        # GRID LAYOUT
        main = ttk.Frame(content, style="App.TFrame")
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        user_frame = ttk.LabelFrame(main, text="User Management", padding=SPACING["md"], style="Card.TFrame")
        user_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["md"]), pady=(0, SPACING["md"]))
        for text, cmd in [
            ("View all users", self.list_users_ui),
        ]:
            btn_style = "TButton"
            ttk.Button(user_frame, text=text, command=cmd, style=btn_style).pack(fill="x", pady=2)

        other = ttk.LabelFrame(main, text="Quick Actions", padding=SPACING["md"], style="Card.TFrame")
        other.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["md"]))
        ttk.Label(other, text="Messaging", style="Header.TLabel").pack(anchor="w")
        ttk.Label(other, text="Open direct and group chats.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, SPACING["sm"]))
        ttk.Button(other, text="Open Messaging", command=self.messaging_ui, style="Primary.TButton").pack(fill="x", pady=(0, SPACING["md"]))
        ttk.Separator(other).pack(fill="x", pady=(SPACING["sm"], SPACING["sm"]))
        ttk.Button(other, text="Logout", command=self.logout, style="Danger.TButton").pack(fill="x")

    def _focus_dashboard(self):
        # Admin dashboard is the default view; show a quick note so the nav click feels responsive.
        messagebox.showinfo("Dashboard", "You’re already on the admin dashboard.")

    def notifications_ui(self):
        open_notifications_window(
            self,
            refresh_badge_cb=self._refresh_notification_badge,
            filter_fn=self._notif_filter,
            username=self.username,
            show_buffer_control=False,
        )

    def list_users_ui(self):
        top = tk.Toplevel(self)
        top.title("All Users")
        top.configure(bg=THEME_BG)
        center_window(top, width=900, height=640)
        center_window(top, width=900, height=640)
        frame = ttk.Frame(top, padding=16, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        header = ttk.Frame(frame, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="All Users", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Admin, Scout Leader, Logistics Coordinator", style="Subtitle.TLabel").pack(anchor="w")
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))

        search_row = ttk.Frame(frame, style="Card.TFrame")
        search_row.pack(fill="x", pady=(0, 8))
        search_row.columnconfigure(1, weight=1)
        ttk.Label(search_row, text="Search users", style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=search_var, style="App.TEntry")
        search_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(search_row, text="Add user", command=lambda: self.add_user_ui(on_added=refresh_tree), style="Primary.TButton").grid(row=0, column=2, padx=(8, 0))

        # load disabled usernames
        columns = ("Role", "Username", "Password", "Status")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col in columns:
            anchor = "center" if col != "Username" else "w"
            tree.heading(col, text=col)
            tree.column(col, anchor=anchor, width=160 if col != "Username" else 200, stretch=True)

        vsb = None
        tree.pack(fill="both", expand=True, pady=(0, 4))

        def refresh_scrollbar(*_):
            # show scrollbar only if rows exceed visible area
            nonlocal vsb
            h = tree.winfo_height()
            if h <= 5:
                return  # defer until layout is ready
            visible = max(int(h / 20), 1)
            if len(tree.get_children()) > visible:
                if vsb is None or not vsb.winfo_exists():
                    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=vsb.set)
                if not vsb.winfo_ismapped():
                    vsb.pack(fill="y", side="right")
            else:
                tree.configure(yscrollcommand=None)
                if vsb is not None and vsb.winfo_exists() and vsb.winfo_ismapped():
                    vsb.pack_forget()
                # do not show a hidden scrollbar
                vsb = vsb

        tree.bind("<Configure>", refresh_scrollbar)
        tree.after_idle(refresh_scrollbar)

        class UserListController:
            def __init__(self, parent, tree, search_var, refresh_scroll_cb):
                self.parent = parent
                self.tree = tree
                self.search_var = search_var
                self.refresh_scroll_cb = refresh_scroll_cb

            def load_disabled_set(self):
                try:
                    with open('disabled_logins.txt', 'r') as file:
                        disabled_login = file.read().strip(',')
                        if disabled_login:
                            return {x for x in disabled_login.split(',') if x}
                except FileNotFoundError:
                    pass
                return set()

            def save_disabled_set(self, s):
                with open('disabled_logins.txt', 'w') as f:
                    f.write(",".join(sorted(s)))

            def ensure_unique_username(self, name):
                existing = {u['username'] for u in users['admin']}
                existing |= {u['username'] for u in users['scout leader']}
                existing |= {u['username'] for u in users['logistics coordinator']}
                return name not in existing

            def add_row(self, role, user, ds):
                status = "Disabled" if user['username'] in ds else "Active"
                self.tree.insert("", "end", values=(role, user['username'], user['password'], status))

            def refresh_tree(self, *_):
                for child in self.tree.get_children():
                    self.tree.delete(child)
                ds = self.load_disabled_set()
                term = self.search_var.get().strip().lower()

                def matches(role_label, username):
                    status = "Disabled" if username in ds else "Active"
                    if not term:
                        return True
                    text = f"{role_label} {username} {status}".lower()
                    return term in text

                for admin in users['admin']:
                    if matches("Admin", admin['username']):
                        self.add_row("Admin", admin, ds)
                for role in ['scout leader', 'logistics coordinator']:
                    for user in users[role]:
                        role_label = role.title()
                        if matches(role_label, user['username']):
                            self.add_row(role_label, user, ds)
                if len(self.tree.get_children()) == 0:
                    msg = "No users found." if not term else "No matches for search."
                    self.tree.insert("", "end", values=("—", msg, "", ""))
                self.refresh_scroll_cb()
                self.tree.after_idle(self.refresh_scroll_cb)

            def get_selected(self):
                sel = self.tree.selection()
                if not sel:
                    show_error_toast(self.parent.master, "Error", "Please select a user.")
                    return None
                vals = self.tree.item(sel[0], "values")
                if not vals or vals[0] == "—":
                    show_error_toast(self.parent.master, "Error", "Please select a valid user.")
                    return None
                return {"role": vals[0], "username": vals[1], "password": vals[2], "item": sel[0]}

            def edit_password(self):
                sel = self.get_selected()
                if not sel:
                    return
                dlg = tk.Toplevel(self.parent)
                dlg.title("Edit Password")
                dlg.configure(bg=THEME_BG)
                center_window(dlg, width=520, height=360)
                frame_inner = ttk.Frame(dlg, padding=14, style="Card.TFrame")
                frame_inner.pack(fill="both", expand=True, padx=12, pady=12)
                ttk.Label(frame_inner, text=f"Edit password for {sel['username']}", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
                ttk.Separator(frame_inner).pack(fill="x", pady=(0, 8))
                ttk.Label(frame_inner, text="New password", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
                pwd_entry = ttk.Entry(frame_inner, style="App.TEntry", show="*")
                pwd_entry.pack(fill="x", pady=(0, 10))

                def submit():
                    new_pwd = pwd_entry.get()
                    role_key = sel['role'].lower()
                    for u in users[role_key]:
                        if u['username'] == sel['username']:
                            u['password'] = new_pwd
                            break
                    save_logins()
                    add_notification(
                        f"[Admin: {self.parent.username}] Changed password for user '{sel['username']}'",
                        level="WARNING")
                    self.refresh_tree()
                    dlg.destroy()

                build_button_row(
                    frame_inner,
                    [
                        ("Save", submit, "Primary.TButton"),
                        ("Cancel", dlg.destroy, None),
                    ],
                )
                center_in_place(dlg)
                dlg.grab_set()

            def delete_user(self):
                sel = self.get_selected()
                if not sel:
                    return
                if not messagebox.askyesno("Delete", f"Delete user {sel['username']}?"):
                    return
                role_key = sel['role'].lower()
                users[role_key] = [u for u in users[role_key] if u['username'] != sel['username']]
                ds = self.load_disabled_set()
                if sel['username'] in ds:
                    ds.remove(sel['username'])
                    self.save_disabled_set(ds)
                add_notification(
                    f"[Admin: {self.parent.username}] Deleted user '{sel['username']}'",
                    level="CRITICAL")
                save_logins()
                self.refresh_tree()

            def toggle_disable(self, enable=False):
                sel = self.get_selected()
                if not sel:
                    return
                ds = self.load_disabled_set()
                if enable:
                    if sel['username'] in ds:
                        ds.remove(sel['username'])
                        self.save_disabled_set(ds)
                    enable_login(sel['username'])
                else:
                    disabled_logins(sel['username'])
                    ds.add(sel['username'])
                    self.save_disabled_set(ds)
                self.refresh_tree()

            def change_username(self):
                sel = self.get_selected()
                if not sel:
                    return
                dlg = tk.Toplevel(self.parent)
                dlg.title("Change Username")
                dlg.configure(bg=THEME_BG)
                center_window(dlg, width=520, height=360)
                frame_inner = ttk.Frame(dlg, padding=14, style="Card.TFrame")
                frame_inner.pack(fill="both", expand=True, padx=12, pady=12)
                ttk.Label(frame_inner, text=f"Change username for {sel['username']}", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
                ttk.Separator(frame_inner).pack(fill="x", pady=(0, 8))
                ttk.Label(frame_inner, text="New username", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
                name_entry = ttk.Entry(frame_inner, style="App.TEntry")
                name_entry.insert(0, sel['username'])
                name_entry.pack(fill="x", pady=(0, 10))

                def submit():
                    new_name = name_entry.get().strip()
                    if not new_name:
                        show_error_toast(self.parent.master, "Error", "Username cannot be blank.")
                        return
                    if not self.ensure_unique_username(new_name):
                        show_error_toast(self.parent.master, "Error", "Username already exists.")
                        return
                    role_key = sel['role'].lower()
                    for u in users[role_key]:
                        if u['username'] == sel['username']:
                            u['username'] = new_name
                            break
                    ds = self.load_disabled_set()
                    if sel['username'] in ds:
                        ds.remove(sel['username'])
                        ds.add(new_name)
                        self.save_disabled_set(ds)
                    save_logins()
                    self.refresh_tree()
                    dlg.destroy()

                build_button_row(
                    frame_inner,
                    [
                        ("Save", submit, "Primary.TButton"),
                        ("Cancel", dlg.destroy, None),
                    ],
                )
                center_in_place(dlg)
                dlg.grab_set()

            def change_role(self):
                sel = self.get_selected()
                if not sel:
                    return
                current = sel['role'].lower()
                roles = ["admin", "scout leader", "logistics coordinator"]
                dlg = tk.Toplevel(self.parent)
                dlg.title("Change Role")
                dlg.configure(bg=THEME_BG)
                center_window(dlg, width=520, height=360)
                frame_inner = ttk.Frame(dlg, padding=14, style="Card.TFrame")
                frame_inner.pack(fill="both", expand=True, padx=12, pady=12)
                ttk.Label(frame_inner, text=f"Change role for {sel['username']}", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
                ttk.Separator(frame_inner).pack(fill="x", pady=(0, 8))
                ttk.Label(frame_inner, text="New role", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
                role_var = tk.StringVar(value=current)
                ttk.OptionMenu(frame_inner, role_var, current, *roles).pack(fill="x", pady=(0, 10))

                def submit():
                    choice = role_var.get()
                    if choice == current:
                        dlg.destroy()
                        return
                    if any(u['username'] == sel['username'] for u in users[choice]):
                        show_error_toast(self.parent.master, "Error", "Username already exists in target role.")
                        return
                    user_rec = None
                    for u in users[current]:
                        if u['username'] == sel['username']:
                            user_rec = u
                            break
                    if user_rec:
                        users[current] = [u for u in users[current] if u['username'] != sel['username']]
                        users[choice].append(user_rec)
                        save_logins()
                        self.refresh_tree()
                    dlg.destroy()

                build_button_row(
                    frame_inner,
                    [
                        ("Save", submit, "Primary.TButton"),
                        ("Cancel", dlg.destroy, None),
                    ],
                )
                center_in_place(dlg)
                dlg.grab_set()

        controller = UserListController(self, tree, search_var, refresh_scrollbar)

        # action buttons
        btn_frame = ttk.Frame(frame, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="Edit Password", command=controller.edit_password).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Change Username", command=controller.change_username).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Change Role", command=controller.change_role).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Disable", command=lambda: controller.toggle_disable(False), style="Danger.TButton").pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Enable", command=lambda: controller.toggle_disable(True)).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Delete", command=controller.delete_user, style="Danger.TButton").pack(side="left", padx=4, pady=2)

        controller.refresh_tree()
        search_var.trace_add("write", controller.refresh_tree)
        search_entry.focus_set()
        center_in_place(top)

    def add_user_ui(self, on_added=None):
        top = tk.Toplevel(self)
        top.title("Add User")
        top.configure(bg=THEME_BG)
        center_window(top, width=520, height=420)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Add a new user", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        roles = ["admin", "scout leader", "logistics coordinator"]
        role_var = tk.StringVar(value=roles[0])
        ttk.Label(frame, text="Role", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        ttk.OptionMenu(frame, role_var, roles[0], *roles).pack(fill="x", pady=(0, 8))

        ttk.Label(frame, text="Username", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        user_entry = ttk.Entry(frame, style="App.TEntry")
        user_entry.pack(fill="x", pady=(0, 8))

        ttk.Label(frame, text="Password (optional)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        pwd_entry = ttk.Entry(frame, style="App.TEntry", show="*")
        pwd_entry.pack(fill="x", pady=(0, 10))

        def submit():
            role = role_var.get()
            username = user_entry.get().strip()
            if not username:
                show_error_toast(self.master, "Error", "Username cannot be blank.")
                return
            existing = [u['username'] for u in users['admin']]
            existing += [u['username'] for u in users['scout leader']]
            existing += [u['username'] for u in users['logistics coordinator']]
            if username in existing:
                show_error_toast(self.master, "Error", "Username already exists.")
                return
            pwd = pwd_entry.get()
            target_list = users['admin'] if role == "admin" else users[role]
            target_list.append({'username': username, 'password': pwd})
            save_logins()
            add_notification(
                f"[Admin: {self.username}] Created user '{username}' with role '{role}'",
                level="INFO")
            messagebox.showinfo("Success", f"Added {role}: {username}")
            if on_added:
                on_added()
            top.destroy()

        ttk.Button(frame, text="Add User", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def edit_user_password_ui(self):
        top = tk.Toplevel(self)
        top.title("Edit User Password")
        top.configure(bg=THEME_BG)
        center_window(top, width=520, height=420)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Edit user password", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        roles = ["admin", "scout leader", "logistics coordinator"]
        role_var = tk.StringVar(value=roles[0])
        ttk.Label(frame, text="Role", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        role_menu = ttk.OptionMenu(frame, role_var, roles[0], *roles)
        role_menu.pack(fill="x", pady=(0, 8))

        ttk.Label(frame, text="User", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        user_var = tk.StringVar()
        user_menu = ttk.OptionMenu(frame, user_var, "")
        user_menu.pack(fill="x", pady=(0, 8))

        def refresh_users(*args):
            role = role_var.get()
            names = [u['username'] for u in users[role]]
            menu = user_menu["menu"]
            menu.delete(0, "end")
            if names:
                user_var.set(names[0])
                for n in names:
                    menu.add_command(label=n, command=lambda v=n: user_var.set(v))
            else:
                user_var.set("")
        role_var.trace_add("write", refresh_users)
        refresh_users()

        ttk.Label(frame, text="New password", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        pwd_entry = ttk.Entry(frame, style="App.TEntry", show="*")
        pwd_entry.pack(fill="x", pady=(0, 10))

        def submit():
            role = role_var.get()
            target_user = user_var.get()
            if not target_user:
                show_error_toast(self.master, "Error", "No users for this role.")
                return
            new_pwd = pwd_entry.get()
            for u in users[role]:
                if u['username'] == target_user:
                    u['password'] = new_pwd
                    break
            save_logins()
            add_notification(
                f"[Admin: {self.username}] Changed password for user '{target_user}'",
                level="WARNING")
            messagebox.showinfo("Success", "Password updated.")
            top.destroy()

        ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def delete_user_ui(self):
        top = tk.Toplevel(self)
        top.title("Delete User")
        top.configure(bg=THEME_BG)
        center_window(top, width=520, height=420)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Delete user", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        roles = ["scout leader", "logistics coordinator"]
        role_var = tk.StringVar(value=roles[0])
        ttk.Label(frame, text="Role", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        role_menu = ttk.OptionMenu(frame, role_var, roles[0], *roles)
        role_menu.pack(fill="x", pady=(0, 8))

        ttk.Label(frame, text="User", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        user_var = tk.StringVar()
        user_menu = ttk.OptionMenu(frame, user_var, "")
        user_menu.pack(fill="x", pady=(0, 10))

        def refresh_users(*args):
            role = role_var.get()
            names = [u['username'] for u in users[role]]
            menu = user_menu["menu"]
            menu.delete(0, "end")
            if names:
                user_var.set(names[0])
                for n in names:
                    menu.add_command(label=n, command=lambda v=n: user_var.set(v))
            else:
                user_var.set("")
        role_var.trace_add("write", refresh_users)
        refresh_users()

        def submit():
            role = role_var.get()
            target_user = user_var.get()
            if not target_user:
                show_error_toast(self.master, "Error", "No users for this role.")
                return
            users[role] = [u for u in users[role] if u['username'] != target_user]
            save_logins()
            add_notification(
                f"[Admin: {self.username}] Deleted user '{target_user}'",
                level="INFO")
            top.destroy()
            messagebox.showinfo("Success", f"Deleted {target_user}.")
            top.destroy()

        ttk.Button(frame, text="Delete", command=submit, style="Danger.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def disable_user_ui(self):
        names = [u['username'] for u in users['admin']]
        names += [u['username'] for u in users['scout leader']]
        names += [u['username'] for u in users['logistics coordinator']]
        if not names:
            messagebox.showinfo("Info", "No users to disable.")
            return
        top = tk.Toplevel(self)
        top.title("Disable User")
        top.configure(bg=THEME_BG)
        center_window(top, width=500, height=200)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Disable user", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text="User", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        user_var = tk.StringVar(value=names[0])
        ttk.OptionMenu(frame, user_var, names[0], *names).pack(fill="x", pady=(0, 10))

        def submit():
            target_user = user_var.get()
            disabled_logins(target_user)
            save_logins()
            add_notification(
                f"[Admin: {self.username}] Disabled user '{target_user}'",
                level="WARNING")
            messagebox.showinfo("Success", f"Disabled {target_user}.")
            top.destroy()

        ttk.Button(frame, text="Disable", command=submit, style="Danger.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def enable_user_ui(self):
        disabled_usernames = []
        try:
            with open('disabled_logins.txt', 'r') as file:
                disabled_login = file.read().strip(',')
                if disabled_login != "":
                    disabled_usernames.extend([x for x in disabled_login.split(',') if x])
        except FileNotFoundError:
            pass
        if not disabled_usernames:
            messagebox.showinfo("Info", "No disabled users.")
            return
        top = tk.Toplevel(self)
        top.title("Enable User")
        top.configure(bg=THEME_BG)
        center_window(top, width=520, height=360)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Enable user", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text="User", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        user_var = tk.StringVar(value=disabled_usernames[0])
        ttk.OptionMenu(frame, user_var, disabled_usernames[0], *disabled_usernames).pack(fill="x", pady=(0, 10))

        def submit():
            target_user = user_var.get()
            existing = [u['username'] for u in users['admin']]
            existing += [u['username'] for u in users['scout leader']]
            existing += [u['username'] for u in users['logistics coordinator']]
            if target_user not in existing:
                show_error_toast(self.master, "Error", "User no longer exists.")
                return
            enable_login(target_user)
            add_notification(
                f"[Admin: {self.username}] Enabled user '{target_user}'",
                level="INFO")
            messagebox.showinfo("Success", f"Enabled {target_user}.")
            top.destroy()

        ttk.Button(frame, text="Enable", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def messaging_ui(self):
        top = tk.Toplevel(self)
        top.title("Messaging")
        top.configure(bg=THEME_BG)
        center_window(top, width=420, height=240)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Messaging", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))
        ttk.Button(frame, text="Direct Messages", command=lambda: open_chat_window(self.master, self.username, role="admin"), style="Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(frame, text="Group Chat", command=lambda: open_group_chat_window(self.master, self.username, role="admin")).pack(fill="x", pady=4)
        ttk.Button(frame, text="Close", command=top.destroy).pack(fill="x", pady=(8, 0))
        center_in_place(top)

    def notifications_ui(self):
        open_notifications_window(
            self,
            refresh_badge_cb=self._refresh_notification_badge,
            filter_fn=self._notif_filter,
            username=self.username,
            show_buffer_control=True,
        )

    def logout(self):
        root = self.master
        state_info = capture_window_state(root)
        for child in list(root.winfo_children()):
            child.destroy()
        root.title("CampTrack Login")
        init_style(root)
        restore_geometry(root, state_info, min_w=1040, min_h=820)
        LoginWindow(root)


class LogisticsWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=0, style="App.TFrame")
        self.username = username
        master.minsize(1040, 820)
        self.pack(fill="both", expand=True)

        sections = [
            ("Dashboard", self._focus_dashboard),
            ("Manage Camps", self.manage_camps_menu),
            ("Food Allocation", self.food_allocation_menu),
            ("Financial Settings", self.financial_settings_ui),
            ("Visualise Data", self.visualise_menu),
            ("Notifications", self.notifications_ui),
            ("Messaging", self.messaging_ui),
            ("Logout", self.logout),
        ]
        logistics_notif_filter = lambda n: n.get("category") in LOGISTICS_NOTIF_CATEGORIES
        content, nav = _init_nav_with_badge(
            self,
            username,
            "Logistics Coordinator",
            sections,
            notif_filter=logistics_notif_filter,
        )
        self._sections = sections

        # HERO
        hero = ttk.Frame(content, style="Card.TFrame", padding=SPACING["lg"])
        hero.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        hero.columnconfigure(1, weight=1)
        logo = load_logo(80)
        if logo:
            ttk.Label(hero, image=logo, background=THEME_CARD).grid(row=0, column=0, rowspan=3, sticky="w", padx=(0, SPACING["md"]))
            hero.logo_ref = logo
        ttk.Label(hero, text="Logistics Overview", style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(hero, text="Define camps, manage food stock and pay rates, view notifications.", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")
        ttk.Button(hero, text="Open Messaging", command=self.messaging_ui, style="Primary.TButton").grid(row=2, column=1, sticky="w", pady=(SPACING["sm"], 0))

        # SUMMARY
        summary = ttk.Frame(content, style="Card.TFrame")
        summary.grid(row=1, column=0, sticky="ew", pady=(0, SPACING["md"]))
        camps = read_from_file()
        campers_total = sum(len(c.campers) for c in camps)
        leaders_assigned = len({leader for c in camps for leader in c.scout_leaders})
        _pill(summary, "Camps", str(len(camps)), "Active camps")
        _pill(summary, "Campers", str(campers_total), "Across all camps")
        _pill(summary, "Leaders", str(leaders_assigned), "Assigned to camps")

        # GRID
        main = ttk.Frame(content, style="App.TFrame")
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        camp_frame = ttk.LabelFrame(main, text="Camp Management", padding=SPACING["md"], style="Card.TFrame")
        camp_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["md"]), pady=(0, SPACING["md"]))
        ttk.Label(camp_frame, text="Create, edit, or delete camps.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, SPACING["sm"]))
        for text, cmd in [
            ("Manage Camps", self.manage_camps_menu),
            ("Food Allocation", self.food_allocation_menu),
            ("Financial Settings", self.financial_settings_ui),
        ]:
            btn_style = "Primary.TButton" if "Manage" in text else "TButton"
            ttk.Button(camp_frame, text=text, command=cmd, style=btn_style).pack(fill="x", pady=4)

        viz_frame = ttk.LabelFrame(main, text="Insights & Notifications", padding=SPACING["md"], style="Card.TFrame")
        viz_frame.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["md"]))
        for text, cmd in [
            ("Dashboard", self.dashboard_ui),
            ("Visualise Data", self.visualise_menu),
            ("Notifications", self.notifications_ui),
            ("Messaging", self.messaging_ui),
        ]:
            ttk.Button(viz_frame, text=text, command=cmd).pack(fill="x", pady=4)

        logout_frame = ttk.Frame(content, style="App.TFrame")
        logout_frame.grid(row=3, column=0, sticky="ew", pady=(SPACING["sm"], 0))
        ttk.Button(logout_frame, text="Logout", command=self.logout, style="Danger.TButton").pack(side="right")

    def _focus_dashboard(self):
        # placeholder to match nav selection; content already visible
        pass

    def manage_camps_menu(self):
        top = tk.Toplevel(self)
        top.title("Manage and Create Camps")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Camp Management", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))
        ttk.Button(frame, text="Create Camp", command=self.create_camp_ui, style="Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(frame, text="Edit Camp", command=self.edit_camp_ui).pack(fill="x", pady=4)
        ttk.Button(frame, text="Delete Camp", command=self.delete_camp_ui, style="Danger.TButton").pack(fill="x", pady=4)
        center_in_place(top)

    def food_allocation_menu(self):
        top = tk.Toplevel(self)
        top.title("Manage Food Allocation")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Food Allocation", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))
        ttk.Button(frame, text="Set Daily Food Stock", command=self.set_food_stock_ui, style="Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(frame, text="Top-Up Food Stock", command=self.top_up_food_ui).pack(fill="x", pady=4)
        ttk.Button(frame, text="Check Food Shortage", command=self.shortage_ui).pack(fill="x", pady=4)
        center_in_place(top)

    def set_food_stock_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Set Stock", "No camps exist.")
            return

        def choose_camp():
            top = tk.Toplevel(self)
            top.title("Set Daily Food Stock")
            top.configure(bg=THEME_BG)
            frame = ttk.Frame(top, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text="Set Daily Food Stock", style="Header.TLabel").pack(pady=(0, 4))
            ttk.Label(frame, text="Choose a camp to update", style="Subtitle.TLabel").pack(pady=(0, 6))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            lb_frame = ttk.Frame(frame, style="Card.TFrame")
            lb_frame.pack(fill="both", expand=True, pady=4)
            listbox = tk.Listbox(
                lb_frame,
                bg="#0b1729",
                fg=THEME_FG,
                selectbackground=THEME_ACCENT,
                highlightthickness=0,
                relief="flat",
                width=50,
            )
            scrollbar = ttk.Scrollbar(lb_frame, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
            scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
            for camp in camps:
                listbox.insert("end", camp.name)

            def next_step():
                sel = listbox.curselection()
                if not sel:
                    show_error_toast(self.master, "Error", "Please select a camp.")
                    return
                camp_name = listbox.get(sel[0])
                top.destroy()
                enter_stock(camp_name)

            ttk.Button(frame, text="Next", command=next_step, style="Primary.TButton").pack(fill="x", pady=(8, 0))
            center_in_place(top)

        def enter_stock(camp):
            top = tk.Toplevel(self)
            top.title("Set Daily Food Stock")
            top.configure(bg=THEME_BG)
            frame = ttk.Frame(top, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text="Set Daily Food Stock", style="Header.TLabel").pack(pady=(0, 8))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            ttk.Label(frame, text=f"Camp: {camp}", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 6))
            ttk.Label(frame, text="New daily stock", style="FieldLabel.TLabel").pack(anchor="w")
            stock_entry = ttk.Entry(frame, style="App.TEntry")
            stock_entry.pack(fill="x", pady=(0, 10))
            err_lbl = tk.StringVar(value="")
            ttk.Label(frame, textvariable=err_lbl, style="Error.TLabel").pack(anchor="w")

            def submit():
                try:
                    val = int(stock_entry.get().strip())
                except ValueError:
                    err_lbl.set("Please enter a whole number.")
                    return
                res = set_food_stock_data(camp, val)
                messagebox.showinfo("Result", res.get("status"))
                top.destroy()

            ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
            center_in_place(top)

        choose_camp()

    def top_up_food_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Top Up", "No camps exist.")
            return

        def choose_camp():
            top = tk.Toplevel(self)
            top.title("Top-Up Food Stock")
            top.configure(bg=THEME_BG)
            frame = ttk.Frame(top, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text="Top-Up Food Stock", style="Header.TLabel").pack(pady=(0, 4))
            ttk.Label(frame, text="Choose a camp to top up", style="Subtitle.TLabel").pack(pady=(0, 6))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            lb_frame = ttk.Frame(frame, style="Card.TFrame")
            lb_frame.pack(fill="both", expand=True, pady=4)
            listbox = tk.Listbox(
                lb_frame,
                bg="#0b1729",
                fg=THEME_FG,
                selectbackground=THEME_ACCENT,
                highlightthickness=0,
                relief="flat",
                width=50,
            )
            scrollbar = ttk.Scrollbar(lb_frame, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
            scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
            for camp in camps:
                listbox.insert("end", camp.name)

            def next_step():
                sel = listbox.curselection()
                if not sel:
                    show_error_toast(self.master, "Error", "Please select a camp.")
                    return
                camp_name = listbox.get(sel[0])
                top.destroy()
                enter_amount(camp_name)

            ttk.Button(frame, text="Next", command=next_step, style="Primary.TButton").pack(fill="x", pady=(8, 0))
            center_in_place(top)

        def enter_amount(camp):
            top = tk.Toplevel(self)
            top.title("Top-Up Food Stock")
            top.configure(bg=THEME_BG)
            frame = ttk.Frame(top, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text="Top-Up Food Stock", style="Header.TLabel").pack(pady=(0, 8))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            ttk.Label(frame, text=f"Camp: {camp}", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 6))
            ttk.Label(frame, text="Amount to add", style="FieldLabel.TLabel").pack(anchor="w")
            amt_entry = ttk.Entry(frame, style="App.TEntry")
            amt_entry.pack(fill="x", pady=(0, 10))
            err_lbl = tk.StringVar(value="")
            ttk.Label(frame, textvariable=err_lbl, style="Error.TLabel").pack(anchor="w")

            def submit():
                try:
                    val = int(amt_entry.get().strip())
                except ValueError:
                    err_lbl.set("Please enter a whole number.")
                    return
                res = top_up_food_data(camp, val)
                messagebox.showinfo("Result", res.get("status"))
                top.destroy()

            ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
            center_in_place(top)

        choose_camp()

    def set_pay_rate_ui(self):
        camp = self.choose_camp_name(title="Set Pay Rate", subtitle="Choose a camp to update pay")
        if not camp:
            return
        top = tk.Toplevel(self)
        top.title("Set Pay Rate")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Set Daily Pay Rate", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text=f"Camp: {camp}", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(frame, text="Daily pay rate", style="FieldLabel.TLabel").pack(anchor="w")
        rate_entry = ttk.Entry(frame, style="App.TEntry")
        rate_entry.pack(fill="x", pady=(0, 10))
        err_lbl = tk.StringVar(value="")
        ttk.Label(frame, textvariable=err_lbl, style="Error.TLabel").pack(anchor="w")

        def submit():
            try:
                val = int(rate_entry.get().strip())
            except ValueError:
                err_lbl.set("Please enter a whole number.")
                return
            res = set_pay_rate_data(camp, val)
            messagebox.showinfo("Result", res.get("status"))
            top.destroy()

        ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def shortage_ui(self):
        camp = self.choose_camp_name()
        if not camp:
            return
        res = compute_food_shortage(camp)
        status = res.get("status")
        if status == "shortage":
            message = f"{res['camp_name']} requires {res['required']} units vs available {res['available']}."
        elif status == "ok":
            message = "Food stock is sufficient."
        elif status == "missing_requirement":
            message = "No food requirement set. Ask scout leader to set daily food per camper."
        else:
            message = status
        messagebox.showinfo("Shortage Check", message)

    def dashboard_ui(self):
        df, summary = build_dashboard_data()
        if df is None:
            messagebox.showinfo("Dashboard", "No camps found.")
            return
        top = tk.Toplevel(self)
        top.title("Dashboard Summary")
        top.minsize(1200, 100)
        center_window(top, width=1200, height=400)
        frame = ttk.Frame(top, padding=10, style="Card.TFrame")
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, width=120, height=15)
        text.pack(fill="both", expand=True)
        text.insert("end", df.to_string(index=False))
        text.insert("end", "\n\nSummary:\n")
        for k, v in summary.items():
            text.insert("end", f"{k}: {v}\n")
        center_in_place(top)

    def notifications_ui(self):
        open_notifications_window(
            self,
            refresh_badge_cb=self._refresh_notification_badge,
            filter_fn=self._notif_filter,
            username=self.username,
        )
        
    def visualise_menu(self):
        top = tk.Toplevel(self)
        top.title("Visualise Camp Data")
        top.configure(bg=THEME_BG)
        top.minsize(300, 300)
        center_window(top, width=300, height=300)
        frame = ttk.Frame(top, padding=8, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(frame, text="Visualise Camp Data", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))
        ttk.Button(frame, text="Food Stock per Camp", command=plot_food_stock, style="Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(frame, text="Camper Distribution", command=plot_camper_distribution).pack(fill="x", pady=4)
        ttk.Button(frame, text="Leaders per Camp", command=plot_leaders_per_camp).pack(fill="x", pady=4)
        ttk.Button(frame, text="Engagement Overview", command=plot_engagement_scores).pack(fill="x", pady=4)
        center_in_place(top)

    def financial_settings_ui(self):
        self.set_pay_rate_ui()

    def create_camp_ui(self):
        top = tk.Toplevel(self)
        top.title("Create Camp")
        top.configure(bg=THEME_BG)
        center_window(top, width=720, height=560)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Create a new camp", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))

        form = ttk.Frame(frame, style="Card.TFrame")
        form.pack(fill="both", expand=True)

        err_var = tk.StringVar(value="")

        def add_labeled_entry(label_text, placeholder=""):
            lbl = ttk.Label(form, text=label_text, style="FieldLabel.TLabel")
            lbl.pack(anchor="w", pady=(0, 2))
            entry = ttk.Entry(form, style="App.TEntry")
            entry.insert(0, placeholder)
            entry.pack(fill="x", pady=(0, 8))
            return entry

        name_entry = add_labeled_entry("Camp name")
        location_entry = add_labeled_entry("Location")

        ttk.Label(form, text="Camp type (1=Day, 2=Overnight, 3=Multiple Days)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        camp_type_entry = ttk.Entry(form, style="App.TEntry")
        camp_type_entry.pack(fill="x", pady=(0, 8))

        start_entry = add_labeled_entry("Start date (flexible: e.g. 2025-10-10 or 10 Oct 2025)")
        nights_entry = add_labeled_entry("Nights (for type 3 only; min 2)")
        food_entry = add_labeled_entry("Initial daily food stock")

        def submit():
            err_var.set("")
            name = name_entry.get().strip()
            location = location_entry.get().strip()
            if not name or not location:
                err_var.set("Name and location are required.")
                return
            try:
                camp_type = int(camp_type_entry.get().strip())
                if camp_type not in (1, 2, 3):
                    raise ValueError
            except ValueError:
                err_var.set("Camp type must be 1, 2, or 3.")
                return
            try:
                start_date = parse_date_flexible(start_entry.get())
            except ValueError:
                show_error_toast(
                    self.master,
                    "Error",
                    "Invalid start date. Try formats like 2025-10-10, 10 Oct 2025, Oct 10 2025, or 10/10/2025.",
                )
                return
            nights = 0
            if camp_type == 1:
                nights = 0
            elif camp_type == 2:
                nights = 1
            elif camp_type == 3:
                try:
                    nights = int(nights_entry.get().strip() or "0")
                    if nights < 2:
                        raise ValueError
                except ValueError:
                    show_error_toast(self.master, "Error", "For type 3, nights must be 2 or more.")
                    return
            end_dt = datetime.strptime(start_date, "%Y-%m-%d").date() + timedelta(days=nights)
            end_date = end_dt.strftime("%Y-%m-%d")
            try:
                food_stock = int(food_entry.get().strip())
                if food_stock < 0:
                    raise ValueError
            except ValueError:
                err_var.set("Food stock must be a non-negative integer.")
                return

            read_from_file()
            Camp(name, location, camp_type, start_date, end_date, food_stock)
            add_notification(f"Camp {name} created")
            save_to_file()
            messagebox.showinfo("Success", f"Camp {name} created.")
            top.destroy()

        ttk.Button(frame, text="Create", command=submit, style="Primary.TButton").pack(fill="x", pady=(8, 0))
        center_in_place(top)

    def edit_camp_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Edit Camp", "No camps exist.")
            return
        top = tk.Toplevel(self)
        top.title("Edit Camp")
        top.configure(bg=THEME_BG)
        center_window(top, width=720, height=560)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Edit an existing camp", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))

        names = [c.name for c in camps]
        ttk.Label(frame, text="Select camp", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        camp_var = tk.StringVar()
        camp_var.set(names[0])
        ttk.OptionMenu(frame, camp_var, names[0], *names).pack(fill="x", pady=(0, 10))

        form = ttk.Frame(frame, style="Card.TFrame")
        form.pack(fill="both", expand=True)

        def add_labeled_entry(label_text, initial=""):
            ttk.Label(form, text=label_text, style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            entry = ttk.Entry(form, style="App.TEntry")
            entry.insert(0, initial)
            entry.pack(fill="x", pady=(0, 8))
            return entry

        camp = camps[0]
        name_entry = add_labeled_entry("Name", camp.name)
        loc_entry = add_labeled_entry("Location", camp.location)
        type_entry = add_labeled_entry("Camp type (1-3)", str(camp.camp_type))
        start_entry = add_labeled_entry("Start date (flexible)", camp.start_date)
        end_entry = add_labeled_entry("End date (flexible)", camp.end_date)
        nights_entry = add_labeled_entry("Nights (for type 3 only; min 2)")
        food_entry = add_labeled_entry("Daily food stock", str(camp.food_stock))
        pay_entry = add_labeled_entry("Daily pay rate", str(camp.pay_rate))

        def on_select(*args):
            selected = camp_var.get()
            for c in camps:
                if c.name == selected:
                    name_entry.delete(0, tk.END); name_entry.insert(0, c.name)
                    loc_entry.delete(0, tk.END); loc_entry.insert(0, c.location)
                    type_entry.delete(0, tk.END); type_entry.insert(0, str(c.camp_type))
                    start_entry.delete(0, tk.END); start_entry.insert(0, c.start_date)
                    end_entry.delete(0, tk.END); end_entry.insert(0, c.end_date)
                    try:
                        sd = datetime.strptime(c.start_date, "%Y-%m-%d")
                        ed = datetime.strptime(c.end_date, "%Y-%m-%d")
                        nights_entry.delete(0, tk.END); nights_entry.insert(0, str((ed - sd).days))
                    except Exception:
                        nights_entry.delete(0, tk.END)
                    food_entry.delete(0, tk.END); food_entry.insert(0, str(c.food_stock))
                    pay_entry.delete(0, tk.END); pay_entry.insert(0, str(c.pay_rate))
                    break
        camp_var.trace_add("write", on_select)

        def submit():
            selected = camp_var.get()
            camp_obj = next((c for c in camps if c.name == selected), None)
            if not camp_obj:
                return
            try:
                ct = int(type_entry.get().strip())
                if ct not in (1, 2, 3):
                    raise ValueError
            except ValueError:
                show_error_toast(self.master, "Error", "Camp type must be 1, 2, or 3.")
                return
            try:
                nf = int(food_entry.get().strip())
                if nf < 0:
                    raise ValueError
            except ValueError:
                show_error_toast(self.master, "Error", "Invalid food stock.")
                return
            try:
                pr = int(pay_entry.get().strip())
                if pr < 0:
                    raise ValueError
            except ValueError:
                show_error_toast(self.master, "Error", "Invalid pay rate.")
                return
            try:
                new_start = parse_date_flexible(start_entry.get())
            except ValueError:
                show_error_toast(
                    self.master,
                    "Error",
                    "Invalid date. Try formats like 2025-10-10, 10 Oct 2025, Oct 10 2025, or 10/10/2025.",
                )
                return
            nights = 0
            if ct == 1:
                nights = 0
            elif ct == 2:
                nights = 1
            elif ct == 3:
                try:
                    nights = int(nights_entry.get().strip() or "0")
                    if nights < 2:
                        raise ValueError
                except ValueError:
                    show_error_toast(self.master, "Error", "For type 3, nights must be 2 or more.")
                    return
            new_end = (datetime.strptime(new_start, "%Y-%m-%d").date() + timedelta(days=nights)).strftime("%Y-%m-%d")

            camp_obj.name = name_entry.get().strip() or camp_obj.name
            camp_obj.location = loc_entry.get().strip() or camp_obj.location
            camp_obj.camp_type = ct
            camp_obj.start_date = new_start or camp_obj.start_date
            camp_obj.end_date = new_end or camp_obj.end_date
            camp_obj.food_stock = nf
            camp_obj.pay_rate = pr
            add_notification(f"Camp {camp_obj.name} edited")
            save_to_file()
            messagebox.showinfo("Success", "Camp updated.")
            top.destroy()

        ttk.Button(frame, text="Save changes", command=submit, style="Primary.TButton").pack(fill="x", pady=(8, 0))
        center_in_place(top)

    def delete_camp_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Delete Camp", "No camps exist.")
            return
        top = tk.Toplevel(self)
        top.title("Delete Camp")
        top.configure(bg=THEME_BG)
        center_window(top, width=520, height=420)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Delete a camp", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))
        names = [c.name for c in camps]
        ttk.Label(frame, text="Select camp to delete", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        camp_var = tk.StringVar()
        camp_var.set(names[0])
        ttk.OptionMenu(frame, camp_var, names[0], *names).pack(fill="x", pady=(0, 8))

        def delete():
            selected = camp_var.get()
            camp_obj = next((c for c in camps if c.name == selected), None)
            if not camp_obj:
                return
            if not messagebox.askyesno("Confirm", f"Delete camp '{camp_obj.name}'?"):
                return
            camps.remove(camp_obj)
            Camp.all_camps = camps
            add_notification(f"Camp {camp_obj.name} deleted")
            save_to_file()
            messagebox.showinfo("Success", f"Camp '{camp_obj.name}' deleted.")
            top.destroy()

        ttk.Button(frame, text="Delete", command=delete, style="Danger.TButton").pack(fill="x", pady=(8, 0))
        center_in_place(top)

    def messaging_ui(self):
        open_chat_window(self.master, self.username, role="logistics coordinator")

    def choose_camp_name(self, title="Select a camp", subtitle=None):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Camps", "No camps exist.")
            return None

        top = tk.Toplevel(self)
        top.title(title)
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text=title, style="Header.TLabel").pack(pady=(0, 4))
        if subtitle:
            ttk.Label(frame, text=subtitle, style="Subtitle.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        lb_frame = ttk.Frame(frame, style="Card.TFrame")
        lb_frame.pack(fill="both", expand=True, pady=4)
        listbox = tk.Listbox(
            lb_frame,
            bg="#0b1729",
            fg=THEME_FG,
            selectbackground=THEME_ACCENT,
            highlightthickness=0,
            relief="flat",
            width=50,
        )
        scrollbar = ttk.Scrollbar(lb_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
        for camp in camps:
            listbox.insert("end", camp.name)

        result = {"camp": None}

        def submit():
            sel = listbox.curselection()
            if not sel:
                messagebox.showerror("Error", "Please select a camp.")
                return
            result["camp"] = listbox.get(sel[0])
            top.destroy()

        ttk.Button(frame, text="Select", command=submit, style="Primary.TButton").pack(fill="x", pady=(8, 0))
        center_in_place(top)
        top.grab_set()
        top.wait_window()
        return result["camp"]

    def logout(self):
        root = self.master
        state_info = capture_window_state(root)
        for child in list(root.winfo_children()):
            child.destroy()
        root.title("CampTrack Login")
        init_style(root)
        restore_geometry(root, state_info, min_w=1040, min_h=820)
        LoginWindow(root)


class ScoutWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=0, style="App.TFrame")
        self.username = username
        master.minsize(1040, 820)
        self.pack(fill="both", expand=True)

        content, nav = _init_nav_with_badge(
            self,
            username,
            "Scout Leader",
            [
                ("Dashboard", self._focus_dashboard),
                ("Select Camps", self.select_camps_ui),
                ("Import Campers", self.bulk_assign_ui),
                ("Record Activity", self.record_activity_ui),
                ("Record Incident", self.record_incidents_ui),
                ("View Stats", self.stats_ui),
                ("View Activities", self.view_activities_ui),
                ("View Incidents", self.view_incidents_ui),
                ("Notifications", self.notifications_ui),
                ("Messaging", self.messaging_ui),
                ("Logout", self.logout),
            ],
            notif_filter=None,  # set after we know supervised camps
        )
        # Scout sees notifications for camps they supervise
        camps = read_from_file()
        supervised_names = {c.name for c in camps if self.username in c.scout_leaders}
        self._notif_filter = lambda n: (n.get("context") or {}).get("camp") in supervised_names
        self._refresh_notification_badge()

        # HERO
        hero = ttk.Frame(content, style="Card.TFrame", padding=SPACING["lg"])
        hero.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["md"]))
        hero.columnconfigure(1, weight=1)
        logo = load_logo(80)
        if logo:
            ttk.Label(hero, image=logo, background=THEME_CARD).grid(row=0, column=0, rowspan=3, sticky="w", padx=(0, SPACING["md"]))
            hero.logo_ref = logo
        ttk.Label(hero, text="Scout Leader Hub", style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(hero, text="Supervise camps, import campers, record activities and incidents.", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")
        ttk.Button(hero, text="Open Messaging", command=self.messaging_ui, style="Primary.TButton").grid(row=2, column=1, sticky="w", pady=(SPACING["sm"], 0))

        # SUMMARY
        summary = ttk.Frame(content, style="Card.TFrame")
        summary.grid(row=1, column=0, sticky="ew", pady=(0, SPACING["md"]))
        camps = read_from_file()
        supervised = [c for c in camps if self.username in c.scout_leaders]
        campers_total = sum(len(c.campers) for c in supervised)
        incidents_total = sum(len(getattr(c, "incidents", [])) for c in supervised)
        _pill(summary, "Your Camps", str(len(supervised)), "Camps you supervise")
        _pill(summary, "Campers", str(campers_total), "In your camps")
        _pill(summary, "Incidents", str(incidents_total), "Logged incidents")

        # GRID
        main = ttk.Frame(content, style="App.TFrame")
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        actions = ttk.LabelFrame(main, text="Camp Actions", padding=SPACING["md"], style="Card.TFrame")
        actions.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["md"]), pady=(0, SPACING["md"]))
        ttk.Label(actions, text="Select camps, import campers, and set food needs.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, SPACING["sm"]))
        for text, cmd in [
            ("Select Camp(s) to Supervise", self.select_camps_ui),
            ("Stop Supervising Camp(s)", self.unsupervise_camps_ui),
            ("Manage Campers", self.bulk_assign_ui),
            ("Set Food per Camper", self.food_req_ui),
        ]:
            btn_style = "Primary.TButton" if "Select camps" in text else "TButton"
            ttk.Button(actions, text=text, command=cmd, style=btn_style).pack(fill="x", pady=4)

        stats_frame = ttk.LabelFrame(main, text="Record & Review", padding=SPACING["md"], style="Card.TFrame")
        stats_frame.grid(row=0, column=1, sticky="nsew", pady=(0, SPACING["md"]))
        for text, cmd in [
            ("Record Activity", self.record_activity_ui),
            ("Record Incident", self.record_incidents_ui),
            ("View Stats", self.stats_ui),
            ("View Camp Activities", self.view_activities_ui),
            ("View Incidents", self.view_incidents_ui),
            ("Messaging", self.messaging_ui),
        ]:
            ttk.Button(stats_frame, text=text, command=cmd).pack(fill="x", pady=4)

        logout_frame = ttk.Frame(content, style="App.TFrame")
        logout_frame.grid(row=3, column=0, sticky="ew", pady=(SPACING["sm"], 0))
        ttk.Button(logout_frame, text="Logout", command=self.logout, style="Danger.TButton").pack(side="right")

    def _focus_dashboard(self):
        # placeholder to align with nav; content already visible
        pass

    def notifications_ui(self):
        open_notifications_window(
            self,
            refresh_badge_cb=self._refresh_notification_badge,
            filter_fn=self._notif_filter,
            username=self.username,
        )

    def group_chat_ui(self):
        from chat_window import open_group_chat_window
        open_group_chat_window(self, self.username)

    def select_camps_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Select Camps", "No camps exist.")
            return
        indices = select_camp_dialog("Select camps to supervise", camps, allow_multiple=True)
        if not indices:
            messagebox.showinfo("Select Camps", "No camps selected.")
            return
        # Build conflict info between current + new selections
        existing = [c for c in camps if self.username in c.scout_leaders]
        new_camps = [camps[i] for i in indices]

        def overlaps(a, b):
            return camps_overlap(a, b)

        new_new_conflicts = []
        for i in range(len(new_camps)):
            for j in range(i + 1, len(new_camps)):
                if overlaps(new_camps[i], new_camps[j]):
                    new_new_conflicts.append((new_camps[i].name, new_camps[j].name))

        if new_new_conflicts:
            pairs = "\n".join([f"- {a} ↔ {b}" for a, b in new_new_conflicts])
            show_error_toast(self.master, "Conflict", f"Your selected camps overlap each other:\n{pairs}\nPlease adjust your selection.")
            return

        conflict_pairs = []
        for ncamp in new_camps:
            for ecamp in existing:
                if overlaps(ncamp, ecamp):
                    conflict_pairs.append((ncamp.name, ecamp.name))

        proceed_indices = indices
        removed_existing = []
        skipped_new = []

        if conflict_pairs:
            lines = "\n".join([f"- New: {n} ↔ Existing: {e}" for n, e in conflict_pairs])
            msg = (
                "Some selected camps overlap with your current assignments:\n"
                f"{lines}\n\n"
                "Yes: replace overlapping existing assignments with the new ones.\n"
                "No: keep existing assignments and skip the conflicting new camps.\n"
                "Cancel: do nothing."
            )
            choice = messagebox.askyesnocancel("Conflicts found", msg)
            if choice is None:
                return
            if choice:  # replace existing
                conflict_existing_names = {e for _, e in conflict_pairs}
                for camp in existing:
                    if camp.name in conflict_existing_names and self.username in camp.scout_leaders:
                        camp.scout_leaders.remove(self.username)
                        removed_existing.append(camp.name)
                proceed_indices = indices  # keep all new selections
            else:  # keep existing, skip conflicting new
                conflict_new_names = {n for n, _ in conflict_pairs}
                proceed_indices = [i for i in indices if camps[i].name not in conflict_new_names]
                skipped_new = [camps[i].name for i in indices if camps[i].name in conflict_new_names]
                if not proceed_indices:
                    messagebox.showinfo("Select Camps", "All selected camps conflict with your current assignments; kept existing.")
                    return

        res = assign_camps_to_leader(camps, self.username, proceed_indices)
        status = res.get("status")
        if status == "ok":
            summary = ", ".join(res.get("selected", [])) or "None"
            extra = ""
            if removed_existing:
                extra += f"\nRemoved (replaced): {', '.join(removed_existing)}"
            if skipped_new:
                extra += f"\nSkipped (conflict): {', '.join(skipped_new)}"
            messagebox.showinfo("Success", f"Assigned: {summary}{extra}")
        elif status == "overlap":
            show_error_toast(self.master, "Error", "Selected camps overlap in dates. Please choose non-conflicting camps.")
        elif status == "invalid_index":
            show_error_toast(self.master, "Error", "Invalid selection.")
        else:
            show_error_toast(self.master, "Error", status or "Unknown error")
    
    def unsupervise_camps_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Stop Supervising", "No camps exist.")
            return
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Stop Supervising", "You are not supervising any camps yet.")
            return
        
        indices = select_camp_dialog(
            "Select camp(s) to stop supervising",
            supervised,
            allow_multiple= True,
            allow_cancel= True
        )
        if not indices:
            return
        
        for i in indices:
            camp = supervised[i]
            if self.username in camp.scout_leaders:
                camp.scout_leaders.remove(self.username)
        
        save_to_file()
        messagebox.showinfo("Updated", "You are no longer supervising the selected camp(s).")


    def bulk_assign_ui(self):
        
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Bulk Assign", "No camps exist.")
            return
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Bulk Assign", "You are not supervisiing any camps yet.")
            return
        
        top = tk.Toplevel(self)
        top.title("Manage Campers")
        top.configure(bg=THEME_BG)
        top.transient(self)
        top.grab_set()
        top.focus()
        top.minsize(720,800)
        center_window(top,width=720,height=800)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(frame, text="Manage campers", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Label(frame, text="Select a camp, import campers, and view/delete campers.", style="Subtitle.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(4, 8))

        # Camp list
        ttk.Label(frame, text="Camp", style="FieldLabel.TLabel").pack(anchor="w")

        camp_var = tk.StringVar()
        camp_names = [c.name for c in supervised]
        camp_var.set(camp_names[0])  # default to first supervised camp

        camp_menu = ttk.OptionMenu(frame, camp_var, camp_names[0], *camp_names)
        camp_menu.pack(fill="x", pady=(0, 8))

        def get_selected_camp():
            all_camps = read_from_file()
            supervised_now = [c for c in all_camps if self.username in c.scout_leaders]
            name = camp_var.get()
            for c in supervised_now:
                if c.name == name:
                    return c
            return None

        # File picker
        path_var = tk.StringVar()
        ttk.Label(frame, text="CSV file", style="FieldLabel.TLabel").pack(anchor="w")
        path_entry = ttk.Entry(frame, textvariable=path_var, style="App.TEntry")
        path_entry.pack(fill="x", pady=(0, 4))

        def browse():
            fp = filedialog.askopenfilename(parent=top, title="Select campers CSV", filetypes=[("CSV files", "*.csv")])
            if fp:
                path_var.set(fp)

        ttk.Button(frame, text="Browse", command=browse).pack(fill="x", pady=(0, 10))


        def submit():
            camp = get_selected_camp()
            if camp is None:
                show_error_toast(self.master, "Error", "Please select a camp.")
                return
            filepath = path_var.get().strip()
            if not filepath:
                show_error_toast(self.master, "Error", "Please choose a CSV file.")
                return

            res = bulk_assign_campers_from_csv(camp.name, filepath)
            status = res.get("status")
            if status == "ok":
                added = res.get("added", [])
                messagebox.showinfo("Success", f"Assigned {len(added)} campers to {camp.name}.")
                refresh_campers()
            elif status == "file_not_found":
                show_error_toast(self.master, "Error", "CSV file not found.")
            elif status == "camp_not_found":
                show_error_toast(self.master, "Error", "Camp not found.")
            elif status == "no_campers":
                messagebox.showinfo("Result", "No campers in CSV.")
            elif status == "no_new_campers":
                show_error_toast(self.master, "No new campers",("No campers were imported. "
                "They may already be assigned to this camp or to another camp with overlapping dates"),)
            else:
                show_error_toast(self.master, "Error", status or "Unknown error")

        ttk.Button(frame, text="Import", command=submit, style="Primary.TButton").pack(fill="x", pady=(0, 8))

        ttk.Separator(frame).pack(fill="x", pady=(4, 8))
        
        campers_frame = ttk.Frame(frame, style="Card.TFrame")
        campers_frame.pack(fill="both", expand=True)

        ttk.Label(campers_frame, text="Campers in selected camp", style="FieldLabel.TLabel").pack(anchor="w")

        campers_list = tk.Listbox(
            campers_frame,
            bg="#0b1729",
            fg=THEME_FG,
            selectbackground=THEME_ACCENT,
            highlightthickness=0,
            relief="flat",
            height=8,
        )
        campers_list.pack(fill="both", expand=True, padx=(4, 0), pady=4)

        ttk.Label(frame, text="Camper details", style="FieldLabel.TLabel").pack(anchor="w", pady=(4, 2))
        details_text = tk.Text(
            frame,
            height=6,
            bg="#0b1729",
            fg=THEME_FG,
            highlightthickness=0,
            relief="flat",
            wrap="word",
        )
        details_text.pack(fill="both", expand=True, pady=(0, 4))


        def show_camper_details(event=None):
            camp = get_selected_camp()
            if camp is None:
                return
            selection = campers_list.curselection()
            if not selection:
                return
            idx = selection[0]
            if idx < 0 or idx >= len(camp.campers):
                return
            name = camp.campers[idx]
            info = camp.campers_info.get(name, {})

            dob = info.get("dob", "")
            emergency = info.get("emergency", [])
            if isinstance(emergency, list):
                emergency_str = ", ".join(emergency)
            else:
                emergency_str = str(emergency)

            details_text.delete("1.0", "end")
            lines = [
                f"Name: {name}",
                f"DOB: {dob}",
                f"Emergency info: {emergency_str}",
            ]
            details_text.insert("end", "\n".join(lines))
        
        def refresh_campers(*args):
            campers_list.delete(0, "end")
            details_text.delete("1.0", "end")
            camp = get_selected_camp()
            if camp is None:
                return
            for name in camp.campers:
                campers_list.insert("end",name)
            if camp.campers:
                campers_list.selection_clear(0,"end")
                campers_list.selection_set(0)
                show_camper_details()
        

        def delete_selected_camper(): 
            camp = get_selected_camp()
            if camp is None:
                show_error_toast(self.master, "Error", "Please select a camp.")
                return

            selection = campers_list.curselection()
            if not selection:
                show_error_toast(self.master, "Error", "Please select a camper to delete.")
                return
            idx = selection[0]
            if idx < 0 or idx >= len(camp.campers):
                return
            name = camp.campers[idx]

            confirm = messagebox.askyesno("Confirm", "Remove this camper from the camp?")
            if not confirm:
                return

            camp = get_selected_camp()
            if name in camp.campers:
                camp.campers.remove(name)
            if name in camp.campers_info:
                del camp.campers_info[name]

            save_to_file()   
            refresh_campers()
        
        ttk.Button(frame, text="Delete selected camper", command=delete_selected_camper, style="Danger.TButton").pack(fill="x", pady=(0, 0))
        camp_var.trace_add("write", refresh_campers)
        campers_list.bind("<<ListboxSelect>>", show_camper_details)
        refresh_campers()
        center_in_place(top)

    # --- Shared helpers for scout actions ---
    def _camp_date_picker(self, parent, supervised):
        """Build camp + date selectors and return (camp_var, date_var, get_camp_fn)."""
        ttk.Label(parent, text="Camp", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        camp_var = tk.StringVar(value=supervised[0].name)
        ttk.OptionMenu(parent, camp_var, supervised[0].name, *[c.name for c in supervised]).pack(fill="x", pady=(0, 8))

        ttk.Label(parent, text="Date", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        date_var = tk.StringVar()
        date_menu = ttk.OptionMenu(parent, date_var, "")
        date_menu.pack(fill="x", pady=(0, 8))

        def get_selected_camp():
            name = camp_var.get()
            for c in supervised:
                if c.name == name:
                    return c
            return supervised[0]

        def refresh_dates(*_):
            camp_obj = get_selected_camp()
            try:
                start = datetime.strptime(camp_obj.start_date, "%Y-%m-%d").date()
                end = datetime.strptime(camp_obj.end_date, "%Y-%m-%d").date()
            except ValueError:
                dates = []
            else:
                dates = []
                d = start
                while d <= end:
                    dates.append(d.isoformat())
                    d += timedelta(days=1)

            menu = date_menu["menu"]
            menu.delete(0, "end")
            if dates:
                for d_str in dates:
                    menu.add_command(label=d_str, command=lambda v=d_str: date_var.set(v))
                date_var.set(dates[0])
            else:
                date_var.set("")

        camp_var.trace_add("write", refresh_dates)
        refresh_dates()
        return camp_var, date_var, get_selected_camp

    def _campers_listbox(self, parent):
        listbox = tk.Listbox(
            parent,
            selectmode="extended",
            height=6,
            bg="#0b1729",
            fg=THEME_FG,
            selectbackground=THEME_ACCENT,
            highlightthickness=0,
            relief="flat",
        )
        listbox.pack(fill="both", expand=True, pady=(0, 8))
        return listbox

    def _build_detail_table(self, parent, columns, col_config):
        """Create a tree + details text pane; return (tree, details_text, item_details)."""
        table_frame = ttk.Frame(parent, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        col_keys = list(columns.keys())

        tree = ttk.Treeview(table_frame, columns=col_keys, show="headings", height=10)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        for key in col_keys:
            heading = columns[key]
            tree.heading(key, text=heading)
            conf = col_config.get(key, {})
            tree.column(key, width=conf.get("width", 120), anchor=conf.get("anchor", "w"))

        details_frame = ttk.LabelFrame(parent, text="Details", padding=8, style="Card.TFrame")
        details_frame.pack(fill="both", expand=True, pady=(4, 0))
        details_text = tk.Text(
            details_frame,
            height=8,
            bg="#0b1729",
            fg=THEME_FG,
            wrap="word",
            highlightthickness=0,
            relief="flat",
        )
        details_text.pack(fill="both", expand=True)

        return tree, details_text, {}

    def food_req_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Food", "No camps exist.")
            return
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Bulk Assign", "You are not supervisiing any camps yet.")
            return
        indices = select_camp_dialog("Select camp to set food requirement", supervised, allow_multiple=False)
        if not indices:
            return
        camp = supervised[indices[0]].name
        units = simple_prompt_int("Daily food units per camper")
        if units is None:
            return
        res = assign_food_amount_pure(camp, units)
        status = res.get("status")
        if status == "ok":
            messagebox.showinfo("Success", f"Saved {units} units per camper for {camp}.")
        else:
            messagebox.showerror("Error", status or "Unknown error")

    def record_activity_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Activity", "No camps exist.")
            return
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Activity", "You are not supervising any camps yet.")
            return

        top = tk.Toplevel(self)
        top.title("Record Activity")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Record daily activity", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        camp_var, date_var, get_selected_camp = self._camp_date_picker(frame, supervised)

        def add_entry(label, initial=""):
            ttk.Label(frame, text=label, style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            entry = ttk.Entry(frame, style="App.TEntry")
            if initial:
                entry.insert(0, initial)
            entry.pack(fill="x", pady=(0, 6))
            return entry

        activity_entry = add_entry("Activity name (optional)")
        time_entry = add_entry("Time (optional)")

        ttk.Label(frame, text="Notes / Special Achievements", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        notes_text = tk.Text(frame, height=4, bg="#0b1729", fg=THEME_FG, highlightthickness=0, relief="flat", insertbackground=THEME_FG)
        notes_text.pack(fill="both", expand=True, pady=(0, 8))

        ttk.Label(frame, text="Food units used (optional)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        food_entry = ttk.Entry(frame, style="App.TEntry")
        food_entry.pack(fill="x", pady=(0, 10))

        ttk.Label(frame, text="Campers in this activity (optional)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        campers_listbox = self._campers_listbox(frame)

        def refresh_campers_list(*args):
            campers_listbox.delete(0, "end")
            camp_obj = get_selected_camp()
            for name in camp_obj.campers:
                campers_listbox.insert("end", name)

        camp_var.trace_add("write", refresh_campers_list)
        refresh_campers_list()
        
        def submit():
            camp_name = camp_var.get()
            date = date_var.get().strip()
            if not date:
                show_error_toast(self.master, "Error", "Date is required.")
                return
            activity_name = activity_entry.get().strip()
            activity_time = time_entry.get().strip()
            notes = notes_text.get("1.0", "end").strip()
            food_units = None
            food_val = food_entry.get().strip()
            if food_val:
                try:
                    food_units = int(food_val)
                except ValueError:
                    show_error_toast(self.master, "Error", "Food units must be a whole number.")
                    return

            sel = campers_listbox.curselection()
            selected_campers = [campers_listbox.get(i) for i in sel]

            if (not activity_name and not activity_time and not notes and food_units is None and not selected_campers):
                show_error_toast(self.master, "Error", "Please fill in at least one field (activity, time, notes, food units or campers)")
                return
            
            res = record_activity_entry_data(
                camp_name,
                date,
                activity_name,
                activity_time,
                notes,
                food_units,
                selected_campers,
            )
            status = res.get("status")
            if status == "ok":
                messagebox.showinfo("Success", f"Entry recorded for {camp_name} on {date}.")
                top.destroy()
            else:
                show_error_toast(self.master, "Error", status or "Unknown error")

        ttk.Button(frame, text="Save Entry", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))
        center_in_place(top)

    def view_activities_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Activities", "No camps exist.")
            return
        
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Activities", "You are not supervising any camps yet.")
            return
        
        indices = select_camp_dialog(
            "Select camp to view activities",
            supervised,
            allow_multiple = False,
            allow_cancel= True,
        )
        if not indices:
            return
        camp = supervised[indices[0]]

        data = activity_participation_data(camp)
        if data["status"] != "ok":
            messagebox.showinfo("Activities",f"No activities recorded for {camp.name}")
            return
        
        top = tk.Toplevel(self)
        top.title(f"Activities for {camp.name}")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, style="Card.TFrame")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Activities for {camp.name}", style="Header.TLabel").pack(anchor="w", pady=(0, 0))

        columns = {
            "date": "Date",
            "time": "Time",
            "activity": "Activity",
            "num_campers": "# Campers",
            "campers": "Campers",
        }
        col_cfg = {
            "date": {"width": 100, "anchor": "w"},
            "time": {"width": 70, "anchor": "w"},
            "activity": {"width": 140, "anchor": "w"},
            "num_campers": {"width": 80, "anchor": "center"},
            "campers": {"width": 220, "anchor": "w"},
        }
        tree, details_text, item_details = self._build_detail_table(frame, columns, col_cfg)

        for date in sorted(camp.activities.keys()):
            entries = camp.activities.get(date, [])
            for e in entries:
                act_name = e.get("activity", "unspecified")
                time_val = e.get("time", "") or ""
                notes = e.get("notes", "") or ""
                food_used = e.get("food_used", "")
                campers = e.get("campers", [])
                if type(campers) == list:
                    camper_list = campers
                else:
                    camper_list = []
                num_campers = len(camper_list)
                campers_str = ", ".join(camper_list)

                
                item_id = tree.insert(
                    "",
                    "end",
                    values=(date, time_val, act_name, num_campers, campers_str),
                )

                item_details[item_id] = {
                    "date": date,
                    "time": time_val,
                    "activity": act_name,
                    "notes": notes,
                    "campers": camper_list,
                    "food_used": food_used,
                }
        def show_details(event=None):
            sel = tree.selection()
            if not sel:
                return
            item_id = sel[0]
            info = item_details.get(item_id, {})
            details_text.delete("1.0", "end")

            lines = []
            lines.append(f"Date: {info.get('date', '')}")
            lines.append(f"Time: {info.get('time', '')}")
            lines.append(f"Activity: {info.get('activity', '')}")

            campers_full = info.get("campers", [])
            campers_str = ", ".join(campers_full) if campers_full else "none recorded"
            lines.append(f"Campers: {campers_str}")

            food_used = info.get("food_used", None)
            if food_used is not None:
                lines.append(f"Food used: {food_used} unit(s)")

            lines.append("")
            lines.append("Notes / log:")
            lines.append(info.get("notes", ""))

            details_text.insert("end", "\n".join(lines))

        tree.bind("<<TreeviewSelect>>", show_details)
        first = tree.get_children()
        if first:
            tree.selection_set(first[0])
            show_details()
        
        def delete_selected():
            sel = tree.selection()
            if not sel:
                show_error_toast(self.master, "Error", "Please select an activity to delete.")
                return

            item_id = sel[0]
            info = item_details.get(item_id)
            if not info:
                return

            confirm = messagebox.askyesno(
                "Delete Activity",
                "Are you sure you want to delete this activity entry?"
            )
            if not confirm:
                return

            date = info.get("date")
            entry = info.get("entry")
            food_used = info.get("food_used", None)

            if date in camp.activities:
                entries = camp.activities[date]
                try:
                    entries.remove(entry)
                except ValueError:
                    pass
                if not entries:
                    del camp.activities[date]

            if food_used:
                if date in camp.daily_food_usage:
                    camp.daily_food_usage[date] -= food_used
                    if camp.daily_food_usage[date] <= 0:
                        del camp.daily_food_usage[date]
            save_to_file()

            tree.delete(item_id)
            del item_details[item_id]
            details_text.delete("1.0", "end")

            remaining = tree.get_children()
            if remaining:
                tree.selection_set(remaining[0])
                show_details()

        ttk.Button(frame, text="Delete Selected Activity", command=delete_selected, style="Danger.TButton",).pack(fill="x", pady=(4, 4))
        first = tree.get_children()
        if first:
            tree.selection_set(first[0])
            show_details()
        center_in_place(top)

    def record_incidents_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Incident", "No camps exist.")
            return
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Incident", "You are not supervising any camps yet.")
            return

        top = tk.Toplevel(self)
        top.title("Record Incident")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Record Incident", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        camp_var, date_var, get_selected_camp = self._camp_date_picker(frame, supervised)

        def add_entry(label, initial=""):
            ttk.Label(frame, text=label, style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            entry = ttk.Entry(frame, style="App.TEntry")
            if initial:
                entry.insert(0, initial)
            entry.pack(fill="x", pady=(0, 6))
            return entry

        time_entry = add_entry("Time (optional)")

        ttk.Label(frame, text="Incident Description", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        notes_text = tk.Text(frame, height=4, bg="#0b1729", fg=THEME_FG, highlightthickness=0, relief="flat",insertbackground=THEME_FG)
        notes_text.pack(fill="both", expand=True, pady=(0, 8))

        ttk.Label(frame, text="Campers involved (optional)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        campers_listbox = self._campers_listbox(frame)
    
        def refresh_campers_list(*args):
            campers_listbox.delete(0, "end")
            camp_obj = get_selected_camp()
            # Here camp_obj.campers is your list of camper names for that camp
            for name in camp_obj.campers:
                campers_listbox.insert("end", name)
        camp_var.trace_add("write", refresh_campers_list)
        refresh_campers_list()

        def save_incident():
            camp_name = camp_var.get()
            date = date_var.get()
            description = notes_text.get("1.0", "end").strip()
            time_val = time_entry.get().strip()

            if not date:
                show_error_toast(self.master, "Error", "Please select a date.")
                return
            if not description:
                show_error_toast(self.master, "Error", "Please enter a description.")
                return

            selected = campers_listbox.curselection()
            camper_names = [campers_listbox.get(i) for i in selected]

            res = record_incident_entry_data(camp_name, date, description, camper_names, time_val)
            if res.get("status") == "ok":
                messagebox.showinfo("Saved", "Incident recorded.")
                top.destroy()
            else:
                messagebox.showerror("Error", "Could not save incident.")

        ttk.Button(frame, text="Save Incident", command=save_incident, style="Primary.TButton").pack(fill="x", pady=(4,0))
        center_in_place(top)

    def view_incidents_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Incidents", "No camps exist.")
            return

        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Incidents", "You are not supervising any camps yet.")
            return

        indices = select_camp_dialog(
            "Select camp to view incidents",
            supervised,
            allow_multiple = False,
            allow_cancel= True,
        )
        if not indices:
            return
        camp = supervised[indices[0]]
        if not camp.incidents:
            messagebox.showinfo("Incidents", f"No incidents recorded for {camp.name}.")
            return

        top = tk.Toplevel(self)
        top.title(f"Incidents - {camp.name}")
        top.configure(bg=THEME_BG)
        ttk.Label(top, text=f"Incidents for {camp.name}", style= "Header.TLabel").pack(anchor="w", padx=9, pady=(8,4))
        frame = ttk.Frame(top, style="Card.TFrame")  # FIXED parent here
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        columns = {"date": "Date", "description": "Description", "campers": "Campers"}
        col_cfg = {
            "date": {"width": 90, "anchor": "w"},
            "description": {"width": 240, "anchor": "w"},
            "campers": {"width": 180, "anchor": "w"},
        }
        tree, details_text, item_details = self._build_detail_table(frame, columns, col_cfg)

        for inc in camp.incidents:
            date = inc.get("date", "")
            desc = inc.get("description", "")
            time_val = inc.get("time", "") or ""
            camper_list = inc.get("campers", [])
            camper_str = ", ".join(camper_list) if camper_list else "none"

            item_id = tree.insert("", "end", values=(date, desc, camper_str))
            item_details[item_id] = inc  



        def show_details(event=None):
            sel = tree.selection()
            if not sel:
                return
            item = sel[0]
            info = item_details.get(item, {})
            details_text.delete("1.0", "end")
            time_val = info.get("time","")

            lines = []
            lines.append(f"Date: {info.get('date', '')}")
            lines.append("")
            lines.append("Time:")
            lines.append(time_val)
            lines.append("")
            lines.append("Description:")
            lines.append(info.get("description", ""))
            campers = info.get("campers", [])
            campers_str = ", ".join(campers) if campers else "none"
            lines.append("")
            lines.append(f"Campers involved: {campers_str}")

            details_text.insert("end", "\n".join(lines))

        tree.bind("<<TreeviewSelect>>", show_details)
        first = tree.get_children()
        if first:
            tree.selection_set(first[0])
            show_details()
        
        def delete_selected():
            sel = tree.selection()
            if not sel:
                show_error_toast(self.master, "Error", "Please select an incident to delete.")
                return

            item_id = sel[0]
            info = item_details.get(item_id)
            if not info:
                return

            confirm = messagebox.askyesno(
                "Delete Incident",
                "Are you sure you want to delete this incident entry?"
            )
            if not confirm:
                return

            try:
                camp.incidents.remove(info)
            except ValueError:
                pass
            save_to_file()

            tree.delete(item_id)
            del item_details[item_id]
            details_text.delete("1.0", "end")

            remaining = tree.get_children()
            if remaining:
                tree.selection_set(remaining[0])
                show_details()

        ttk.Button(frame, text="Delete Selected Incident", command=delete_selected, style="Danger.TButton",).pack(fill="x", pady=(4, 4))
        first = tree.get_children()
        if first:
            tree.selection_set(first[0])
            show_details()
        center_in_place(top)

    # --- Stats helpers ---
    def _format_stats_for_camp(self, camp, scores_map, money_map):
        lines = []
        lines.append(f"{camp.name} ({camp.location}) {camp.start_date} -> {camp.end_date}")
        lines.append(f"Type: {camp.camp_type} | Engagement: {scores_map.get(camp.name, 'N/A')}")
        if camp.name in money_map:
            lines.append(f"Money earned: ${money_map[camp.name]}")
        stats = activity_stats_data(camp)
        if stats["status"] == "ok":
            food_used = stats['total_food_used'] if stats['total_food_used'] is not None else 0
            lines.append(f"Activities: {stats['total_entries']} | Food used: {food_used}")
        else:
            lines.append("Activities: none")
        return "\n".join(lines)

    def _render_stats_window(self, parent, title, text_lines):
        top = tk.Toplevel(parent)
        top.title(title)
        body = ttk.Frame(top, padding=8, style="Card.TFrame")
        body.pack(fill="both", expand=True)
        text = tk.Text(body, width=70, height=25)
        text.pack(fill="both", expand=True, pady=(0, 8))
        text.insert("end", "\n".join(text_lines))
        center_in_place(top)
        return top, body


    def stats_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Stats", "No camps exist.")
            return
        indices = select_camp_dialog("Select a camp for stats (cancel to close)", camps, allow_multiple=False, allow_cancel=True, allow_view_all=True)
        scores = dict(engagement_scores_data())
        money_map = dict(money_earned_per_camp_data())

        if indices is None:
            return
        if indices == "ALL":
            all_lines = []
            for camp in camps:
                all_lines.append(self._format_stats_for_camp(camp, scores, money_map))
                all_lines.append("")  # spacer
            self._render_stats_window(self, "All Camp Stats", all_lines)
            return
        if not indices:
            return

        camp_obj = camps[indices[0]]
        lines = []
        lines.append(f"Stats for {camp_obj.name}:")
        lines.append(f"Engagement: {scores.get(camp_obj.name, 'N/A')}")
        if camp_obj.name in money_map:
            lines.append(f"Money earned: ${money_map[camp_obj.name]}")
        lines.append(f"Total money across camps: ${total_money_earned_value()}")

        stats = activity_stats_data(camp_obj)
        if stats["status"] == "ok":
            lines.append(f"\nActivity summary for {camp_obj.name}:")
            lines.append(f"Total entries: {stats['total_entries']}")
            if stats["total_food_used"] is not None:
                lines.append(f"Total food used: {stats['total_food_used']} units")
        else:
            lines.append(f"\nNo activities recorded for {camp_obj.name}.")

        top, body = self._render_stats_window(self, "Scout Stats", lines)
        ttk.Button(
            body,
            text="Show all camp stats",
            command=lambda: self._render_stats_window(
                top,
                "All Camp Stats",
                [self._format_stats_for_camp(c, scores, money_map) + "\n" for c in camps],
            ),
            style="Primary.TButton",
        ).pack(fill="x", pady=(0, 4))

    def messaging_ui(self):
        top = tk.Toplevel(self)
        top.title("Messaging")
        top.configure(bg=THEME_BG)
        center_window(top, width=420, height=240)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Messaging", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))
        ttk.Button(frame, text="Direct Messages", command=lambda: open_chat_window(self.master, self.username, role="scout leader"), style="Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(frame, text="Group Chat", command=lambda: open_group_chat_window(self.master, self.username, role="scout leader")).pack(fill="x", pady=4)
        ttk.Button(frame, text="Close", command=top.destroy).pack(fill="x", pady=(8, 0))

    def logout(self):
        root = self.master
        for child in list(root.winfo_children()):
            child.destroy()
        root.title("CampTrack Login")
        init_style(root)
        state_info = capture_window_state(root)
        restore_geometry(root, state_info, min_w=1040, min_h=820)
        LoginWindow(root)

def simple_prompt(prompt):
    return simpledialog.askstring("Input", prompt)


def simple_prompt_int(prompt):
    val = simpledialog.askinteger("Input", prompt)
    return val


def select_camp_dialog(title, camps, allow_multiple=False, allow_cancel=False, allow_view_all=False):
    """Return list of selected indices from camps via a listbox dialog."""
    def build_dialog():
        top = tk.Toplevel()
        top.title(title)
        center_window(top, width=520, height=380)
        top.minsize(400, 260)
        top.configure(bg=THEME_BG)
        wrapper = ttk.Frame(top, padding=12, style="Card.TFrame")
        wrapper.pack(fill="both", expand=True)

        selectmode = "extended" if allow_multiple else "browse"
        lb_frame = ttk.Frame(wrapper, style="Card.TFrame")
        lb_frame.pack(fill="both", expand=True, padx=6, pady=6)
        listbox = tk.Listbox(
            lb_frame,
            selectmode=selectmode,
            width=60,
            bg="#0b1729",
            fg=THEME_FG,
            selectbackground=THEME_ACCENT,
            highlightthickness=0,
            relief="flat",
        )
        scrollbar = ttk.Scrollbar(lb_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)

        for camp in camps:
            leaders = ",".join(camp.scout_leaders) if camp.scout_leaders else "None"
            listbox.insert("end", f"{camp.name} ({camp.location}) {camp.start_date}->{camp.end_date} | Leaders: {leaders}")

        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=5)
        return top, listbox, btn_frame

    top, listbox, btn_frame = build_dialog()
    result = {"indices": None}

    def on_ok():
        sel = listbox.curselection()
        result["indices"] = [int(i) for i in sel]
        top.destroy()

    def on_cancel():
        result["indices"] = None
        top.destroy()

    def on_view_all():
        result["indices"] = "ALL"
        top.destroy()

    tk.Button(btn_frame, text="OK", command=on_ok).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
    if allow_cancel:
        tk.Button(btn_frame, text="Skip", command=on_cancel).pack(side="left", padx=5)
    if allow_view_all:
        tk.Button(btn_frame, text="View all", command=on_view_all).pack(side="left", padx=5)

    center_in_place(top)
    top.grab_set()
    top.wait_window()
    return result["indices"]

def capture_window_state(win):
    win.update_idletasks()
    return {
        "width": win.winfo_width(),
        "height": win.winfo_height(),
        "state": win.state(),
        "geom": win.winfo_geometry(),
        "screen_w": win.winfo_screenwidth(),
        "screen_h": win.winfo_screenheight(),
    }


def apply_window_state(win, state_info, min_w, min_h):
    was_full = (
        state_info["state"] != "normal"
        or (state_info["width"] >= state_info["screen_w"] * 0.9 and state_info["height"] >= state_info["screen_h"] * 0.9)
    )
    if was_full:
        win.minsize(state_info["screen_w"], state_info["screen_h"])
        try:
            win.state("zoomed")
        except Exception:
            win.attributes("-fullscreen", True)
    else:
        win.minsize(min_w, min_h)
        target_w = max(state_info["width"], min_w)
        target_h = max(state_info["height"], min_h)
        center_window(win, width=target_w, height=target_h)


def restore_geometry(win, state_info, min_w=1040, min_h=820):
    """Restore size/position without recentering; fallback to centering if unknown."""
    win.update_idletasks()
    w = max(state_info.get("width", min_w), min_w)
    h = max(state_info.get("height", min_h), min_h)
    geom = state_info.get("geom")
    try:
        if geom and "+" in geom:
            parts = geom.split("+")
            if len(parts) >= 3 and "x" in parts[0]:
                x = int(parts[1])
                y = int(parts[2])
                win.minsize(w, h)
                win.geometry(f"{w}x{h}+{x}+{y}")
                return
    except Exception:
        pass
    win.minsize(w, h)
    center_window(win, width=w, height=h)


def init_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=THEME_BG)

    base_font = ("Helvetica Neue", 11)
    header_font = ("Helvetica Neue", 16, "bold")
    title_font = ("Helvetica Neue", 20, "bold")
    subtitle_font = ("Helvetica Neue", 11)

    # Frames / cards
    style.configure("TFrame", background=THEME_BG)
    style.configure("App.TFrame", background=THEME_BG, padding=SPACING["md"])
    style.configure("Card.TFrame", background=THEME_CARD, padding=SPACING["lg"])
    style.configure("Inset.TFrame", background=THEME_CARD_ALT, padding=SPACING["md"])

    # General labels
    style.configure(
        "TLabel",
        background=THEME_CARD,
        foreground=THEME_FG,
        font=base_font,
        padding=2,
    )

    style.configure(
        "Header.TLabel",
        font=header_font,
        background=THEME_CARD,
        foreground=THEME_FG,
    )

    style.configure(
        "Title.TLabel",
        font=title_font,
        background=THEME_CARD,
        foreground=THEME_FG,
    )

    style.configure(
        "Subtitle.TLabel",
        font=subtitle_font,
        background=THEME_CARD,
        foreground=THEME_MUTED,
    )

    style.configure(
        "FieldLabel.TLabel",
        font=base_font,
        background=THEME_CARD,
        foreground="#e5e7eb",
    )

    style.configure(
        "Error.TLabel",
        font=("Helvetica Neue", 10),
        background=THEME_CARD,
        foreground="#fca5a5",
    )

    # Labelframes
    style.configure("TLabelframe", background=THEME_CARD, foreground=THEME_FG, padding=SPACING["sm"])
    style.configure(
        "TLabelframe.Label",
        background=THEME_CARD,
        foreground=THEME_FG,
        font=("Helvetica Neue", 11, "bold"),
    )

    # Entries
    style.configure(
        "App.TEntry",
        fieldbackground="#0b1729",
        foreground=THEME_FG,
        insertcolor=THEME_FG,
        bordercolor="#1f2937",
        lightcolor=THEME_ACCENT,
        darkcolor="#000000",
        relief="flat",
        padding=6,
    )

    # Base button
    style.configure(
        "TButton",
        padding=SPACING["sm"],
        background=THEME_ACCENT,
        foreground=THEME_FG,
        font=base_font,
        borderwidth=0,
    )
    style.map(
        "TButton",
        background=[
            ("active", THEME_ACCENT_ACTIVE),
            ("pressed", THEME_ACCENT_PRESSED),
            ("disabled", "#1f2937"),
        ],
        foreground=[("disabled", "#9ca3af")],
    )

    # Primary button (e.g. login)
    style.configure(
        "Primary.TButton",
        padding=SPACING["sm"],
        background=THEME_ACCENT,
        foreground=THEME_FG,
        font=("Helvetica Neue", 11, "bold"),
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", THEME_ACCENT_ACTIVE),
            ("pressed", THEME_ACCENT_PRESSED),
            ("disabled", "#1f2937"),
        ],
        foreground=[("disabled", "#9ca3af")],
    )

    # Danger button (logout, delete, etc.)
    style.configure(
        "Danger.TButton",
        padding=SPACING["sm"],
        background="#dc2626",
        foreground=THEME_FG,
        font=("Helvetica Neue", 11, "bold"),
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#b91c1c"), ("pressed", "#991b1b")],
        foreground=[("disabled", "#9ca3af")],
    )

    # Separator
    style.configure(
        "TSeparator",
        background=THEME_MUTED,
        foreground=THEME_MUTED,
        bordercolor=THEME_MUTED,
        darkcolor=THEME_MUTED,
        lightcolor=THEME_MUTED,
    )

    # Ghost button for nav
    style.configure(
        "Ghost.TButton",
        padding=SPACING["sm"],
        background=THEME_CARD,
        foreground=THEME_FG,
        font=base_font,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Ghost.TButton",
        background=[("active", THEME_CARD_ALT), ("pressed", THEME_CARD_ALT)],
        foreground=[("disabled", "#6b7280")],
    )


def center_window(win, width=500, height=400):
    """Center a window on the screen with optional default size."""
    try:
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        pass


def center_in_place(win):
    """Center a window using its current size without resizing it."""
    try:
        win.update_idletasks()
        center_window(win, width=win.winfo_width(), height=win.winfo_height())
    except Exception:
        pass


def launch_login():
    root = tk.Tk()
    root.withdraw()
    root.title("CampTrack Login")
    # Start larger so role windows retain space for nav + content
    root.minsize(1024, 768)
    root.configure(bg=THEME_BG)
    init_style(root)
    LoginWindow(root)
    center_window(root, width=1120, height=820)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    load_logins()
    launch_login()
