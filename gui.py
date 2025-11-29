import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from datetime import datetime
from PIL import Image, ImageTk
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
from features.notifications import load_notifications
from features.scout import (
    assign_camps_to_leader,
    bulk_assign_campers_from_csv,
    assign_food_amount_pure,
    record_activity_entry_data,
    engagement_scores_data,
    money_earned_per_camp_data,
    total_money_earned_value,
    activity_stats_data,
    find_camp_by_name,
)
from messaging import get_conversations_for_user, get_conversation, send_message

LOGO_GREEN = "#487C56"       # match logo green
THEME_BG = "#0b1f36"         # window background
THEME_CARD = "#12263f"       # card background
THEME_FG = "#e6f1ff"         # main text
THEME_MUTED = "#cbd5f5"      # subtle/secondary text
THEME_ACCENT = LOGO_GREEN    # primary accent now matches logo
THEME_ACCENT_ACTIVE = "#43a047"
THEME_ACCENT_PRESSED = "#388e3c"


_GIF_CACHE = {}


def _load_gif_frames_raw(name):
    """Return list of raw RGBA frames for a gif, cached."""
    if name in _GIF_CACHE:
        return _GIF_CACHE[name]
    path = os.path.join(os.path.dirname(__file__), name)
    frames = []
    if os.path.exists(path):
        try:
            im = Image.open(path)
            while True:
                frames.append(im.copy().convert("RGBA"))
                im.seek(im.tell() + 1)
        except EOFError:
            pass
        except Exception:
            frames = []
    _GIF_CACHE[name] = frames
    return frames


def _attach_gif_background(container, gif_name="campfire.gif", delay=100, start_delay=100):
    """Attach a full-window animated gif to a container."""
    container.bg_label = tk.Label(container, bd=0, highlightthickness=0)
    container.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    container.bg_label.configure(bg=THEME_BG)
    container.bg_label.lower()
    container._bg_frames_raw = _load_gif_frames_raw(gif_name)
    container._bg_frame_index = 0
    container._bg_photo = None
    container._bg_last_size = None
    container._bg_resized_cache = {}

    def render(index):
        if not container._bg_frames_raw:
            return
        w = max(container.winfo_width(), container.winfo_reqwidth(), 1)
        h = max(container.winfo_height(), container.winfo_reqheight(), 1)
        if w == 1 and h == 1:
            container.after(30, lambda: render(index))
            return
        size_key = (w, h)
        if size_key != container._bg_last_size:
            resized = [ImageTk.PhotoImage(frame.resize((w, h), Image.LANCZOS)) for frame in container._bg_frames_raw]
            container._bg_resized_cache[size_key] = resized
            container._bg_last_size = size_key
        frames = container._bg_resized_cache.get(size_key)
        if frames:
            frame = frames[index % len(frames)]
            container.bg_label.configure(image=frame)

    def animate():
        if not container._bg_frames_raw:
            return
        render(container._bg_frame_index)
        container._bg_frame_index = (container._bg_frame_index + 1) % max(1, len(container._bg_frames_raw))
        container.after(delay, animate)

    if container._bg_frames_raw:
        render(0)
        container.after(start_delay, animate)


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
    logo_path = os.path.join(os.path.dirname(__file__), "image.png")
    if not os.path.exists(logo_path):
        return None
    try:
        with Image.open(logo_path) as im:
            im.thumbnail((max_px, max_px), Image.LANCZOS)
            return ImageTk.PhotoImage(im)
    except Exception:
        return None

class LoginWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=0, style="App.TFrame")
        self.master = master
        self.pack(fill="both", expand=True)

        # --- Animated background ---
        self.bg_label = tk.Label(self, bd=0, highlightthickness=0)
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bg_label.configure(bg=THEME_BG)
        self.bg_frames = []
        self.bg_frame_index = 0
        self._load_campfire_frames()
        if self.bg_frames:
            # delay start so login shows theme bg momentarily
            self.after(100, self._animate_background)

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

    def _load_campfire_frames(self):
        """Load frames from campfire.gif into self.bg_frames."""
        gif_path = os.path.join(os.path.dirname(__file__), "campfire.gif")
        if not os.path.exists(gif_path):
            return
        try:
            im = Image.open(gif_path)
        except Exception:
            return

        frames = []
        try:
            while True:
                frame = im.copy()
                w = max(self.master.winfo_screenwidth(), 800)
                h = max(self.master.winfo_screenheight(), 700)
                frame = frame.resize((w, h), Image.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame))
                im.seek(im.tell() + 1)
        except EOFError:
            pass
        self.bg_frames = frames

    def _animate_background(self):
        """Loop through GIF frames on the background label."""
        if not self.bg_frames:
            return
        frame = self.bg_frames[self.bg_frame_index]
        self.bg_label.configure(image=frame)
        self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_frames)
        self.after(80, self._animate_background)

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
            apply_window_state(root, state_info, min_w=760, min_h=600)
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
        _attach_gif_background(self, gif_name="campfire1.gif", start_delay=500)
        self.pack(fill="both", expand=True)
        wrapper = ttk.Frame(self, padding=18, style="Card.TFrame", width=520)
        wrapper.pack(expand=True, padx=20, pady=16)

        self.logo_small = load_logo(64)
        header = ttk.Frame(wrapper, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        if self.logo_small:
            ttk.Label(header, image=self.logo_small, background=THEME_CARD).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 8))
        ttk.Label(header, text="Administrator", style="Header.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Admin tools", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")

        user_frame = ttk.LabelFrame(wrapper, text="User Management", padding=12, style="Card.TFrame")
        user_frame.pack(fill="both", expand=True, pady=(0, 12))
        for text, cmd in [
            ("View all users", self.list_users_ui),
            ("Add a new user", self.add_user_ui),
            ("Edit a user's password", self.edit_user_password_ui),
            ("Delete a user", self.delete_user_ui),
            ("Disable a user", self.disable_user_ui),
            ("Enable a user", self.enable_user_ui),
        ]:
            btn_style = "TButton"
            if "Add" in text:
                btn_style = "Primary.TButton"
            if "Delete" in text or "Disable" in text:
                btn_style = "Danger.TButton"
            ttk.Button(user_frame, text=text, command=cmd, style=btn_style).pack(fill="x", pady=2)

        misc_frame = ttk.LabelFrame(wrapper, text="Other", padding=12, style="Card.TFrame")
        misc_frame.pack(fill="both", expand=True, pady=(0, 12))
        ttk.Button(misc_frame, text="Messaging", command=self.messaging_ui).pack(fill="x", pady=2)
        ttk.Button(misc_frame, text="Logout", command=self.logout, style="Danger.TButton").pack(fill="x", pady=2)

    def list_users_ui(self):
        top = tk.Toplevel(self)
        top.title("All Users")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=16, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        header = ttk.Frame(frame, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="All Users", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Admin, Scout Leader, Logistics Coordinator", style="Subtitle.TLabel").pack(anchor="w")
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))

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

        def load_disabled_set():
            s = set()
            try:
                with open('disabled_logins.txt', 'r') as file:
                    disabled_login = file.read().strip(',')
                    if disabled_login:
                        s = {x for x in disabled_login.split(',') if x}
            except FileNotFoundError:
                pass
            return s

        def save_disabled_set(s):
            with open('disabled_logins.txt', 'w') as f:
                f.write(",".join(sorted(s)))

        def add_row(role, user, ds):
            status = "Disabled" if user['username'] in ds else "Active"
            tree.insert("", "end", values=(role, user['username'], user['password'], status))

        def refresh_tree():
            for child in tree.get_children():
                tree.delete(child)
            ds = load_disabled_set()
            for admin in users['admin']:
                add_row("Admin", admin, ds)
            for role in ['scout leader', 'logistics coordinator']:
                for user in users[role]:
                    add_row(role.title(), user, ds)
            if len(tree.get_children()) == 0:
                tree.insert("", "end", values=("—", "No users found.", "", ""))
            refresh_scrollbar()
            tree.after_idle(refresh_scrollbar)

        def get_selected():
            sel = tree.selection()
            if not sel:
                show_error_toast(self.master, "Error", "Please select a user.")
                return None
            vals = tree.item(sel[0], "values")
            if not vals or vals[0] == "—":
                show_error_toast(self.master, "Error", "Please select a valid user.")
                return None
            return {"role": vals[0], "username": vals[1], "password": vals[2], "item": sel[0]}

        def ensure_unique_username(name):
            existing = {u['username'] for u in users['admin']}
            existing |= {u['username'] for u in users['scout leader']}
            existing |= {u['username'] for u in users['logistics coordinator']}
            return name not in existing

        def edit_password():
            sel = get_selected()
            if not sel:
                return
            dlg = tk.Toplevel(self)
            dlg.title("Edit Password")
            dlg.configure(bg=THEME_BG)
            frame = ttk.Frame(dlg, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text=f"Edit password for {sel['username']}", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            ttk.Label(frame, text="New password", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            pwd_entry = ttk.Entry(frame, style="App.TEntry", show="*")
            pwd_entry.pack(fill="x", pady=(0, 10))

            def submit():
                new_pwd = pwd_entry.get()
                role_key = sel['role'].lower()
                for u in users[role_key]:
                    if u['username'] == sel['username']:
                        u['password'] = new_pwd
                        break
                save_logins()
                refresh_tree()
                dlg.destroy()

            btns = ttk.Frame(frame, style="Card.TFrame")
            btns.pack(fill="x")
            ttk.Button(btns, text="Save", command=submit, style="Primary.TButton").pack(side="left", padx=4, pady=4)
            ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=4, pady=4)
            dlg.grab_set()

        def delete_user():
            sel = get_selected()
            if not sel:
                return
            if not messagebox.askyesno("Delete", f"Delete user {sel['username']}?"):
                return
            role_key = sel['role'].lower()
            users[role_key] = [u for u in users[role_key] if u['username'] != sel['username']]
            # also remove from disabled list if present
            ds = load_disabled_set()
            if sel['username'] in ds:
                ds.remove(sel['username'])
                save_disabled_set(ds)
            save_logins()
            refresh_tree()

        def toggle_disable(enable=False):
            sel = get_selected()
            if not sel:
                return
            ds = load_disabled_set()
            if enable:
                if sel['username'] in ds:
                    ds.remove(sel['username'])
                    save_disabled_set(ds)
                enable_login(sel['username'])
            else:
                disabled_logins(sel['username'])
                ds.add(sel['username'])
                save_disabled_set(ds)
            refresh_tree()

        def change_username():
            sel = get_selected()
            if not sel:
                return
            dlg = tk.Toplevel(self)
            dlg.title("Change Username")
            dlg.configure(bg=THEME_BG)
            frame = ttk.Frame(dlg, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text=f"Change username for {sel['username']}", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            ttk.Label(frame, text="New username", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            name_entry = ttk.Entry(frame, style="App.TEntry")
            name_entry.insert(0, sel['username'])
            name_entry.pack(fill="x", pady=(0, 10))

            def submit():
                new_name = name_entry.get().strip()
                if not new_name:
                    show_error_toast(self.master, "Error", "Username cannot be blank.")
                    return
                if not ensure_unique_username(new_name):
                    show_error_toast(self.master, "Error", "Username already exists.")
                    return
                role_key = sel['role'].lower()
                for u in users[role_key]:
                    if u['username'] == sel['username']:
                        u['username'] = new_name
                        break
                ds = load_disabled_set()
                if sel['username'] in ds:
                    ds.remove(sel['username'])
                    ds.add(new_name)
                    save_disabled_set(ds)
                save_logins()
                refresh_tree()
                dlg.destroy()

            btns = ttk.Frame(frame, style="Card.TFrame")
            btns.pack(fill="x")
            ttk.Button(btns, text="Save", command=submit, style="Primary.TButton").pack(side="left", padx=4, pady=4)
            ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=4, pady=4)
            dlg.grab_set()

        def change_role():
            sel = get_selected()
            if not sel:
                return
            current = sel['role'].lower()
            roles = ["admin", "scout leader", "logistics coordinator"]
            dlg = tk.Toplevel(self)
            dlg.title("Change Role")
            dlg.configure(bg=THEME_BG)
            frame = ttk.Frame(dlg, padding=14, style="Card.TFrame")
            frame.pack(fill="both", expand=True, padx=12, pady=12)
            ttk.Label(frame, text=f"Change role for {sel['username']}", style="Header.TLabel").pack(anchor="w", pady=(0, 6))
            ttk.Separator(frame).pack(fill="x", pady=(0, 8))
            ttk.Label(frame, text="New role", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            role_var = tk.StringVar(value=current)
            ttk.OptionMenu(frame, role_var, current, *roles).pack(fill="x", pady=(0, 10))

            def submit():
                choice = role_var.get()
                if choice == current:
                    dlg.destroy()
                    return
                if any(u['username'] == sel['username'] for u in users[choice]):
                    show_error_toast(self.master, "Error", "Username already exists in target role.")
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
                    refresh_tree()
                dlg.destroy()

            btns = ttk.Frame(frame, style="Card.TFrame")
            btns.pack(fill="x")
            ttk.Button(btns, text="Save", command=submit, style="Primary.TButton").pack(side="left", padx=4, pady=4)
            ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=4, pady=4)
            dlg.grab_set()

        # action buttons
        btn_frame = ttk.Frame(frame, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="Edit Password", command=edit_password).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Change Username", command=change_username).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Change Role", command=change_role).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Disable", command=lambda: toggle_disable(False), style="Danger.TButton").pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Enable", command=lambda: toggle_disable(True)).pack(side="left", padx=4, pady=2)
        ttk.Button(btn_frame, text="Delete", command=delete_user, style="Danger.TButton").pack(side="left", padx=4, pady=2)

        refresh_tree()

    def add_user_ui(self):
        top = tk.Toplevel(self)
        top.title("Add User")
        top.configure(bg=THEME_BG)
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
            messagebox.showinfo("Success", f"Added {role}: {username}")
            top.destroy()

        ttk.Button(frame, text="Add User", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

    def edit_user_password_ui(self):
        top = tk.Toplevel(self)
        top.title("Edit User Password")
        top.configure(bg=THEME_BG)
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
            messagebox.showinfo("Success", "Password updated.")
            top.destroy()

        ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

    def delete_user_ui(self):
        top = tk.Toplevel(self)
        top.title("Delete User")
        top.configure(bg=THEME_BG)
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
            messagebox.showinfo("Success", f"Deleted {target_user}.")
            top.destroy()

        ttk.Button(frame, text="Delete", command=submit, style="Danger.TButton").pack(fill="x", pady=(4, 0))

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
            messagebox.showinfo("Success", f"Disabled {target_user}.")
            top.destroy()

        ttk.Button(frame, text="Disable", command=submit, style="Danger.TButton").pack(fill="x", pady=(4, 0))

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
            messagebox.showinfo("Success", f"Enabled {target_user}.")
            top.destroy()

        ttk.Button(frame, text="Enable", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

    def messaging_ui(self):
        open_chat_window(self.master, self.username)

    def logout(self):
        state_info = capture_window_state(self.master)
        root = self.master
        for child in list(root.winfo_children()):
            child.destroy()
        root.title("CampTrack Login")
        init_style(root)
        apply_window_state(root, state_info, min_w=480, min_h=360)
        LoginWindow(root)


class LogisticsWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=0, style="App.TFrame")
        self.username = username
        _attach_gif_background(self, gif_name="campfire1.gif", delay=140, start_delay=500)
        master.minsize(640, 640)
        self.pack(fill="both", expand=True)
        wrapper = ttk.Frame(self, padding=18, style="Card.TFrame", width=520)
        wrapper.pack(expand=True, padx=20, pady=16)

        self.logo_small = load_logo(64)
        header = ttk.Frame(wrapper, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        if self.logo_small:
            ttk.Label(header, image=self.logo_small, background=THEME_CARD).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 8))
        ttk.Label(header, text="Logistics Coordinator", style="Header.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Logistics overview", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")

        camp_frame = ttk.LabelFrame(wrapper, text="Camp Management", padding=12, style="Card.TFrame")
        camp_frame.pack(fill="both", expand=True, pady=(0, 14))
        ttk.Label(camp_frame, text="Pick a camp to create, edit, or delete.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 6))
        for text, cmd in [
            ("Manage Camps", self.manage_camps_menu),
            ("Food Allocation", self.food_allocation_menu),
            ("Financial Settings", self.financial_settings_ui),
        ]:
            btn_style = "Primary.TButton" if "Manage" in text else "TButton"
            ttk.Button(camp_frame, text=text, command=cmd, style=btn_style).pack(fill="x", pady=6)

        viz_frame = ttk.LabelFrame(wrapper, text="Insights & Notifications", padding=12, style="Card.TFrame")
        viz_frame.pack(fill="both", expand=True, pady=(0, 14))
        for text, cmd in [
            ("Dashboard", self.dashboard_ui),
            ("Visualise Data", self.visualise_menu),
            ("Notifications", self.notifications_ui),
            ("Messaging", self.messaging_ui),
        ]:
            ttk.Button(viz_frame, text=text, command=cmd).pack(fill="x", pady=6)

        ttk.Button(wrapper, text="Logout", command=self.logout, style="Danger.TButton").pack(fill="x", pady=8)

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

            def submit():
                try:
                    val = int(stock_entry.get().strip())
                except ValueError:
                    show_error_toast(self.master, "Error", "Please enter a whole number.")
                    return
                res = set_food_stock_data(camp, val)
                messagebox.showinfo("Result", res.get("status"))
                top.destroy()

            ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

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

            def submit():
                try:
                    val = int(amt_entry.get().strip())
                except ValueError:
                    show_error_toast(self.master, "Error", "Please enter a whole number.")
                    return
                res = top_up_food_data(camp, val)
                messagebox.showinfo("Result", res.get("status"))
                top.destroy()

            ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

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

        def submit():
            try:
                val = int(rate_entry.get().strip())
            except ValueError:
                show_error_toast(self.master, "Error", "Please enter a whole number.")
                return
            res = set_pay_rate_data(camp, val)
            messagebox.showinfo("Result", res.get("status"))
            top.destroy()

        ttk.Button(frame, text="Save", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

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
        text = tk.Text(top, width=80, height=20)
        text.pack(fill="both", expand=True)
        text.insert("end", df.to_string(index=False))
        text.insert("end", "\n\nSummary:\n")
        for k, v in summary.items():
            text.insert("end", f"{k}: {v}\n")

    def notifications_ui(self):
        notes = load_notifications()
        messagebox.showinfo("Notifications", "\n".join(str(n) for n in notes) if notes else "No notifications")

    def visualise_menu(self):
        top = tk.Toplevel(self)
        top.title("Visualise Camp Data")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Visualise Camp Data", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))
        ttk.Button(frame, text="Food Stock per Camp", command=plot_food_stock, style="Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(frame, text="Camper Distribution", command=plot_camper_distribution).pack(fill="x", pady=4)
        ttk.Button(frame, text="Leaders per Camp", command=plot_leaders_per_camp).pack(fill="x", pady=4)
        ttk.Button(frame, text="Engagement Overview", command=plot_engagement_scores).pack(fill="x", pady=4)

    def financial_settings_ui(self):
        self.set_pay_rate_ui()

    def create_camp_ui(self):
        top = tk.Toplevel(self)
        top.title("Create Camp")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Create a new camp", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 10))

        form = ttk.Frame(frame, style="Card.TFrame")
        form.pack(fill="both", expand=True)

        def add_labeled_entry(label_text):
            lbl = ttk.Label(form, text=label_text, style="FieldLabel.TLabel")
            lbl.pack(anchor="w", pady=(0, 2))
            entry = ttk.Entry(form, style="App.TEntry")
            entry.pack(fill="x", pady=(0, 8))
            return entry

        name_entry = add_labeled_entry("Camp name")
        location_entry = add_labeled_entry("Location")

        ttk.Label(form, text="Camp type (1=Day, 2=Overnight, 3=Multiple Days)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        camp_type_entry = ttk.Entry(form, style="App.TEntry")
        camp_type_entry.pack(fill="x", pady=(0, 8))

        start_entry = add_labeled_entry("Start date (YYYY-MM-DD)")
        end_entry = add_labeled_entry("End date (YYYY-MM-DD)")
        food_entry = add_labeled_entry("Initial daily food stock")

        def submit():
            name = name_entry.get().strip()
            location = location_entry.get().strip()
            if not name or not location:
                show_error_toast(self.master, "Error", "Name and location are required.")
                return
            try:
                camp_type = int(camp_type_entry.get().strip())
                if camp_type not in (1, 2, 3):
                    raise ValueError
            except ValueError:
                show_error_toast(self.master, "Error", "Camp type must be 1, 2, or 3.")
                return
            start_date = start_entry.get().strip()
            end_date = end_entry.get().strip()
            for d in (start_date, end_date):
                try:
                    datetime.strptime(d, "%Y-%m-%d")
                except Exception:
                    show_error_toast(self.master, "Error", "Invalid date format.")
                    return
            try:
                food_stock = int(food_entry.get().strip())
                if food_stock < 0:
                    raise ValueError
            except ValueError:
                show_error_toast(self.master, "Error", "Food stock must be a non-negative integer.")
                return

            read_from_file()
            Camp(name, location, camp_type, start_date, end_date, food_stock)
            save_to_file()
            messagebox.showinfo("Success", f"Camp {name} created.")
            top.destroy()

        ttk.Button(frame, text="Create", command=submit, style="Primary.TButton").pack(fill="x", pady=(8, 0))

    def edit_camp_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Edit Camp", "No camps exist.")
            return
        top = tk.Toplevel(self)
        top.title("Edit Camp")
        top.configure(bg=THEME_BG)
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
        start_entry = add_labeled_entry("Start date (YYYY-MM-DD)", camp.start_date)
        end_entry = add_labeled_entry("End date (YYYY-MM-DD)", camp.end_date)
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
            new_start = start_entry.get().strip()
            new_end = end_entry.get().strip()
            for d in (new_start, new_end):
                try:
                    datetime.strptime(d, "%Y-%m-%d")
                except Exception:
                    show_error_toast(self.master, "Error", "Invalid date format.")
                    return

            camp_obj.name = name_entry.get().strip() or camp_obj.name
            camp_obj.location = loc_entry.get().strip() or camp_obj.location
            camp_obj.camp_type = ct
            camp_obj.start_date = new_start or camp_obj.start_date
            camp_obj.end_date = new_end or camp_obj.end_date
            camp_obj.food_stock = nf
            camp_obj.pay_rate = pr
            save_to_file()
            messagebox.showinfo("Success", "Camp updated.")
            top.destroy()

        ttk.Button(frame, text="Save changes", command=submit, style="Primary.TButton").pack(fill="x", pady=(8, 0))

    def delete_camp_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Delete Camp", "No camps exist.")
            return
        top = tk.Toplevel(self)
        top.title("Delete Camp")
        top.configure(bg=THEME_BG)
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
            save_to_file()
            messagebox.showinfo("Success", f"Camp '{camp_obj.name}' deleted.")
            top.destroy()

        ttk.Button(frame, text="Delete", command=delete, style="Danger.TButton").pack(fill="x", pady=(8, 0))

    def messaging_ui(self):
        open_chat_window(self.master, self.username)

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
        top.grab_set()
        top.wait_window()
        return result["camp"]

    def logout(self):
        state_info = capture_window_state(self.master)
        root = self.master
        for child in list(root.winfo_children()):
            child.destroy()
        root.title("CampTrack Login")
        init_style(root)
        apply_window_state(root, state_info, min_w=480, min_h=360)
        LoginWindow(root)


class ScoutWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=0, style="App.TFrame")
        self.username = username
        _attach_gif_background(self, gif_name="campfire1.gif", delay=140, start_delay=500)
        master.minsize(640, 640)
        self.pack(fill="both", expand=True)
        wrapper = ttk.Frame(self, padding=18, style="Card.TFrame", width=520)
        wrapper.pack(expand=True, padx=20, pady=16)

        self.logo_small = load_logo(64)
        header = ttk.Frame(wrapper, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        if self.logo_small:
            ttk.Label(header, image=self.logo_small, background=THEME_CARD).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 8))
        ttk.Label(header, text="Scout Leader", style="Header.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Scouting tools", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")

        actions = ttk.LabelFrame(wrapper, text="Camp Actions", padding=12, style="Card.TFrame")
        actions.pack(fill="both", expand=True, pady=(0, 14))
        ttk.Label(actions, text="Select camps, import campers, and set food needs.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 6))
        for text, cmd in [
            ("Select Camp(s) to supervise", self.select_camps_ui),
            ("Stop supervising Camp(s)", self.unsupervise_camps_ui),
            ("Import Campers", self.bulk_assign_ui),
            ("Set Food per Camper", self.food_req_ui),
            ("Record Activity", self.record_activity_ui),
        ]:
            btn_style = "Primary.TButton" if "Select camps" in text else "TButton"
            ttk.Button(actions, text=text, command=cmd, style=btn_style).pack(fill="x", pady=6)

        stats_frame = ttk.LabelFrame(wrapper, text="Insights & Messaging", padding=12, style="Card.TFrame")
        stats_frame.pack(fill="both", expand=True, pady=(0, 14))
        for text, cmd in [
            ("View Stats", self.stats_ui),
            ("Private Messages", self.messaging_ui),
            ("Camp Group Chats", self.group_chat_ui),
            ("Logout", self.logout),
        ]:
            style = "Danger.TButton" if "Logout" in text else "TButton"
            ttk.Button(stats_frame, text=text, command=cmd, style=style).pack(fill="x", pady=6)

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
        res = assign_camps_to_leader(camps, self.username, indices)
        status = res.get("status")
        if status == "ok":
            messagebox.showinfo("Success", f"Assigned: {', '.join(res.get('selected', []))}")
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
        top.title("Bulk Assign Campers")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Bulk assign campers from CSV", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Label(frame, text="Select a camp and CSV to import campers.", style="Subtitle.TLabel").pack(pady=(0, 8))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        # Camp list
        lb_frame = ttk.Frame(frame, style="Card.TFrame")
        lb_frame.pack(fill="both", expand=True, pady=4)
        camp_list = tk.Listbox(
            lb_frame,
            bg="#0b1729",
            fg=THEME_FG,
            selectbackground=THEME_ACCENT,
            highlightthickness=0,
            relief="flat",
            height=6,
        )
        scroll = ttk.Scrollbar(lb_frame, orient="vertical", command=camp_list.yview)
        camp_list.configure(yscrollcommand=scroll.set)
        camp_list.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        scroll.pack(side="right", fill="y", padx=(0, 4), pady=4)
        for camp in supervised:
            camp_list.insert("end", f"{camp.name} ({camp.location})")

        ttk.Separator(frame).pack(fill="x", pady=(4, 8))

        # File picker
        path_var = tk.StringVar()
        ttk.Label(frame, text="CSV file", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        path_entry = ttk.Entry(frame, textvariable=path_var, style="App.TEntry")
        path_entry.pack(fill="x", pady=(0, 6))

        def browse():
            fp = filedialog.askopenfilename(title="Select campers CSV", filetypes=[("CSV files", "*.csv")])
            if fp:
                path_var.set(fp)

        ttk.Button(frame, text="Browse", command=browse).pack(fill="x", pady=(0, 10))

        def submit():
            sel = camp_list.curselection()
            if not sel:
                show_error_toast(self.master, "Error", "Please select a camp.")
                return
            filepath = path_var.get().strip()
            if not filepath:
                show_error_toast(self.master, "Error", "Please choose a CSV file.")
                return
            camp = supervised[int(sel[0])]
            res = bulk_assign_campers_from_csv(camp.name, filepath)
            status = res.get("status")
            if status == "ok":
                added = res.get("added", [])
                messagebox.showinfo("Success", f"Assigned {len(added)} campers to {camp.name}.")
                top.destroy()
            elif status == "file_not_found":
                show_error_toast(self.master, "Error", "CSV file not found.")
            elif status == "camp_not_found":
                show_error_toast(self.master, "Error", "Camp not found.")
            elif status == "no_campers":
                messagebox.showinfo("Result", "No campers in CSV.")
            else:
                show_error_toast(self.master, "Error", status or "Unknown error")

        ttk.Button(frame, text="Import", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

    def food_req_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Food", "No camps exist.")
            return
        supervised = [c for c in camps if self.username in c.scout_leaders]
        if not supervised:
            messagebox.showinfo("Bulk Assign", "You are not supervisiing any camps yet.")
            return
        indices = select_camp_dialog("Select camp to set food requirement", camps, allow_multiple=False)
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
            messagebox.showinfo("Bulk Assign", "You are not supervisiing any camps yet.")
            return
        top = tk.Toplevel(self)
        top.title("Record Activity")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=14, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Record daily activity", style="Header.TLabel").pack(pady=(0, 6))
        ttk.Separator(frame).pack(fill="x", pady=(0, 8))

        ttk.Label(frame, text="Camp", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        camp_var = tk.StringVar(value=camps[0].name)
        ttk.OptionMenu(frame, camp_var, supervised[0].name, *[c.name for c in supervised]).pack(fill="x", pady=(0, 8))

        def add_entry(label, initial=""):
            ttk.Label(frame, text=label, style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
            entry = ttk.Entry(frame, style="App.TEntry")
            if initial:
                entry.insert(0, initial)
            entry.pack(fill="x", pady=(0, 6))
            return entry

        date_entry = add_entry("Date (YYYY-MM-DD)")
        activity_entry = add_entry("Activity name (optional)")
        time_entry = add_entry("Time (optional)")

        ttk.Label(frame, text="Notes / outcomes / incidents", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        notes_text = tk.Text(frame, height=4, bg="#0b1729", fg=THEME_FG, highlightthickness=0, relief="flat")
        notes_text.pack(fill="both", expand=True, pady=(0, 8))

        ttk.Label(frame, text="Food units used (optional)", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 2))
        food_entry = ttk.Entry(frame, style="App.TEntry")
        food_entry.pack(fill="x", pady=(0, 10))

        def submit():
            camp = camp_var.get()
            date = date_entry.get().strip()
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
            res = record_activity_entry_data(camp, date, activity_name, activity_time, notes, food_units)
            status = res.get("status")
            if status == "ok":
                messagebox.showinfo("Success", f"Entry recorded for {camp} on {date}.")
                top.destroy()
            else:
                show_error_toast(self.master, "Error", status or "Unknown error")

        ttk.Button(frame, text="Save Entry", command=submit, style="Primary.TButton").pack(fill="x", pady=(4, 0))

    def stats_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Stats", "No camps exist.")
            return
        lines = []
        lines.append("Engagement:")
        for name, score in engagement_scores_data():
            lines.append(f"{name}: {score}")
        lines.append("\nMoney per camp:")
        for name, earned in money_earned_per_camp_data():
            lines.append(f"{name}: ${earned}")
        lines.append(f"\nTotal money: ${total_money_earned_value()}")

        # optional activity detail
        indices = select_camp_dialog("Select a camp for activity stats (cancel to skip)", camps, allow_multiple=False, allow_cancel=True)
        if indices:
            camp_obj = camps[indices[0]]
            stats = activity_stats_data(camp_obj)
            if stats["status"] == "ok":
                lines.append(f"\nActivity summary for {camp_obj.name}:")
                lines.append(f"Total entries: {stats['total_entries']}")
                if stats["total_food_used"] is not None:
                    lines.append(f"Total food used: {stats['total_food_used']} units")
            else:
                lines.append(f"\nNo activities recorded for {camp_obj.name}.")

        # show in a scrollable window
        top = tk.Toplevel(self)
        top.title("Scout Stats")
        text = tk.Text(top, width=70, height=25)
        text.pack(fill="both", expand=True)
        text.insert("end", "\n".join(lines))

    def messaging_ui(self):
        open_chat_window(self.master, self.username)

    def logout(self):
        state_info = capture_window_state(self.master)
        root = self.master
        for child in list(root.winfo_children()):
            child.destroy()
        root.title("CampTrack Login")
        init_style(root)
        apply_window_state(root, state_info, min_w=480, min_h=360)
        LoginWindow(root)

def simple_prompt(prompt):
    return simpledialog.askstring("Input", prompt)


def simple_prompt_int(prompt):
    val = simpledialog.askinteger("Input", prompt)
    return val


def select_camp_dialog(title, camps, allow_multiple=False, allow_cancel=False):
    """Return list of selected indices from camps via a listbox dialog."""
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

    result = {"indices": None}

    def on_ok():
        sel = listbox.curselection()
        result["indices"] = [int(i) for i in sel]
        top.destroy()

    def on_cancel():
        result["indices"] = None
        top.destroy()

    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="OK", command=on_ok).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
    if allow_cancel:
        tk.Button(btn_frame, text="Skip", command=on_cancel).pack(side="left", padx=5)

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


def init_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=THEME_BG)

    base_font = ("Helvetica", 11)

    # Frames / cards
    style.configure("TFrame", background=THEME_BG)
    style.configure("App.TFrame", background=THEME_BG, padding=12)
    style.configure("Card.TFrame", background=THEME_CARD, padding=18)

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
        font=("Helvetica", 16, "bold"),
        background=THEME_CARD,
        foreground=THEME_FG,
    )

    style.configure(
        "Title.TLabel",
        font=("Helvetica", 20, "bold"),
        background=THEME_CARD,
        foreground=THEME_FG,
    )

    style.configure(
        "Subtitle.TLabel",
        font=("Helvetica", 11),
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
        font=("Helvetica", 10),
        background=THEME_CARD,
        foreground="#fca5a5",
    )

    # Labelframes
    style.configure("TLabelframe", background=THEME_CARD, foreground=THEME_FG, padding=6)
    style.configure(
        "TLabelframe.Label",
        background=THEME_CARD,
        foreground=THEME_FG,
        font=("Helvetica", 11, "bold"),
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
        padding=8,
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
        padding=8,
        background=THEME_ACCENT,
        foreground=THEME_FG,
        font=("Helvetica", 11, "bold"),
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
        padding=8,
        background="#dc2626",
        foreground=THEME_FG,
        font=("Helvetica", 11, "bold"),
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


def launch_login():
    root = tk.Tk()
    root.withdraw()
    root.title("CampTrack Login")
    # Start larger so role windows retain space for full cards/log out buttons
    root.minsize(900, 720)
    root.configure(bg=THEME_BG)
    init_style(root)
    LoginWindow(root)
    center_window(root, width=960, height=760)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    load_logins()
    launch_login()
