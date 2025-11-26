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
                        print(f"{name} already assigned to another camp.")
                        value = True
                        break
                if value is False:
                    if name not in camp.campers:
                        camp.campers.append(name)
            break
    save_to_file()
    print(f"\nAssigned campers to {camp_name}.")


def save_food_requirement(camp_name, food_per_camper):
    try:
        with open(data_path("food_requirements.json"), "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[camp_name] = food_per_camper

    with open(data_path("food_requirements.json"), 'w') as file:
        json.dump(data, file, indent=4)


def assign_food_amount():
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
    save_food_requirement(camp.name, food_per_camper)
    print(f"\nSaved requirement: {food_per_camper} unit(s) per camper per day for {camp.name}.")


def record_daily_activity():
    camps = read_from_file()
    for i, camp in enumerate(camps, start=1):
        print(f"{i} | {camp.name}| {camp.start_date} -> {camp.end_date}")

    choice = get_int("\nSelect a camp to add entry to: ", 1, len(camps))
    camp = camps[choice - 1]

    print(f"\nAdding activities/notes for: {camp.name}")

    while True:

        date_today = datetime.today().date()
        new_date = input("Enter the date (YYYY-MM-DD) or type n to exit: ").strip()
        if new_date.lower() == "n":
            break

        try:
            new_date = datetime.strptime(new_date, "%Y-%m-%d").date()

            if new_date > date_today:
                print("Invalid date. You entered a date in the future.")
            else:
                activity_name = input("Activity name (optional, press enter to skip): ").strip()
                activity_time = input("Time (optional, e.g. 14:00): ").strip()
                notes = input("Enter notes/outcomes/incidents for this entry: ").strip()

                # optional food used for this activity
                food_used = input("Food units used for this activity (optional number): ").strip()
                food_units = None
                if food_used.isdigit():
                    food_units = int(food_used)

                entry = {
                    "activity": activity_name or "unspecified",
                    "time": activity_time,
                    "notes": notes,
                }
                if food_units is not None:
                    entry["food_used"] = food_units

                new_date = str(new_date)
                # store under activities by date
                if new_date not in camp.activities:
                    camp.activities[new_date] = []
                camp.activities[new_date].append(entry)

                # also keep a simple daily record note
                camp.note_daily_record(new_date, notes)

                # track food usage per day if provided
                if food_units is not None:
                    if new_date not in camp.daily_food_usage:
                        camp.daily_food_usage[new_date] = 0
                    camp.daily_food_usage[new_date] += food_units

                save_to_file()

                view_choice = input("Entry added. View today's entries? (y/n): ").strip().lower()
                if view_choice == "y":
                    print(camp.activities.get(new_date, []))
                else:
                    continue
        except ValueError:
            print("Invalid entry. Please try again.")



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

    if not camp.activities:
        print(f"\nNo activities recorded for {camp.name}.")
        return

    total_entries = sum(len(entries) for entries in camp.activities.values())
    print(f"\nActivity summary for {camp.name}:")
    print(f"Total activity entries: {total_entries}")
    for date, entries in sorted(camp.activities.items()):
        print(f"{date}: {len(entries)} activit(ies)")
        for entry in entries:
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

    if camp.daily_food_usage:
        total_food = sum(camp.daily_food_usage.values())
        print(f"\nTotal food used across recorded activities: {total_food} units")


def print_engagement_score():
    from features.logistics import _engagement_score
    read_from_file()

    print("\n--- Existing Camps ---")
    for i, camp in enumerate(Camp.all_camps, start=1):
        print(f"{i}. {camp.name}")

    try:
        choice = int(input("\nEnter the camp number that you want to see the Engagement Score of: "))
        if choice < 1 or choice > len(Camp.all_camps):
            print("Invalid selection of camp.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    camp = Camp.all_camps[choice - 1]
    eng_score = _engagement_score(camp)

    print(f"\nEngagement Score for {camp.name}: {eng_score}")


def info_from_json():
    with open(data_path('camp_data.json'), 'r') as file:
        data = json.load(file)
        for camp in data:
            print(camp)


def money_earned_per_camp():
    read_from_file()
    print("\n--- Existing Camps ---")
    for i, camp in enumerate(Camp.all_camps, start=1):
        print(f"{i}. {camp.name}")
    choice = get_int("\nEnter the camp number that you want to see the money earned of: ", 1, len(Camp.all_camps))
    camp = Camp.all_camps[choice - 1]
    print(f"\nMoney earned by {camp.name}: ${camp.pay_rate * len(camp.campers)}")


def total_money_earned():
    read_from_file()
    total = 0
    for camp in Camp.all_camps:
        total += camp.pay_rate * len(camp.campers)
    print(f"\nTotal money earned: ${total}")


def assign_camp_to_supervise(leader_username):
    while True:
        camps = read_from_file()
        if camps == []:
            print('\nNo camps exist yet. Ask the logistics coordinator to create one.')
            return

        print('\nAvaliable Camps: ')
        n = 0
        for camp in camps:
            n += 1
            print(f"[{n}] {camp.name} | {camp.location} | {camp.start_date} -> {camp.end_date}")

        print("\nCurrent Camp Assignments:")
        view_leader_camp_assignments()

        print("\nSelect the camps you wish to supervise. (Use commas to seperate numbers)")
        selection = input("Input your option(s): ").strip()
        if selection == "":
            print("\nNo camps selected.")
            break

        try:
            chosen_numbers = [int(i) for i in selection.split(',')]
        except ValueError:
            print("\nInvalid input. Please try again.")
            continue

        valid_indices = []
        for n in chosen_numbers:
            if 1 <= n <= len(camps):
                valid_indices.append(n)
            else:
                print(f"Ignoring invalid camp number: {n}")

        if not valid_indices:
            print("\nNo valid camps selected. Try again")
            continue

        selected_camps = [camps[i-1] for i in valid_indices]
        if camps_conflict(selected_camps):
            print("You camps you have selected overlap.\nPlease choose camps that do not overlap.")
            continue

        print(f"{leader_username} has selected these camps to supervise:")
        selected_camp_names = []
        for n in valid_indices:
            camp = camps[n-1]
            selected_camp_names.append(camp.name)
            print(f"{camp.name} | {camp.location} | {camp.start_date} -> {camp.end_date}")

        save_selected_camps(leader_username, selected_camp_names)
        print("\nYour camp selections have been saved")
        break


def bulk_assign_campers():
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

        selected_file = files[file_choice - 1 ]
        filepath = os.path.join(csv_folder, selected_file)

        campers = load_campers_csv(filepath)
        if not campers:
            print("\nCSV contained no campers.")
            continue

        save_campers(selected_camp.name, campers)
        print(f"\nSuccessfully assigned {len(campers)} campers to {selected_camp}!")
        break
