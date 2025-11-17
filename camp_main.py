from datetime import datetime, timedelta
import os
import json

from logistics_coordinator_features import (
    top_up_food,
    set_food_stock,
    check_food_shortage,
    dashboard,
    plot_food_stock,
    set_pay_rate
)

from camp_class import Camp, save_to_file, read_from_file

def get_int(prompt, min_val=None, max_val=None):
    while True:
        user_input = input(prompt)

        if not user_input.isdigit():
            print("Invalid input. Please enter a number.")
            continue

        value = int(user_input)

        if (min_val is not None and value < min_val) or \
           (max_val is not None and value > max_val):
            print("Invalid option. Please choose a valid number.")
            continue

        return value



print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
print('\nWelcome to CampTrack! Please select a user.')

users = {
    'admin': {
        'username': 'admin',
        'password': '',
    },

    'scout leader': [
        {
            'username': 'leader1',
            'password': '',
        }
    ],

    'logistics coordinator': [{
        'username': 'logistics',
        'password': '',
    }]
}


def disabled_logins(username):
    with open('disabled_logins.txt', 'a') as file:
        file.write(username + ',')


def check_disabled_logins(username):
    try:
        with open('disabled_logins.txt', 'r') as file:
            disabled = file.read()
            disabled_usernames = disabled.split(',')
            if username in disabled_usernames:
                return True
    except FileNotFoundError:
        return False


def enable_login(username):
    try:
        with open('disabled_logins.txt', 'r') as file:
            disabled = file.read()
            disabled_usernames = disabled.split(',')

            if username in disabled_usernames:
                disabled_usernames.remove(username)
                
                with open('disabled_logins.txt', 'w') as file:
                    if disabled_usernames:
                        file.write(','.join(disabled_usernames) +',')
                    else:
                        file.write('')

                return True
    except FileNotFoundError:
        return False


def save_logins():
    global users
    with open('logins.txt', 'w') as file:
        file.write(f"admin,{users['admin']['username']},{users['admin']['password']}\n")
        for leader in users['scout leader']:
            file.write(f"scout leader,{leader['username']},{leader['password']}\n")
        for coordinator in users['logistics coordinator']:
            file.write(f"logistics coordinator,{coordinator['username']},{coordinator['password']}\n")


def load_logins():
    global users
    try:
        with open('logins.txt', 'r') as file:
            lines = file.readlines()
            users = {
                'admin': {'username': 'admin', 'password': ''},
                'scout leader': [],
                'logistics coordinator': []
            }
            for line in lines:
                line = line.strip()

                parts = [item.strip() for item in line.split(',')]
                if len(parts) < 3:
                    print(f"Skipping malformed line: {line}")
                    continue

                role, username, password = parts[:3]

                if role == 'admin':
                    users['admin'] = {'username': username, 'password': password}
                elif role == 'scout leader':
                    users['scout leader'].append({'username': username, 'password': password})
                elif role == 'logistics coordinator':
                    users['logistics coordinator'].append({'username': username, 'password': password})

    except FileNotFoundError:
        print('\n logins.txt not found')


load_logins()

# -------------------------------------------------
# ADMIN MENU
# -------------------------------------------------

def admin_menu():
    while True:
        print('\nAdministrator Menu')
        print('\nChoose [1] to View all users'
              '\nChoose [2] to Add a new user'
              "\nChoose [3] to Edit a user's password"
              '\nChoose [4] to Delete a user'
              '\nChoose [5] to Disable a user'
              '\nChoose [6] to Enable a user'
              '\nChoose [7] to Logout')
        choice = get_int("Input your option: ", 1, 7)


        if choice == 1:
            print('\n--- All Users ---')
            for role, role_info in users.items():
                if role == 'admin':
                    print(f"Role: {role}, Username: {role_info['username']}, Password: {role_info['password']}")
                else:
                    for user in role_info:
                        print(f"Role: {role}, Username: {user['username']}, Password: {user['password']}")

        elif choice == 2:
            print('\n---Add New User---')
            print('\nChoose the role you wish to add.')
            while True:
                new_role_option = int(input('\nChoose [1] for Scout Leader'
                                            '\nChoose [2] for Logistics Coordinator'
                                            '\nInput your option: '))
                if new_role_option == 1:
                    new_role = 'scout leader'
                    break
                if new_role_option == 2:
                    new_role = 'logistics coordinator'
                    break
                else:
                    print('Invalid input. Please try again.')

            new_username = input('Enter username: ')
            new_password = input('Enter password: ')

            users[new_role].append({'username': new_username, 'password': new_password})
            print(f"\nUser {new_username} added successfully!")
            save_logins()

        elif choice == 3:
            print("\n---Edit a User's password---")
            while True:
                print('\nChoose [1] to see Admin users'
                      '\nChoose [2] to see Scout Leader users'
                      '\nChoose [3] to see Logistics Coordinator users')

                option = int(input('Input your option: '))

                if option == 1:
                    print(f"Select which user to change password:\n[1] {users['admin']['username']}")
                    option2 = int(input('Input your option: '))
                    if option2 == 1:
                        new_admin_password = str(input(f"Enter a new password for {users['admin']['username']} "))
                        users['admin']['password'] = new_admin_password
                        print("\nPassword updated successfully")
                        save_logins()
                        break
                    else:
                        print('Invalid input. Please try again.')

                if option == 2:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n += 1
                        print(f"\nSelect which user to change password:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)

                    option3 = int(input('\nInput your option: '))
                    if option3 <= len(scout_leader_user_list):
                        chosen_scout_leader = scout_leader_user_list[option3 - 1]
                        print(f"\nThe current password is {chosen_scout_leader['password']}.")
                        new_leader_password = str(input(f"Enter a new password for {chosen_scout_leader['username']}: "))
                        chosen_scout_leader['password'] = new_leader_password
                        print('\nPassword updated successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

                if option == 3:
                    n = 0
                    logistics_coordinator_user_list = []
                    for user in users['logistics coordinator']:
                        n += 1
                        print(f"\nSelect which user to change password:\n[{n}] {user['username']}")
                        logistics_coordinator_user_list.append(user)

                    option4 = int(input('\nInput your option: '))
                    if option4 <= len(logistics_coordinator_user_list):
                        chosen_coordinator = logistics_coordinator_user_list[option4 - 1]
                        print(f"\nThe current password is {chosen_coordinator['password']}.")
                        new_coordinator_password = str(input(f"Enter a new password for {chosen_coordinator['username']}: "))
                        chosen_coordinator['password'] = new_coordinator_password
                        print('\nPassword updated successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

        elif choice == 4:
            print('---Delete a user---')
            while True:
                print('\nChoose [1] to see Scout Leader users'
                      '\nChoose [2] to see Logistics Coordinator users')
                option = int(input('Input your option: '))

                if option == 1:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n += 1
                        print(f"\nSelect which user to delete:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)

                    option5 = int(input('\nInput your option: '))
                    if option5 <= len(scout_leader_user_list):
                        del users['scout leader'][option5 - 1]
                        print('\nUser deleted successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

                if option == 2:
                    n = 0
                    logistics_coordinator_user_list = []
                    for user in users['logistics coordinator']:
                        n += 1
                        print(f"\nSelect which user to delete:\n[{n}] {user['username']}")
                        logistics_coordinator_user_list.append(user)

                    option6 = int(input('\nInput your option: '))
                    if option6 <= len(logistics_coordinator_user_list):
                        del users['logistics coordinator'][option6 - 1]
                        print('\nUser deleted successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

        elif choice == 5:
            while True:
                print('\nChoose [1] to see Scout Leader users'
                      '\nChoose [2] to see Logistics Coordinator users')
                option = int(input('Input your option: '))
                if option == 1:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n += 1
                        print(f"\nSelect which user to disable:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)

                    option5 = int(input('\nInput your option: '))
                    if option5 <= len(scout_leader_user_list):
                        user_to_disable = users['scout leader'][option5 - 1]
                        disabled_logins(user_to_disable['username'])
                        print('\nUser disabled successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

                if option == 2:
                    n = 0
                    logistics_coordinator_user_list = []
                    for user in users['logistics coordinator']:
                        n += 1
                        print(f"\nSelect which user to disable:\n[{n}] {user['username']}")
                        logistics_coordinator_user_list.append(user)

                    option6 = int(input('\nInput your option: '))
                    if option6 <= len(logistics_coordinator_user_list):
                        user_to_disable = users['logistics coordinator'][option6 - 1]
                        disabled_logins(user_to_disable['username'])
                        print('\nUser disabled successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

        elif choice == 6:
            while True:
                disabled_usernames = []
                try:
                    with open('disabled_logins.txt', 'r') as file:
                        disabled_login = file.read().strip(',')
                        if disabled_login != "":
                            disabled_usernames.extend(disabled_login.split(','))
                except FileNotFoundError:
                    pass
            
                if disabled_usernames == []:
                    print("\nThere are no disabled users.")
                    break

                print("\n---Enable a User---")
                n= 0
                for disabled_username in disabled_usernames:
                    n += 1
                    print(f"[{n}] {disabled_username}")
            
                option = int(input("\nInput your option: "))
                if 1 <= option <= len(disabled_usernames):
                    username_to_enable = disabled_usernames[option-1]
                    enable_login(username_to_enable)
                    print(f"\n User '{username_to_enable}' enabled successfully!")
                    break
                else:
                    print('\nInvalid input. Please try again. ')


        elif choice == 7:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
            print('\nWelcome to CampTrack! Please select a user.')
            return

        else:
            print('Invalid input. Please try again.')

# -------------------------------------------------
# LOGISTICS COORDINATOR MENU
# -------------------------------------------------

def logistics_coordinator_menu():
    while True:
        print('\nLogisitics Coordiator Menu')
        print('\nChoose [1] to Manage and Create Camps'
              '\nChoose [2] to Manage Food Allocation'
              "\nChoose [3] to View Camp Dashboard"
              '\nChoose [4] to Visualise Camp Data'
              '\nChoose [5] to Access Financial Settings'
              '\nChoose [6] to Access Notifications'
              '\nChoose [7] to Logout')

        choice = get_int("Input your option: ", 1, 7)

        if choice == 1:
            print('\nCamp Management Menu')
            print('\nChoose [1] to Create a Camp'
                  '\nChoose [2] to Edit Existing Camp'
                  '\nChoose [3] to Return to Main Menu')
            choice = get_int("\nInput your option: ", 1, 3)

            if choice == 1:
                create_camp()
            elif choice == 2:
                edit_camp()
            elif choice == 3:
                logistics_coordinator_menu()
            else:
                print('Invalid input. Please try again.')
                logistics_coordinator_menu()

        elif choice == 2:
            print("\nFood Allocation Menu")
            print("[1] Set Daily Food Stock")
            print("[2] Top-Up Food Stock")
            print("[3] Check Food Shortage")
            print("[4] Return")
            sub = get_int("Choice: ", 1, 4)

            if sub == 1:
                camp = input("Camp name: ")
                new_stock = int(input("New daily stock: "))
                set_food_stock(camp, new_stock)

            elif sub == 2:
                camp = input("Camp name: ")
                amount = int(input("Amount to add: "))
                top_up_food(camp, amount)

            elif sub == 3:
                camp = input("Camp name: ")
                needed = int(input("Required amount: "))
                check_food_shortage(camp, needed)

            else:
                continue

        elif choice == 3:
            dashboard()

        elif choice == 4:
            plot_food_stock()

        elif choice == 5:
            camp = input("Camp name: ")
            rate = int(input("Daily pay rate: "))
            set_pay_rate(camp, rate)

        elif choice == 6:
            try:
                with open("notifications.json", "r") as f:
                    notes = json.load(f)
                print("\n--- Notifications ---")
                for n in notes:
                    print("-", n)
            except:
                print("No notifications found.")

        elif choice == 7:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
            print('\nWelcome to CampTrack! Please select a user.')
            return

        else:
            print('Invalid input. Please try again.')
            logistics_coordinator_menu()

# -------------------------------------------------
# LOGIN FUNCTIONS
# -------------------------------------------------

def login_admin():
    login = True
    while login:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        user = users['admin']
        if check_disabled_logins(ask_username):
            print("This account has been disabled.")
            return
        if user['username'] == ask_username and user['password'] == ask_password:
            print('\nLogin successful! Welcome Application Administrator.\n')
            login = False
            admin_menu()
        else:
            print('\nInvalid username or password.\n')


def login_scoutleader():
    login = True
    while login:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        if check_disabled_logins(ask_username):
            print("This account has been disabled.")
            return
        for user in users['scout leader']:
            if user['username'] == ask_username and user['password'] == ask_password:
                print('\nLogin successful! Welcome Scout Leader.\n')
                login = False
                scout_leader_menu(ask_username)
            else:
                print('\nInvalid username or password.\n')


def login_logisticscoordinator():
    login = True
    while login:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        if check_disabled_logins(ask_username):
            print("This account has been disabled.")
            return
        for user in users['logistics coordinator']:
            if user['username'] == ask_username and user['password'] == ask_password:
                print('\nLogin successful! Welcome Logistics Coordinator.\n')
                login = False
                logistics_coordinator_menu()
            else:
                print('\nInvalid username or password.\n')


# -------------------------------------------------
# CAMP CREATION
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

    # Helper function for text fields
    def update_text(prompt, current_value):
        value = input(f"{prompt} [{current_value}]: ").strip()
        if value.lower() in ("", "same"):
            return current_value
        return value

    # Helper function for numeric fields
    def update_number(prompt, current_value):
        value = input(f"{prompt} [{current_value}]: ").strip()
        if value.lower() in ("", "same"):
            return current_value
        if value.isdigit():
            return int(value)
        print("Invalid number. Keeping current value.")
        return current_value

    # Update values
    camp.name = update_text("New Name", camp.name)
    camp.location = update_text("New Location", camp.location)
    camp.camp_type = update_text("New Type", camp.camp_type)
    camp.start_date = update_text("New Start Date", camp.start_date)
    camp.end_date = update_text("New End Date", camp.end_date)
    camp.food_stock = update_number("New Daily Food Stock", camp.food_stock)
    camp.pay_rate = update_number("New Pay Rate", camp.pay_rate)

    save_to_file()
    print("\nCamp updated successfully!")


def create_camp():
    print('\nCamp Creator')

    name = input('\nPlease enter the name of this camp: ')
    location = input('\nPlease enter the location of this camp: ')

    print('\nPlease enter the camp type:'
          '\nSelect [1] for Day Camp'
          '\nSelect [2] for Overnight'
          '\nSelect [3] for Multiple Days')
    camp_type = choice = get_int("Input your option: ", 1, 3)
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
                if nights < 1:
                    print("A multi-day camp must be at least 1 night.")
                    continue
                second_date = first_date + timedelta(days=nights)
                valid = True
        except ValueError:
            print('Invalid date format! Please use YYYY-MM-DD.')
            start_date = input('\nPlease enter the start date (YYYY-MM-DD): ')

    start_date = first_date.strftime("%Y-%m-%d")
    end_date = second_date.strftime("%Y-%m-%d")

    initial_food_stock = int(input('\nPlease enter the amount of food allocated for this camp [units]: '))

    print("\nYour Camp Details:")
    print("Name:", name)
    print("Location:", location)
    print("Type:", camp_type)
    print("Start Date:", start_date)
    print("End Date:", end_date)
    print("Daily Food Stock:", initial_food_stock)

    confirm = input("\nConfirm camp creation? (Y/N): ").strip().lower()

    if confirm == 'y':
        Camp(
            name,
            location,
            camp_type,
            start_date,
            end_date,
            initial_food_stock
        )
        save_to_file()
        print("\nCamp successfully created!")
    else:
        print("\nCamp creation cancelled.")

    logistics_coordinator_menu()


# -------------------------------------------------
# SCOUT LEADER MENU
# -------------------------------------------------

def save_selected_camps(leader_username, selected_camp_names):
    try:
        with open('leader_camps.txt', 'r') as file:
            lines = file.read().splitlines()
    except FileNotFoundError:
        return False
    
    new_lines = []
    for line in lines:
        if line.startswith(leader_username + ',') == False:
            new_lines.append(line)

    for camp_name in selected_camp_names:
        new_lines.append(f"{leader_username},{camp_name}") 

    with open('leader_camps.txt', 'w') as file:
        for line in new_lines:
            file.write(line + '\n')   

def view_leader_camp_assignments():
    try:
        with open('leader_camps.txt','r') as file:
            lines = file.read().splitlines()
    except FileNotFoundError:
        return False
    
    if len(lines) == 0:
        print('\nNo leader has been assigned camps yet')
        return
    
    print("\nLeaders and their camps:")
    for line in lines:
        parts = line.split(',')
        if len(parts) < 2:
            continue

        leader_username = parts[0].strip()
        camp_name = parts[1].strip()

        print(f"{leader_username} is supervising {camp_name}")
    
    def camps_overlap(camp1, camp2):
        pass


def scout_leader_menu(leader_username):
    while True:
        print('\nScout Leader Menu')
        print('\nChoose [1] to Select camps to supervise'
              '\nChoose [2] to Bulk assign campers from CSV'
              '\nChoose [3] to Assign food amount per camper per day'
              '\nChoose [4] to Record daily activity outcomes / incidents'
              '\nChoose [5] to View camp statistics and trends'
              '\nChoose [6] to Logout')
        choice = get_int('Input your option: ', 1, 6)

        if choice == 1:
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
                    
                if valid_indices == False:
                    print("\nNo valid camps selected. Try again")
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
                    
            
        
        elif choice == 2:
            # TODO
            print('\n[NOT IMPLENENTED YET]')

        elif choice == 3 :
             # TODO
            print('\n[NOT IMPLENENTED YET]')

        elif choice == 4:
            # TODO
            print('\n[NOT IMPLENENTED YET]')

        elif choice == 5:
            # TODO
            print('\n[NOT IMPLENENTED YET]')

        elif choice == 6:
            break           



    


# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
while True:
    option = get_int(
        "\nChoose [1] for Application Administrator\n"
        "Choose [2] for Scout Leader\n"
        "Choose [3] for Logistics Coordinator\n\n"
        "Input your option: ",
        1, 3
    )

    if option == 1:
        login_admin()
    elif option == 2:
        login_scoutleader()
    elif option == 3:
        login_logisticscoordinator()