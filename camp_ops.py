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

    choice = get_int("\nSelect a camp to edit: ", 1, len(camps))
    camp = camps[choice - 1]

    print(f"\nEditing Camp: {camp.name}")
    print("Press ENTER or type 'same' to keep the current value.\n")

    def update_text(prompt, current_value):
        value = input(f"{prompt} [{current_value}]: ").strip()
        if value.lower() in ("", "same"):
            return current_value
        return value

    def update_number(prompt, current_value):
        value = input(f"{prompt} [{current_value}]: ").strip()
        if value.lower() in ("", "same"):
            return current_value
        if value.isdigit():
            return int(value)
        print("Invalid number. Keeping current value.")
        return current_value

    camp.name = update_text("New Name", camp.name)
    camp.location = update_text("New Location", camp.location)
    camp.camp_type = get_int(update_text('Please enter the new camp type:'
          '\nSelect [1] for Day Camp'
          '\nSelect [2] for Overnight'
          '\nSelect [3] for Multiple Days', camp.camp_type) )
    date_change = input("Update dates? (y/n): ").strip().lower()
    if date_change == ("y"):
        new_start, new_end = get_dates(camp.camp_type)
        camp.start_date = new_start
        camp.end_date = new_end
    camp.food_stock = update_number("New Daily Food Stock", camp.food_stock)
    camp.pay_rate = update_number("New Pay Rate", camp.pay_rate)

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

    choice = get_int("\nSelect a camp to delete: ", 1, len(camps))
    camp = camps[choice - 1]

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

    name = input('\nPlease enter the name of this camp: ')
    location = input('\nPlease enter the location of this camp: ')

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
                nights = int(input("\nHow many nights is the camp? "))
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
