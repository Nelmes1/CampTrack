import os
import json
import csv
from datetime import datetime

from camp_class import Camp, save_to_file, read_from_file
from utils import get_int, data_path


def camps_overlap(camp1, camp2):
    s1 = datetime.strptime(camp1.start_date, "%Y-%m-%d")
    e1 = datetime.strptime(camp1.end_date, "%Y-%m-%d")
    s2 = datetime.strptime(camp2.start_date, "%Y-%m-%d")
    e2 = datetime.strptime(camp2.end_date, "%Y-%m-%d")
    return not (s1 > e2 or s2 > e1)


def camps_conflict(selected_camps):
    for camp_a in selected_camps:
        for camp_b in selected_camps:
            if camp_a is camp_b:
                continue
            if camps_overlap(camp_a, camp_b):
                return True
    return False


def save_selected_camps(leader_username, selected_camp_names):
    camps = read_from_file()
    for camp in camps:
        if camp.name in selected_camp_names:
            camp.assign_leader(leader_username)
        else:
            if leader_username in camp.scout_leaders:
                camp.scout_leaders.remove(leader_username)
    save_to_file()


def view_leader_camp_assignments():
    camps = read_from_file()
    if not camps:
        print("\nNo camps exist yet.")
        return

    value = False
    for camp in camps:
        if camp.scout_leaders:
            value = True
            print(f"{camp.name}: {', '.join(camp.scout_leaders)}")

    if value is False:
        print("\nNo leader has been assigned camps yet")


def load_campers_csv(filepath):
    campers = {}
    try:
        with open(filepath) as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row["Name"].strip()
                age = row["Age"].strip()
                activities = row["Activities"].split(';')
                campers[name] = {
                    "age": age,
                    "activities": [a.strip() for a in activities]
                }
    except FileNotFoundError:
        print("\nCSV file not found.")
    return campers


def save_campers(camp_name, campers):
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            for name in campers.keys():
                value = False
                for other_camp in camps:
                    if other_camp.name != camp_name and name in other_camp.campers:
                        # camper already assigned elsewhere
                        value = True
                        break
                if value is False:
                    if name not in camp.campers:
                        camp.campers.append(name)
            break
    save_to_file()
    return {"status": "ok", "camp": camp_name, "added": list(campers.keys())}


def find_camp_by_name(camp_name):
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            return camp
    return None


def bulk_assign_campers_data(selected_camp, campers):
    """Assign campers dict to the given Camp instance; returns status dict."""
    if selected_camp is None:
        return {"status": "no_camp"}
    # prevent duplicates across camps
    camps = read_from_file()
    for name in list(campers.keys()):
        for other_camp in camps:
            if other_camp.name != selected_camp.name and name in other_camp.campers:
                # remove camper already assigned elsewhere
                campers.pop(name, None)
                break
    return save_campers(selected_camp.name, campers)


def bulk_assign_campers_from_csv(camp_name, filepath):
    """Pure helper: assign campers from a CSV to a named camp."""
    if not os.path.exists(filepath):
        return {"status": "file_not_found"}
    selected_camp = find_camp_by_name(camp_name)
    if selected_camp is None:
        return {"status": "camp_not_found"}
    campers = load_campers_csv(filepath)
    if not campers:
        return {"status": "no_campers"}
    return bulk_assign_campers_data(selected_camp, campers)


def assign_camps_to_leader(camps, leader_username, selected_indices):
    """Pure helper to assign a leader to selected camps and remove from others."""
    if not selected_indices:
        return {"status": "no_selection"}
    selected_camp_names = []
    for idx in selected_indices:
        if idx < 0 or idx >= len(camps):
            return {"status": "invalid_index"}
        selected_camp_names.append(camps[idx].name)
    # check conflicts
    selected_camps = [camps[i] for i in selected_indices]
    if camps_conflict(selected_camps):
        return {"status": "overlap"}
    # apply assignments
    for camp in camps:
        if camp.name in selected_camp_names:
            camp.assign_leader(leader_username)
        else:
            if leader_username in camp.scout_leaders:
                camp.scout_leaders.remove(leader_username)
    save_to_file()
    return {"status": "ok", "selected": selected_camp_names}


def assign_camps_to_leader_ui(leader_username):
    camps = read_from_file()
    if not camps:
        print('\nNo camps exist yet. Ask the logistics coordinator to create one.')
        return

    print('\nAvaliable Camps: ')
    for idx, camp in enumerate(camps, start=1):
        print(f"[{idx}] {camp.name} | {camp.location} | {camp.start_date} -> {camp.end_date}")

    print("\nCurrent Camp Assignments:")
    view_leader_camp_assignments()

    print("\nSelect the camps you wish to supervise. (Use commas to seperate numbers)")
    selection = input("Input your option(s): ").strip()
    if selection == "":
        print("\nNo camps selected.")
        return

    try:
        chosen_numbers = [int(i) for i in selection.split(',')]
    except ValueError:
        print("\nInvalid input. Please try again.")
        return

    valid_indices = []
    for n in chosen_numbers:
        if 1 <= n <= len(camps):
            valid_indices.append(n - 1)
        else:
            print(f"Ignoring invalid camp number: {n}")

    res = assign_camps_to_leader(camps, leader_username, valid_indices)
    if res["status"] == "no_selection":
        print("\nNo valid camps selected. Try again")
    elif res["status"] == "invalid_index":
        print("\nInvalid camp selection.")
    elif res["status"] == "overlap":
        print("You camps you have selected overlap.\nPlease choose camps that do not overlap.")
    elif res["status"] == "ok":
        print(f"{leader_username} has selected these camps to supervise:")
        for name in res["selected"]:
            print(name)
        print("\nYour camp selections have been saved")


def save_food_requirement(camp_name, food_per_camper):
    try:
        with open(data_path("food_requirements.json"), "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[camp_name] = food_per_camper

    with open(data_path("food_requirements.json"), 'w') as file:
        json.dump(data, file, indent=4)
    return {"status": "ok", "camp": camp_name, "food_per_camper": food_per_camper}


def assign_food_amount():
    """UI wrapper to assign food per camper for a camp."""
    camps = read_from_file()
    if not camps:
        print("\nNo camps exist yet. Ask the logistics coordinator to create one.")
        return

    print('\nAvailable Camps: ')
    for idx, camp in enumerate(camps, start=1):
        print(f"[{idx}] {camp.name} | {camp.location} | {camp.start_date} -> {camp.end_date} | Campers: {len(camp.campers)}")

    choice = get_int("\nSelect a camp to assign food per camper: ", 1, len(camps))
    camp = camps[choice - 1]

    camper_count = len(camp.campers)
    if camper_count == 0:
        print(f"\n{camp.name} has no campers assigned yet. Add campers before assigning food per camper.")
        return
    print(f"\n{camp.name} has {camper_count} campers assigned.")

    food_per_camper = get_int("Enter daily food units per camper: ", min_val=0)
    res = assign_food_amount_data(camp, food_per_camper)
    if res.get("status") == "ok":
        print(f"\nSaved requirement: {food_per_camper} unit(s) per camper per day for {camp.name}.")


def assign_food_amount_data(camp, food_per_camper):
    """Pure helper to save food requirement for a camp."""
    if camp is None:
        return {"status": "no_camp"}
    return save_food_requirement(camp.name, food_per_camper)


def assign_food_amount_pure(camp_name, food_per_camper):
    camp = find_camp_by_name(camp_name)
    return assign_food_amount_data(camp, food_per_camper)


def record_daily_activity_data(camp, date, activity_name, activity_time, notes, food_units=None):
    """Pure helper to add an activity entry to a camp; returns status and entry."""
    if camp is None:
        return {"status": "no_camp"}
    entry = add_activity_entry(camp, date, activity_name, activity_time, notes, food_units)
    return {"status": "ok", "entry": entry}


def record_activity_entry_data(camp_name, date, activity_name, activity_time, notes, food_units=None):
    camp = find_camp_by_name(camp_name)
    if camp is None:
        return {"status": "camp_not_found"}
    return record_daily_activity_data(camp, date, activity_name, activity_time, notes, food_units)


def record_daily_activity():
    camps = read_from_file()
    for i, camp in enumerate(camps, start=1):
        print(f"{i} | {camp.name}| {camp.start_date} -> {camp.end_date}")

    choice = get_int("\nSelect a camp to add entry to: ", 1, len(camps))
    camp = camps[choice - 1]

    print(f"\nAdding activities/notes for: {camp.name}")

    while True:
        new_date = input("Enter the date (YYYY-MM-DD) or type n to exit: ").strip()
        if new_date.lower() == "n":
            break

        activity_name = input("Activity name (optional, press enter to skip): ").strip()
        activity_time = input("Time (optional, e.g. 14:00): ").strip()
        notes = input("Enter notes/outcomes/incidents for this entry: ").strip()

        # optional food used for this activity
        food_used = input("Food units used for this activity (optional number): ").strip()
        food_units = None
        if food_used.isdigit():
            food_units = int(food_used)

        record_daily_activity_data(camp, new_date, activity_name, activity_time, notes, food_units)

        view_choice = input("Entry added. View today's entries? (y/n): ").strip().lower()
        if view_choice == "y":
            print(camp.activities.get(new_date, []))
        else:
            continue


def add_activity_entry(camp, date, activity_name, activity_time, notes, food_units=None):
    """Pure helper to add an activity entry to a camp."""
    entry = {
        "activity": activity_name or "unspecified",
        "time": activity_time,
        "notes": notes,
    }
    if food_units is not None:
        entry["food_used"] = food_units

    if date not in camp.activities:
        camp.activities[date] = []
    camp.activities[date].append(entry)

    camp.note_daily_record(date, notes)

    if food_units is not None:
        if date not in camp.daily_food_usage:
            camp.daily_food_usage[date] = 0
        camp.daily_food_usage[date] += food_units
    save_to_file()
    return entry


def view_activity_stats():
    camps = read_from_file()
    if not camps:
        print("\nNo camps exist yet.")
        return

    print("\n--- Existing Camps ---")
    for i, camp in enumerate(camps, start=1):
        print(f"{i}. {camp.name}")
    choice = get_int("\nSelect a camp to view activity stats: ", 1, len(camps))
    camp = camps[choice - 1]

    stats = activity_stats_data(camp)
    if stats["status"] != "ok":
        print(f"\nNo activities recorded for {camp.name}.")
        return

    print(f"\nActivity summary for {camp.name}:")
    print(f"Total activity entries: {stats['total_entries']}")
    for date_info in stats["per_date"]:
        print(f"{date_info['date']}: {date_info['count']} activit(ies)")
        for entry in date_info["entries"]:
            desc = entry.get('activity', 'unspecified')
            time = entry.get('time')
            notes = entry.get('notes', '')
            food = entry.get('food_used')
            extra = []
            if time:
                extra.append(f"@ {time}")
            if food is not None:
                extra.append(f"food used: {food}")
            extra_txt = f" ({', '.join(extra)})" if extra else ""
            print(f"  - {desc}{extra_txt}: {notes}")

    if stats["total_food_used"] is not None:
        print(f"\nTotal food used across recorded activities: {stats['total_food_used']} units")


def print_engagement_score():
    scores = engagement_scores_data()
    if not scores:
        print("\nNo camps found.")
        return
    print("\n--- Existing Camps ---")
    for i, (name, score) in enumerate(scores, start=1):
        print(f"{i}. {name} (Engagement: {score})")


def info_from_json():
    with open(data_path('camp_data.json'), 'r') as file:
        data = json.load(file)
        for camp in data:
            print(camp)


def money_earned_per_camp():
    data = money_earned_per_camp_data()
    if not data:
        print("\nNo camps found.")
        return
    print("\n--- Money Earned Per Camp ---")
    for name, earned in data:
        print(f"{name}: ${earned}")


def total_money_earned():
    total = total_money_earned_value()
    print(f"\nTotal money earned: ${total}")


# UI wrappers (print) for stats, calling data helpers
def show_engagement_scores():
    scores = engagement_scores_data()
    if not scores:
        print("\nNo camps found.")
        return
    print("\n--- Existing Camps ---")
    for i, (name, score) in enumerate(scores, start=1):
        print(f"{i}. {name} (Engagement: {score})")


def show_money_per_camp():
    money_earned_per_camp()


def show_total_money():
    total_money_earned()


def engagement_scores_data():
    read_from_file()
    return [(camp.name, _engagement_score(camp)) for camp in Camp.all_camps]


def money_earned_per_camp_data():
    read_from_file()
    return [(camp.name, camp.pay_rate * len(camp.campers)) for camp in Camp.all_camps]


def total_money_earned_value():
    read_from_file()
    return sum(camp.pay_rate * len(camp.campers) for camp in Camp.all_camps)


def activity_stats_data(camp):
    if not camp.activities:
        return {"status": "no_activities"}
    per_date = []
    for date, entries in sorted(camp.activities.items()):
        per_date.append({
            "date": date,
            "count": len(entries),
            "entries": entries,
        })
    total_entries = sum(item["count"] for item in per_date)
    total_food = sum(camp.daily_food_usage.values()) if camp.daily_food_usage else None
    return {
        "status": "ok",
        "total_entries": total_entries,
        "per_date": per_date,
        "total_food_used": total_food,
    }


def bulk_assign_campers():
    """UI flow for bulk assigning campers from CSV."""
    while True:
        camps = read_from_file()
        if camps == []:
            print('\nNo camps exist yet. Ask the logistics coordinator to create one.')
            break
        print('\nAvaliable Camps: ')
        n = 0
        for camp in camps:
            n += 1
            print(f"[{n}] {camp.name} | {camp.location} | {camp.start_date} -> {camp.end_date}")

        print("\nSelect a camp to assign campers to: ")

        try:
            choice= int(input("Input your option: "))
            if not (1 <= choice <= len(camps)):
                print("\nNo camps selected.")
                continue
        except ValueError:
            print("Invalid input. Please try again")
            continue

        selected_camp = camps[choice - 1]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_folder = os.path.join(os.path.dirname(base_dir), "campers")

        if not os.path.exists(csv_folder):
            print("\nCSV folder not found. Create a 'campers' folder in the project root and add CSV files before bulk assigning.")
            break
        files = []
        for f in os.listdir(csv_folder):
            if f.endswith(".csv"):
                files.append(f)
        if not files:
            print("\nNo CSV files found in campers.")
            break

        print("\nAvaliable CSV Files:")
        n = 0
        for f in files:
            n+=1
            print(f"[{n}] {f}")

        try:
            file_choice = int(input("\nSelect a CSV file to import: "))
            if not (1<= file_choice <= len(files)):
                print("Invalid output. Please try again.")
                continue
        except ValueError:
            print("Invalid output. Please try again.")
            continue

        selected_file = files[file_choice - 1]
        filepath = os.path.join(csv_folder, selected_file)

        campers = load_campers_csv(filepath)
        if not campers:
            print("\nCSV contained no campers.")
            continue

        res = bulk_assign_campers_data(selected_camp, campers)
        if res and res.get("status") == "ok":
            print(f"\nSuccessfully assigned {len(campers)} campers to {selected_camp.name}!")
        else:
            print("\nNo campers were assigned.")
        break


# UI helpers for stats
def show_engagement_scores():
    scores = engagement_scores_data()
    if not scores:
        print("\nNo camps found.")
        return
    print("\n--- Existing Camps ---")
    for i, (name, score) in enumerate(scores, start=1):
        print(f"{i}. {name} (Engagement: {score})")


def show_money_per_camp():
    data = money_earned_per_camp_data()
    if not data:
        print("\nNo camps found.")
        return
    print("\n--- Money Earned Per Camp ---")
    for name, earned in data:
        print(f"{name}: ${earned}")


def show_total_money():
    total = total_money_earned_value()
    print(f"\nTotal money earned: ${total}")


def bulk_assign_campers_ui(leader_username):
    """Alias to keep menu clear; uses bulk_assign_campers for prompts."""
    return bulk_assign_campers()
