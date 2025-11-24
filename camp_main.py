import os
import json
import csv
from datetime import datetime
from messaging import messaging_menu


from logistics_coordinator_features import (
    top_up_food,
    set_food_stock,
    check_food_shortage,
    dashboard,
    plot_food_stock,
    plot_camper_distribution,
    plot_leaders_per_camp,
    plot_engagement_scores,
    set_pay_rate,
    get_dates,
    delete_camp,
    edit_camp,
    create_camp,
)

from camp_class import Camp, save_to_file, read_from_file

from utils import get_int

from scout_leader import(
    selecting_camp_to_supervise,
    bulk_assign_campers,
    assign_food_amount,
    record_daily_activity,
    print_engagement_score,
    info_from_json,
    money_earned_per_camp,
    total_money_earned,
)


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
                new_role_option = get_int('\nChoose [1] for Scout Leader'
                                          '\nChoose [2] for Logistics Coordinator'
                                          '\nInput your option: ', 1, 2)
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

                option = get_int('Input your option: ', 1, 3)

                if option == 1:
                    print(f"Select which user to change password:\n[1] {users['admin']['username']}")
                    option2 = get_int('Input your option: ', 1, 1)
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

                    if not scout_leader_user_list:
                        print('\nNo scout leader users found.')
                        continue

                    option3 = get_int('\nInput your option: ', 1, len(scout_leader_user_list))
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

                    if not logistics_coordinator_user_list:
                        print('\nNo logistics coordinator users found.')
                        continue

                    option4 = get_int('\nInput your option: ', 1, len(logistics_coordinator_user_list))
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
                option = get_int('Input your option: ', 1, 2)

                if option == 1:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n += 1
                        print(f"\nSelect which user to delete:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)

                    if not scout_leader_user_list:
                        print('\nNo scout leader users found.')
                        continue

                    option5 = get_int('\nInput your option: ', 1, len(scout_leader_user_list))
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

                    if not logistics_coordinator_user_list:
                        print('\nNo logistics coordinator users found.')
                        continue

                    option6 = get_int('\nInput your option: ', 1, len(logistics_coordinator_user_list))
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
                option = get_int('Input your option: ', 1, 2)
                if option == 1:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n += 1
                        print(f"\nSelect which user to disable:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)

                    if not scout_leader_user_list:
                        print('\nNo scout leader users found.')
                        continue

                    option5 = get_int('\nInput your option: ', 1, len(scout_leader_user_list))
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

                    if not logistics_coordinator_user_list:
                        print('\nNo logistics coordinator users found.')
                        continue

                    option6 = get_int('\nInput your option: ', 1, len(logistics_coordinator_user_list))
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
              '\nChoose [7] to Messaging'
              '\nChoose [8] to Logout')

        choice = get_int("Input your option: ", 1, 8)

        if choice == 1:
            print('\nCamp Management Menu')
            print('\nChoose [1] to Create a Camp'
                  '\nChoose [2] to Edit Existing Camp'
                  '\nChoose [3] to Delete a Camp'
                  '\nChoose [4] to Return to Main Menu')
            choice = get_int("\nInput your option: ", 1, 3)

            if choice == 1:
                create_camp()
            elif choice == 2:
                edit_camp()
            elif choice == 3:
                delete_camp()
            elif choice == 4:
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
                while True:
                    try:
                        new_stock = int(input("New daily stock: "))
                        break
                    except ValueError:
                        print("Please enter a valid whole number!")
                set_food_stock(camp, new_stock)

            elif sub == 2:
                camp = input("Camp name: ")
                while True:
                    try:
                        amount = int(input("Amount to add: "))
                        break
                    except ValueError:
                        print("Please enter a valid whole number!")
                top_up_food(camp, amount)

            elif sub == 3:
                camp = input("Camp name: ")
                check_food_shortage(camp)

            else:
                continue

        elif choice == 3:
            dashboard()

        elif choice == 4:
            while True:
                print("\nVisualisation Menu")
                print("[1] Food Stock per Camp")
                print("[2] Camper Distribution")
                print("[3] Leaders per Camp")
                print("[4] Engagement Overview")
                print("[5] Return")
                viz_choice = get_int("Choice: ", 1, 5)

                if viz_choice == 1:
                    plot_food_stock()
                elif viz_choice == 2:
                    plot_camper_distribution()
                elif viz_choice == 3:
                    plot_leaders_per_camp()
                elif viz_choice == 4:
                    plot_engagement_scores()
                else:
                    break

        elif choice == 5:
            camp = input("Camp name: ")
            while True:
                try:
                    rate = int(input("Daily pay rate: "))
                    break
                except ValueError:
                    print("Please enter a valid whole number!")
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
            messaging_menu("logistics", users)


        elif choice == 8:
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
# SCOUT LEADER MENU
# -------------------------------------------------

def scout_leader_menu(leader_username):
    while True:
        print('\nScout Leader Menu')
        print('\nChoose [1] to Select camps to supervise'
              '\nChoose [2] to Add campers to a camp'
              '\nChoose [3] to Set daily food per camper'
              '\nChoose [4] to Write daily camp notes (activities / incidents)'
              '\nChoose [5] to View camp summary & statistics'
              '\nChoose [6] to Logout')
        choice = get_int('Input your option: ', 1, 6)

        if choice == 1:
            selecting_camp_to_supervise(leader_username)


        elif choice == 2:
            bulk_assign_campers()

        elif choice == 3 :
            assign_food_amount()

        elif choice == 4:
            record_daily_activity()

        elif choice == 5:
            print('\nChoose [1] to See Engagement Score'
                  '\nChoose [2] to See Details for all Existing Camps'
                  '\nChoose [3] to See Money a Specific Camp Earned'
                  '\nChoose [4] to See Total Money Earned')
            choice = get_int('Input your option: ', 1, 4)

            if choice == 1:
                print_engagement_score()

            if choice == 2:
                info_from_json()

            if choice == 3:
                money_earned_per_camp()

            if choice == 4:

                total_money_earned()


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


#testing