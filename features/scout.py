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

    food_per_camper = get_int("Enter daily food units per camper: ", min_val=0)
    save_food_requirement(camp.name, food_per_camper)
    print(f"\nSaved requirement: {food_per_camper} unit(s) per camper per day for {camp.name}.")


def record_daily_activity():
    camps = read_from_file()
    for i, camp in enumerate(camps, start=1):
        print(f"{i} | {camp.name}| {camp.start_date} -> {camp.end_date}")

    choice = get_int("\nSelect a camp to add entry to: ", 1, len(camps))
    camp = camps[choice - 1]

    print(f"\nAdding the daily entry to: {camp.name}")

    while True:
        new_date = input("Enter the date(or type n to exit):")
        if new_date.lower() == "n":
            break

        new_note = input("Enter the diary entry for today")

        camp.note_daily_record(new_date, new_note)
        save_to_file()

        view_choice = input("Your entry has been added. Would you like to view it? Type 'y' or 'n': ")
        if view_choice.lower() == "y":
            print(camp.daily_records)
        else:
            break


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
            continue

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
            print("\nCSV folder not found")
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
