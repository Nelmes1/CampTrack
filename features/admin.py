from user_logins import users, save_logins, disabled_logins, enable_login
from utils import get_int


def list_users():
    print('\n--- All Users ---')
    for admin in users['admin']:
        print(f"Role: admin, Username: {admin['username']}, Password: {admin['password']}")
    for role in ['scout leader', 'logistics coordinator']:
        for user in users[role]:
            print(f"Role: {role}, Username: {user['username']}, Password: {user['password']}")


def add_user():
    print('\n---Add New User---')
    print('\nChoose the role you wish to add.')
    while True:
        new_role_option = get_int('\nChoose [1] for Scout Leader'
                                  '\nChoose [2] for Logistics Coordinator'
                                  '\nChoose [3] for Admin'
                                  '\nInput your option: ', 1, 3)
        if new_role_option == 1:
            new_role = 'scout leader'
            break
        if new_role_option == 2:
            new_role = 'logistics coordinator'
            break
        if new_role_option == 3:
            new_role = 'admin'
            break
        else:
            print('Invalid input. Please try again.')

    while True:
        new_username = input('Enter username: ').strip()
        if new_username == "":
            print("Username cannot be blank.")
            continue
        # check duplicates
        existing_names = []
        existing_names.extend(u['username'] for u in users['admin'])
        existing_names.extend(u['username'] for u in users['scout leader'])
        existing_names.extend(u['username'] for u in users['logistics coordinator'])
        if new_username in existing_names:
            print("Username already exists. Please choose another.")
            continue
        break

    while True:
        new_password = input('Enter password (blank allowed): ')
        # allow blank, but confirm
        confirm = input('Confirm password (press Enter to accept): ')
        if new_password != confirm:
            print("Passwords do not match. Try again.")
            continue
        break

    if new_role == 'admin':
        users['admin'].append({'username': new_username, 'password': new_password})
    else:
        users[new_role].append({'username': new_username, 'password': new_password})
    print(f"\nUser {new_username} added successfully as {new_role}!")
    add_notification(f"New user: {new_username} added as {new_role}")
    save_logins()


def edit_user_password():
    print("\n---Edit a User's password---")
    while True:
        print('\nChoose [1] to see Admin users'
              '\nChoose [2] to see Scout Leader users'
              '\nChoose [3] to see Logistics Coordinator users')

        option = get_int('Input your option: ', 1, 3)

        if option == 1:
            if not users['admin']:
                print("\nNo admin users found.")
                continue
            print("Select which admin to change password:")
            for idx, admin in enumerate(users['admin'], start=1):
                print(f"[{idx}] {admin['username']}")
            option2 = get_int('Input your option: ', 1, len(users['admin']))
            chosen_admin = users['admin'][option2 - 1]
            new_admin_password = str(input(f"Enter a new password for {chosen_admin['username']}: "))
            chosen_admin['password'] = new_admin_password
            print("\nPassword updated successfully")
            save_logins()
            break

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


def delete_user():
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


def disable_user():
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


def enable_user():
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
        n = 0
        for disabled_username in disabled_usernames:
            n += 1
            print(f"[{n}] {disabled_username}")

        option = get_int("\nInput your option: ", 1, len(disabled_usernames))
        username_to_enable = disabled_usernames[option-1]
        # verify the username still exists in users
        existing_names = set()
        existing_names.update(u['username'] for u in users['admin'])
        existing_names.update(u['username'] for u in users['scout leader'])
        existing_names.update(u['username'] for u in users['logistics coordinator'])
        if username_to_enable not in existing_names:
            print(f"\nUser '{username_to_enable}' no longer exists in users; cannot enable.")
            continue
        enable_login(username_to_enable)
        print(f"\n User '{username_to_enable}' enabled successfully!")
        break
