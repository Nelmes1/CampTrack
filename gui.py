import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from datetime import datetime

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

THEME_BG = "#0f172a"
THEME_CARD = "#1f2937"
THEME_FG = "#e2e8f0"
THEME_ACCENT = "#2563eb"
THEME_ACCENT_ACTIVE = "#1d4ed8"
THEME_ACCENT_PRESSED = "#1e40af"

class LoginWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12, style="App.TFrame")
        self.master = master
        self.pack(fill="both", expand=True)
        # center the login form in a padded, fixed-width container
        card = ttk.Frame(self, padding=24, width=420, style="Card.TFrame")
        card.pack(expand=True)
        card.pack_propagate(False)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="CampTrack", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(card, text="Welcome! Please log in below.").grid(row=1, column=0, columnspan=2, pady=(0, 14))

        ttk.Label(card, text="Username").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        ttk.Label(card, text="Password").grid(row=3, column=0, sticky="e", padx=8, pady=8)
        self.username = ttk.Entry(card, width=32)
        self.password = ttk.Entry(card, show="*", width=32)
        self.username.grid(row=2, column=1, sticky="ew", padx=8, pady=8)
        self.password.grid(row=3, column=1, sticky="ew", padx=8, pady=8)

        ttk.Button(card, text="Login", command=self.attempt_login).grid(row=4, column=0, columnspan=2, pady=14, padx=8, sticky="ew")

    def attempt_login(self):
        uname = self.username.get().strip()
        pwd = self.password.get()
        load_logins()
        if check_disabled_logins(uname):
            messagebox.showerror("Login failed", "This account has been disabled.")
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
            self.master.destroy()
            app = tk.Tk()
            app.title(f"CampTrack - {role}")
            init_style(app)
            app.minsize(720, 560)
            center_window(app, width=760, height=580)
            if role == "admin":
                AdminWindow(app, uname)
            elif role == "scout leader":
                ScoutWindow(app, uname)
            elif role == "logistics coordinator":
                LogisticsWindow(app, uname)
            app.mainloop()
        else:
            messagebox.showerror("Login failed", "Invalid username or password.")


class AdminWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=16, style="App.TFrame")
        self.username = username
        self.pack(fill="both", expand=True)
        wrapper = ttk.Frame(self, padding=16, style="Card.TFrame", width=720)
        wrapper.pack(expand=True, pady=8)

        ttk.Label(wrapper, text="Administrator Menu", style="Header.TLabel").pack(pady=(0, 10))

        user_frame = ttk.LabelFrame(wrapper, text="User Management", padding=10)
        user_frame.pack(fill="both", expand=True, pady=(0, 8))
        for text, cmd in [
            ("View all users", self.list_users_ui),
            ("Add a new user", self.add_user_ui),
            ("Edit a user's password", self.edit_user_password_ui),
            ("Delete a user", self.delete_user_ui),
            ("Disable a user", self.disable_user_ui),
            ("Enable a user", self.enable_user_ui),
        ]:
            ttk.Button(user_frame, text=text, command=cmd).pack(fill="x", pady=2)

        misc_frame = ttk.LabelFrame(wrapper, text="Other", padding=10)
        misc_frame.pack(fill="both", expand=True)
        ttk.Button(misc_frame, text="Messaging", command=self.messaging_ui).pack(fill="x", pady=2)
        ttk.Button(misc_frame, text="Logout", command=self.logout).pack(fill="x", pady=2)

    def list_users_ui(self):
        lines = []
        for admin in users['admin']:
            lines.append(f"Role: admin, Username: {admin['username']}, Password: {admin['password']}")
        for role in ['scout leader', 'logistics coordinator']:
            for user in users[role]:
                lines.append(f"Role: {role}, Username: {user['username']}, Password: {user['password']}")
        messagebox.showinfo("Users", "\n".join(lines) if lines else "No users found.")

    def prompt_role(self, allow_admin=False):
        roles = ["scout leader", "logistics coordinator"]
        if allow_admin:
            roles.append("admin")
        prompt = "Choose role:\n" + "\n".join(f"[{i+1}] {r}" for i, r in enumerate(roles))
        choice = tk.simpledialog.askinteger("Role", prompt, minvalue=1, maxvalue=len(roles))
        if choice is None:
            return None
        return roles[choice-1]

    def add_user_ui(self):
        role = self.prompt_role(allow_admin=True)
        if not role:
            return
        while True:
            username = simple_prompt("Enter username:")
            if username is None:
                return
            username = username.strip()
            if username == "":
                messagebox.showerror("Error", "Username cannot be blank.")
                continue
            existing = [u['username'] for u in users['admin']]
            existing += [u['username'] for u in users['scout leader']]
            existing += [u['username'] for u in users['logistics coordinator']]
            if username in existing:
                messagebox.showerror("Error", "Username already exists.")
                continue
            break
        pwd = simple_prompt("Enter password (blank allowed):")
        if pwd is None:
            return
        if role == "admin":
            users['admin'].append({'username': username, 'password': pwd})
        else:
            users[role].append({'username': username, 'password': pwd})
        save_logins()
        messagebox.showinfo("Success", f"Added {role}: {username}")

    def edit_user_password_ui(self):
        role = self.prompt_role(allow_admin=True)
        if not role:
            return
        if role == "admin":
            names = [u['username'] for u in users['admin']]
            if not names:
                messagebox.showinfo("Info", "No admin users found.")
                return
            target_user = simple_prompt(f"Enter admin username to edit ({', '.join(names)}):")
            if target_user not in names:
                messagebox.showerror("Error", "User not found.")
                return
        else:
            names = [u['username'] for u in users[role]]
            if not names:
                messagebox.showinfo("Info", f"No users found for role {role}.")
                return
            target_user = simple_prompt(f"Enter username to edit ({', '.join(names)}):")
            if target_user not in names:
                messagebox.showerror("Error", "User not found.")
                return
        new_pwd = simple_prompt(f"Enter new password for {target_user}:")
        if new_pwd is None:
            return
        if role == "admin":
            for u in users['admin']:
                if u['username'] == target_user:
                    u['password'] = new_pwd
                    break
        else:
            for u in users[role]:
                if u['username'] == target_user:
                    u['password'] = new_pwd
                    break
        save_logins()
        messagebox.showinfo("Success", "Password updated.")

    def delete_user_ui(self):
        role = self.prompt_role(allow_admin=False)
        if not role:
            return
        names = [u['username'] for u in users[role]]
        if not names:
            messagebox.showinfo("Info", f"No users found for role {role}.")
            return
        target_user = simple_prompt(f"Enter username to delete ({', '.join(names)}):")
        if target_user not in names:
            messagebox.showerror("Error", "User not found.")
            return
        users[role] = [u for u in users[role] if u['username'] != target_user]
        save_logins()
        messagebox.showinfo("Success", f"Deleted {target_user}.")

    def disable_user_ui(self):
        names = [u['username'] for u in users['admin']]
        names += [u['username'] for u in users['scout leader']]
        names += [u['username'] for u in users['logistics coordinator']]
        target_user = simple_prompt(f"Enter username to disable ({', '.join(names)}):")
        if not target_user or target_user not in names:
            messagebox.showerror("Error", "User not found.")
            return
        disabled_logins(target_user)
        save_logins()
        messagebox.showinfo("Success", f"Disabled {target_user}.")

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
        target_user = simple_prompt(f"Enter username to enable ({', '.join(disabled_usernames)}):")
        if not target_user or target_user not in disabled_usernames:
            messagebox.showerror("Error", "User not found in disabled list.")
            return
        # ensure user still exists
        existing = [u['username'] for u in users['admin']]
        existing += [u['username'] for u in users['scout leader']]
        existing += [u['username'] for u in users['logistics coordinator']]
        if target_user not in existing:
            messagebox.showerror("Error", "User no longer exists.")
            return
        enable_login(target_user)
        messagebox.showinfo("Success", f"Enabled {target_user}.")

    def messaging_ui(self):
        convo_win = tk.Toplevel(self)
        convo_win.title("Messaging")
        convo_win.configure(bg=THEME_BG)
        frame = ttk.Frame(convo_win, padding=12, style="Card.TFrame")
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Conversations").pack()
        listbox = tk.Listbox(frame)
        listbox.pack(fill="both", expand=True, pady=6)
        partners = get_conversations_for_user(self.username)
        for p in partners:
            listbox.insert("end", p)
        ttk.Label(frame, text="Recipient:").pack()
        recipient_entry = ttk.Entry(frame)
        recipient_entry.pack(fill="x", pady=2)
        ttk.Label(frame, text="Message:").pack()
        message_entry = ttk.Entry(frame, width=50)
        message_entry.pack(fill="x", pady=2)

        def send():
            to = recipient_entry.get().strip()
            msg = message_entry.get().strip()
            if to and msg:
                send_message(self.username, to, msg)
                messagebox.showinfo("Sent", f"Message sent to {to}")
        ttk.Button(frame, text="Send", command=send).pack(pady=8, fill="x")

    def logout(self):
        self.master.destroy()
        launch_login()


class LogisticsWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=16, style="App.TFrame")
        self.username = username
        self.pack(fill="both", expand=True)
        wrapper = ttk.Frame(self, padding=16, style="Card.TFrame", width=720)
        wrapper.pack(expand=True, pady=8)

        ttk.Label(wrapper, text="Logisitics Coordiator Menu", style="Header.TLabel").pack(pady=(0, 10))

        camp_frame = ttk.LabelFrame(wrapper, text="Camps", padding=10)
        camp_frame.pack(fill="both", expand=True, pady=(0, 8))
        for text, cmd in [
            ("Manage and Create Camps", self.manage_camps_menu),
            ("Manage Food Allocation", self.food_allocation_menu),
            ("Access Financial Settings", self.financial_settings_ui),
        ]:
            ttk.Button(camp_frame, text=text, command=cmd).pack(fill="x", pady=2)

        viz_frame = ttk.LabelFrame(wrapper, text="Insight & Notifications", padding=10)
        viz_frame.pack(fill="both", expand=True, pady=(0, 8))
        for text, cmd in [
            ("View Camp Dashboard", self.dashboard_ui),
            ("Visualise Camp Data", self.visualise_menu),
            ("Access Notifications", self.notifications_ui),
            ("Messaging", self.messaging_ui),
        ]:
            ttk.Button(viz_frame, text=text, command=cmd).pack(fill="x", pady=2)

        ttk.Button(wrapper, text="Logout", command=self.logout).pack(fill="x", pady=2)

    def manage_camps_menu(self):
        top = tk.Toplevel(self)
        top.title("Manage and Create Camps")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=10, style="Card.TFrame")
        frame.pack(fill="both", expand=True)
        ttk.Button(frame, text="Create Camp", command=self.create_camp_ui).pack(fill="x", pady=2)
        ttk.Button(frame, text="Edit Camp", command=self.edit_camp_ui).pack(fill="x", pady=2)
        ttk.Button(frame, text="Delete Camp", command=self.delete_camp_ui).pack(fill="x", pady=2)

    def food_allocation_menu(self):
        top = tk.Toplevel(self)
        top.title("Manage Food Allocation")
        top.configure(bg=THEME_BG)
        frame = ttk.Frame(top, padding=10, style="Card.TFrame")
        frame.pack(fill="both", expand=True)
        ttk.Button(frame, text="Set Daily Food Stock", command=self.set_food_stock_ui).pack(fill="x", pady=2)
        ttk.Button(frame, text="Top-Up Food Stock", command=self.top_up_food_ui).pack(fill="x", pady=2)
        ttk.Button(frame, text="Check Food Shortage", command=self.shortage_ui).pack(fill="x", pady=2)

    def set_food_stock_ui(self):
        camp = self.choose_camp_name()
        if not camp:
            return
        val = simple_prompt_int("New daily stock")
        if val is None:
            return
        res = set_food_stock_data(camp, val)
        messagebox.showinfo("Result", res.get("status"))

    def top_up_food_ui(self):
        camp = self.choose_camp_name()
        if not camp:
            return
        val = simple_prompt_int("Amount to add")
        if val is None:
            return
        res = top_up_food_data(camp, val)
        messagebox.showinfo("Result", res.get("status"))

    def set_pay_rate_ui(self):
        camp = self.choose_camp_name()
        if not camp:
            return
        val = simple_prompt_int("Daily pay rate")
        if val is None:
            return
        res = set_pay_rate_data(camp, val)
        messagebox.showinfo("Result", res.get("status"))

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
        tk.Button(top, text="Food Stock per Camp", command=plot_food_stock).pack(fill="x")
        tk.Button(top, text="Camper Distribution", command=plot_camper_distribution).pack(fill="x")
        tk.Button(top, text="Leaders per Camp", command=plot_leaders_per_camp).pack(fill="x")
        tk.Button(top, text="Engagement Overview", command=plot_engagement_scores).pack(fill="x")

    def financial_settings_ui(self):
        self.set_pay_rate_ui()

    def create_camp_ui(self):
        name = simple_prompt("Camp name:")
        if not name:
            return
        location = simple_prompt("Location:")
        if not location:
            return
        camp_type = simple_prompt_int("Camp type (1=Day, 2=Overnight, 3=Multiple Days)")
        if camp_type not in (1, 2, 3):
            messagebox.showerror("Error", "Camp type must be 1, 2, or 3.")
            return
        start_date = simple_prompt("Start date (YYYY-MM-DD):")
        end_date = simple_prompt("End date (YYYY-MM-DD):")
        for d in (start_date, end_date):
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except Exception:
                messagebox.showerror("Error", "Invalid date format.")
                return
        food_stock = simple_prompt_int("Initial daily food stock:")
        if food_stock is None or food_stock < 0:
            messagebox.showerror("Error", "Food stock must be a non-negative integer.")
            return
        read_from_file()
        Camp(name, location, camp_type, start_date, end_date, food_stock)
        save_to_file()
        messagebox.showinfo("Success", f"Camp {name} created.")

    def edit_camp_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Edit Camp", "No camps exist.")
            return
        camp_names = [c.name for c in camps]
        prompt = "Select camp number to edit:\n" + "\n".join(f"[{i+1}] {name}" for i, name in enumerate(camp_names))
        choice = tk.simpledialog.askinteger("Edit Camp", prompt, minvalue=1, maxvalue=len(camps))
        if choice is None:
            return
        camp = camps[choice - 1]
        new_name = simple_prompt(f"New name (leave blank to keep '{camp.name}'):")
        if new_name:
            camp.name = new_name
        new_loc = simple_prompt(f"New location (leave blank to keep '{camp.location}'):")
        if new_loc:
            camp.location = new_loc
        new_type = simple_prompt("New camp type (1-3, blank to keep):")
        if new_type:
            try:
                ct = int(new_type)
                if ct in (1, 2, 3):
                    camp.camp_type = ct
            except ValueError:
                messagebox.showerror("Error", "Invalid camp type.")
                return
        new_start = simple_prompt(f"New start date (YYYY-MM-DD, blank to keep {camp.start_date}):")
        if new_start:
            try:
                datetime.strptime(new_start, "%Y-%m-%d")
                camp.start_date = new_start
            except Exception:
                messagebox.showerror("Error", "Invalid start date.")
                return
        new_end = simple_prompt(f"New end date (YYYY-MM-DD, blank to keep {camp.end_date}):")
        if new_end:
            try:
                datetime.strptime(new_end, "%Y-%m-%d")
                camp.end_date = new_end
            except Exception:
                messagebox.showerror("Error", "Invalid end date.")
                return
        new_food = simple_prompt("New daily food stock (blank to keep):")
        if new_food:
            try:
                nf = int(new_food)
                if nf < 0:
                    raise ValueError
                camp.food_stock = nf
            except ValueError:
                messagebox.showerror("Error", "Invalid food stock.")
                return
        new_pay = simple_prompt("New daily pay rate (blank to keep):")
        if new_pay:
            try:
                pr = int(new_pay)
                if pr < 0:
                    raise ValueError
                camp.pay_rate = pr
            except ValueError:
                messagebox.showerror("Error", "Invalid pay rate.")
                return
        save_to_file()
        messagebox.showinfo("Success", "Camp updated.")

    def delete_camp_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Delete Camp", "No camps exist.")
            return
        camp_names = [c.name for c in camps]
        prompt = "Select camp number to delete:\n" + "\n".join(f"[{i+1}] {name}" for i, name in enumerate(camp_names))
        choice = tk.simpledialog.askinteger("Delete Camp", prompt, minvalue=1, maxvalue=len(camps))
        if choice is None:
            return
        camp = camps[choice - 1]
        if not messagebox.askyesno("Confirm", f"Delete camp '{camp.name}'?"):
            return
        del camps[choice - 1]
        Camp.all_camps = camps
        save_to_file()
        messagebox.showinfo("Success", f"Camp '{camp.name}' deleted.")
    def messaging_ui(self):
        convo_win = tk.Toplevel(self)
        convo_win.title("Messaging")
        tk.Label(convo_win, text="Conversations").pack()
        listbox = tk.Listbox(convo_win)
        listbox.pack(fill="both", expand=True)
        partners = get_conversations_for_user(self.username)
        for p in partners:
            listbox.insert("end", p)
        tk.Label(convo_win, text="Recipient:").pack()
        recipient_entry = tk.Entry(convo_win)
        recipient_entry.pack()
        tk.Label(convo_win, text="Message:").pack()
        message_entry = tk.Entry(convo_win, width=50)
        message_entry.pack()

        def send():
            to = recipient_entry.get().strip()
            msg = message_entry.get().strip()
            if to and msg:
                send_message(self.username, to, msg)
                messagebox.showinfo("Sent", f"Message sent to {to}")
        tk.Button(convo_win, text="Send", command=send).pack(pady=5)

    def choose_camp_name(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Camps", "No camps exist.")
            return None
        indices = select_camp_dialog("Select a camp", camps, allow_multiple=False)
        if not indices:
            return None
        return camps[indices[0]].name

    def logout(self):
        self.master.destroy()
        launch_login()


class ScoutWindow(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master, padding=16, style="App.TFrame")
        self.username = username
        self.pack(fill="both", expand=True)
        wrapper = ttk.Frame(self, padding=16, style="Card.TFrame", width=720)
        wrapper.pack(expand=True, pady=8)

        ttk.Label(wrapper, text="Scout Leader Menu", style="Header.TLabel").pack(pady=(0, 10))

        actions = ttk.LabelFrame(wrapper, text="Camp Actions", padding=10)
        actions.pack(fill="both", expand=True, pady=(0, 8))
        for text, cmd in [
            ("Select camps to supervise", self.select_camps_ui),
            ("Bulk assign campers from CSV", self.bulk_assign_ui),
            ("Assign food amount per camper per day", self.food_req_ui),
            ("Record daily activity outcomes / incidents", self.record_activity_ui),
        ]:
            ttk.Button(actions, text=text, command=cmd).pack(fill="x", pady=2)

        stats_frame = ttk.LabelFrame(wrapper, text="Insights & Messaging", padding=10)
        stats_frame.pack(fill="both", expand=True)
        for text, cmd in [
            ("View camp statistics and trends", self.stats_ui),
            ("Messaging", self.messaging_ui),
            ("Logout", self.logout),
        ]:
            ttk.Button(stats_frame, text=text, command=cmd).pack(fill="x", pady=2)

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
            messagebox.showerror("Error", "Selected camps overlap in dates. Please choose non-conflicting camps.")
        elif status == "invalid_index":
            messagebox.showerror("Error", "Invalid selection.")
        else:
            messagebox.showerror("Error", status or "Unknown error")

    def bulk_assign_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Bulk Assign", "No camps exist.")
            return
        indices = select_camp_dialog("Select camp for camper import", camps, allow_multiple=False)
        if not indices:
            return
        camp = camps[indices[0]]
        filepath = filedialog.askopenfilename(title="Select campers CSV", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        res = bulk_assign_campers_from_csv(camp.name, filepath)
        status = res.get("status")
        if status == "ok":
            added = res.get("added", [])
            messagebox.showinfo("Success", f"Assigned {len(added)} campers to {camp.name}.")
        elif status == "file_not_found":
            messagebox.showerror("Error", "CSV file not found.")
        elif status == "camp_not_found":
            messagebox.showerror("Error", "Camp not found.")
        elif status == "no_campers":
            messagebox.showinfo("Result", "No campers in CSV.")
        else:
            messagebox.showerror("Error", status or "Unknown error")

    def food_req_ui(self):
        camps = read_from_file()
        if not camps:
            messagebox.showinfo("Food", "No camps exist.")
            return
        indices = select_camp_dialog("Select camp to set food requirement", camps, allow_multiple=False)
        if not indices:
            return
        camp = camps[indices[0]].name
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
        indices = select_camp_dialog("Select camp for activity entry", camps, allow_multiple=False)
        if not indices:
            return
        camp = camps[indices[0]].name
        date = simple_prompt("Date (YYYY-MM-DD)")
        if not date:
            return
        activity_name = simple_prompt("Activity name (optional)") or ""
        activity_time = simple_prompt("Time (optional)") or ""
        notes = simple_prompt("Notes/outcomes/incidents")
        if notes is None:
            return
        food = simple_prompt("Food units used (optional)")
        food_units = int(food) if food and food.isdigit() else None
        res = record_activity_entry_data(camp, date, activity_name, activity_time, notes, food_units)
        status = res.get("status")
        if status == "ok":
            messagebox.showinfo("Success", f"Entry recorded for {camp} on {date}.")
        else:
            messagebox.showerror("Error", status or "Unknown error")

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
        convo_win = tk.Toplevel(self)
        convo_win.title("Messaging")
        tk.Label(convo_win, text="Conversations").pack()
        listbox = tk.Listbox(convo_win)
        listbox.pack(fill="both", expand=True)
        partners = get_conversations_for_user(self.username)
        for p in partners:
            listbox.insert("end", p)
        tk.Label(convo_win, text="Recipient:").pack()
        recipient_entry = tk.Entry(convo_win)
        recipient_entry.pack()
        tk.Label(convo_win, text="Message:").pack()
        message_entry = tk.Entry(convo_win, width=50)
        message_entry.pack()

        def send():
            to = recipient_entry.get().strip()
            msg = message_entry.get().strip()
            if to and msg:
                send_message(self.username, to, msg)
                messagebox.showinfo("Sent", f"Message sent to {to}")
        tk.Button(convo_win, text="Send", command=send).pack(pady=5)

    def logout(self):
        self.master.destroy()
        launch_login()

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
    listbox = tk.Listbox(wrapper, selectmode=selectmode, width=60)
    for camp in camps:
        listbox.insert("end", f"{camp.name} ({camp.location}) {camp.start_date}->{camp.end_date}")
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    result = {"indices": None}

    def on_ok():
        sel = listbox.curselection()
        result["indices"] = list(sel)
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


def init_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    root.configure(bg=THEME_BG)
    style.configure("TFrame", background=THEME_BG, padding=2)
    style.configure("App.TFrame", background=THEME_BG, padding=12)
    style.configure("Card.TFrame", background=THEME_CARD, padding=12)
    style.configure("TLabel", padding=2, background=THEME_CARD, foreground=THEME_FG, font=("Helvetica", 11))
    style.configure("Header.TLabel", font=("Helvetica", 16, "bold"), background=THEME_CARD, foreground=THEME_FG)
    style.configure("TButton", padding=8, background=THEME_ACCENT, foreground=THEME_FG, font=("Helvetica", 11))
    style.map("TButton",
              background=[("active", THEME_ACCENT_ACTIVE), ("pressed", THEME_ACCENT_PRESSED)],
              foreground=[("disabled", "#9ca3af")])
    style.configure("TLabelframe", background=THEME_CARD, foreground=THEME_FG, padding=6)
    style.configure("TLabelframe.Label", background=THEME_CARD, foreground=THEME_FG, font=("Helvetica", 11, "bold"))


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
    root.title("CampTrack Login")
    root.minsize(480, 360)
    init_style(root)
    center_window(root, width=520, height=400)
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    load_logins()
    launch_login()
