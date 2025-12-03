from datetime import datetime, timedelta

from camp_class import Camp, save_to_file, read_from_file
from utils import get_int


# -------------------------------------------------
# CAMP CREATION / EDIT / DELETE
# -------------------------------------------------
def edit_camp():
    camps = read_from_file()

    if not camps:
        print("\nNo camps exist. Create one first.")
        return

    print("\n--- Existing Camps ---")
    for i, camp in enumerate(camps, start=1):
        print(f"[{i}] {camp.name} ({camp.location})")

    sel = input("\nSelect a camp to edit (or press Enter to cancel): ").strip()
    if sel == "":
        print("Edit cancelled.")
        return
    if not sel.isdigit():
        print("Invalid selection.")
        return
    idx = int(sel)
    if not (1 <= idx <= len(camps)):
        print("Invalid selection.")
        return
    camp = camps[idx - 1]

    print(f"\nEditing Camp: {camp.name}")
    print("Press ENTER or type 'same' to keep the current value.\n")
    print("Leave fields blank to keep current values; type 'q' to cancel editing.")

    def update_text(prompt, current_value):
        value = input(f"{prompt} [{current_value}]: ").strip()
        if value.lower() == "q":
            return None
        if value.lower() in ("", "same"):
            return current_value
        return value

    def update_number(prompt, current_value):
        value = input(f"{prompt} [{current_value}]: ").strip()
        if value.lower() == "q":
            return None
        if value.lower() in ("", "same"):
            return current_value
        if value.isdigit():
            return int(value)
        print("Invalid number. Keeping current value.")
        return current_value

    new_name = update_text("New Name", camp.name)
    if new_name is None:
        print("Edit cancelled.")
        return
    camp.name = new_name

    new_loc = update_text("New Location", camp.location)
    if new_loc is None:
        print("Edit cancelled.")
        return
    camp.location = new_loc

    new_type_raw = update_text('Please enter the new camp type:'
          '\nSelect [1] for Day Camp'
          '\nSelect [2] for Overnight'
          '\nSelect [3] for Multiple Days', camp.camp_type)
    if new_type_raw is None:
        print("Edit cancelled.")
        return
    camp.camp_type = get_int(str(new_type_raw), 1, 3)

    date_change = input("Update dates? (y/n): ").strip().lower()
    if date_change == ("y"):
        new_start, new_end = get_dates(camp.camp_type)
        camp.start_date = new_start
        camp.end_date = new_end
    new_food = update_number("New Daily Food Stock", camp.food_stock)
    if new_food is None:
        print("Edit cancelled.")
        return
    camp.food_stock = new_food
    new_pay = update_number("New Pay Rate", camp.pay_rate)
    if new_pay is None:
        print("Edit cancelled.")
        return
    camp.pay_rate = new_pay

    save_to_file()
    print("\nCamp updated successfully!")


def delete_camp():
    camps = read_from_file()

    if not camps:
        print("\nNo camps exist. Create one first.")
        return

    print("\n--- Existing Camps ---")
    for i, camp in enumerate(camps, start=1):
        print(f"[{i}] {camp.name} ({camp.location})")

    sel = input("\nSelect a camp to delete (or press Enter to cancel): ").strip()
    if sel == "":
        print("Deletion cancelled.")
        return
    if not sel.isdigit() or not (1 <= int(sel) <= len(camps)):
        print("Invalid selection.")
        return
    camp = camps[int(sel) - 1]

    confirm = input(f"\nAre you sure you want to delete '{camp.name}'? (Y/N): ").strip().lower()
    if confirm != "y":
        print("\nDeletion cancelled.")
        return

    del camps[choice - 1]
    Camp.all_camps = camps

    save_to_file()
    print("\nCamp deleted successfully!")


def create_camp():
    print('\nCamp Creator')
    print('(Leave name/location blank to cancel.)')

    name = input('\nPlease enter the name of this camp: ')
    if name.strip() == "":
        print("Camp creation cancelled (blank name).")
        return
    location = input('\nPlease enter the location of this camp: ')
    if location.strip() == "":
        print("Camp creation cancelled (blank location).")
        return

    print('\nPlease enter the camp type:'
          '\nSelect [1] for Day Camp'
          '\nSelect [2] for Overnight'
          '\nSelect [3] for Multiple Days')
    camp_type = choice = get_int("Input your option: ", 1, 3)
    start_date, end_date = get_dates(camp_type)

    while True:
        try:
            initial_food_stock = int(input('\nPlease enter the amount of food allocated for this camp [units]: '))
            break
        except ValueError:
            print("Please enter a valid whole number!")

    print("\nYour Camp Details:")
    print("Name:", name)
    print("Location:", location)
    print("Type:", camp_type)
    print("Start Date:", start_date)
    print("End Date:", end_date)
    print("Daily Food Stock:", initial_food_stock)

    while True:
        confirm = input("\nConfirm camp creation? (Y/N): ").strip().lower()
        if confirm in ('y', 'n'):
            break
        print("Please enter Y or N.")

    if confirm == 'y':
        Camp(
            name,
            location,
            camp_type,
            start_date,
            end_date,
            initial_food_stock,

        )
        save_to_file()
        print("\nCamp successfully created!")
    else:
        print("\nCamp creation cancelled.")

    return


def get_dates(camp_type):
    start_date = input('\nPlease enter the start date (YYYY-MM-DD): ')

    valid = False
    while not valid:
        try:
            first_date = datetime.strptime(start_date, "%Y-%m-%d")
            if camp_type == 1:
                nights = 0
                second_date = first_date + timedelta(days=nights)
                valid = True
            elif camp_type == 2:
                nights = 1
                second_date = first_date + timedelta(days=nights)
                valid = True
            elif camp_type == 3:
                nights = get_int("\nHow many nights is the camp? ")
                if nights < 2:
                    print("A multi-day camp must be at least 2 nights.")
                    continue
                second_date = first_date + timedelta(days=nights)
                valid = True
        except ValueError:
            print('Invalid date format! Please use YYYY-MM-DD.')
            start_date = input('\nPlease enter the start date (YYYY-MM-DD): ')

    start_date = first_date.strftime("%Y-%m-%d")
    end_date = second_date.strftime("%Y-%m-%d")

    return start_date, end_date
