from user_logins import users, save_logins, disabled_logins, enable_login
from utils import get_int


def run():
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
                        print('\nInvalid input. Please try again.')

                elif option == 2:
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
                        chosen_leader = scout_leader_user_list[option3 - 1]
                        print(f"\nThe current password is {chosen_leader['password']}.")
                        new_leader_password = str(input(f"Enter a new password for {chosen_leader['username']}: "))
                        chosen_leader['password'] = new_leader_password
                        print('\nPassword updated successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

                elif option == 3:
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
