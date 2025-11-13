print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')

print('\nWelcome to CampTrack! Please select a user.')

users = {
    'admin' : {
        'username' : 'admin',
        'password' : '',
    },
    
    'scout leader' : [
        {
        'username' : 'leader1',
        'password' : '',
    }],

    'logistics coordinator' : [{
        'username' : 'logistics',
        'password' : '',
    }]
}


def disabled_logins(username):
    with open('disabled_logins.txt', 'w') as file:
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

            if username in disabled:
                del username
                return True
    except FileNotFoundError:
        return False



def save_logins():
    global users
    with open('logins.txt', 'w') as file:
        file.write(f'admin,{users['admin']['username']},{users['admin']['password']}\n')
        for leader in users['scout leader']:
            file.write(f'scout leader,{leader['username']}, {leader['password']}\n')
        for coordinator in users['logistics coordinator']:
            file.write(f'logistics coordinator,{coordinator['username']},{coordinator['password']}\n')

def load_logins():
    global users
    try: 
        with open('logins.txt','r') as file:
            lines = file.readlines()
            users = {
                'admin': {'username' : 'admin', 'password': ''},
                'scout leader' : [],
                'logistics coordinator' : []
            }
            for line in lines:
                line = line.strip()
                
                parts = [item.strip() for item in line.split(',')]
                if len(parts) < 3:
                    print(f'Skipping malformed line: {line}')
                    continue

                role, username, password = parts[:3]

                if role == 'admin':
                    users['admin'] = {'username' : username, 'password' : password}
                elif role == 'scout leader':
                    users['scout leader'].append({'username' : username, 'password' : password})
                elif role == 'logistics coordinator':
                    users['logistics coordinator'].append({'username' : username, 'password' : password})
    
    except FileNotFoundError:
        print('\n logins.txt not found') 

load_logins()

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
        choice = int(input('\nInput your option: '))

        if choice == 1:
            print('\n--- All Users ---')
            for role, role_info in users.items():
                if role == 'admin':
                    print(f'Role: {role}, Username: {role_info['username']}, Password: {role_info['password']}')
                else:
                    for user in role_info:
                        print(f'Role: {role}, Username: {user['username']}, Password: {user['password']}')

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

            users[new_role].append({'username' : new_username, 'password': new_password})
            print(f'\nUser {new_username} added successfully!')
            save_logins()
        
        elif choice == 3:
            print("\n---Edit a User's password---")
            while True:
                print('\nChoose [1] to see Admin users' \
                '\nChoose [2] to see Scout Leader users' \
                '\nChoose [3] to see Logistics Coordinator users')
                option = int(input('Input your option: '))

                if option == 1:
                    print(f'Select which user to change password:\n[1] {users["admin"]['username']}')
                    option2 = int(input('Input your option: '))
                    if option2 == 1:
                        new_admin_password = str(input(f"Enter a new password for {users['admin']['username']} "))
                        users['admin']['password'] = new_admin_password
                        print(f"\nPassword updated successfully")
                        break
                        save_logins()
                    else:
                        print('Invalid input. Please try again.')
                if option == 2:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n+=1
                        print(f"\nSelect which user to change password:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)
                    
                    option3 = int(input('\nInput your option: '))

                    if option3<= len(scout_leader_user_list):
                        chosen_scout_leader = scout_leader_user_list[option3 - 1]
                        print(f'\nThe current password is {chosen_scout_leader['password']}.')
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
                        n+=1
                        print(f"\nSelect which user to change password:\n[{n}] {user['username']}")
                        logistics_coordinator_user_list.append(user)
                    
                    option4 = int(input('\nInput your option: '))

                    if option4<= len(logistics_coordinator_user_list):
                        chosen_coordinator = logistics_coordinator_user_list[option4 - 1]
                        print(f'\nThe current password is {chosen_coordinator['password']}.')
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
            
                print('\nChoose [1] to see Scout Leader users' \
                '\nChoose [2] to see Logistics Coordinator users')
                option = int(input('Input your option: '))
                if option == 1:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n+=1
                        print(f"\nSelect which user to delete:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)
                        
                    option5 = int(input('\nInput your option: '))

                    if option5<= len(scout_leader_user_list):
                        del users['scout leader'][option5-1]
                        print('\nUser deleted successfully')
                        save_logins()
                        break
                    else:
                     print('\nInvalid input. Please try again.')
                
                if option == 2:
                    n = 0
                    logistics_coordinator_user_list = []
                    for user in users['logistics coordinator']:
                        n+=1
                        print(f"\nSelect which user to change password:\n[{n}] {user['username']}")
                        logistics_coordinator_user_list.append(user)
                    
                    option6 = int(input('\nInput your option: '))

                    if option6<= len(logistics_coordinator_user_list):
                        del users['logistics coordinator'][option6-1]
                        print(f'\nUser deleted successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')

        elif choice == 5:
            while True:
                print('\nChoose [1] to see Scout Leader users' \
                '\nChoose [2] to see Logistics Coordinator users')
                option = int(input('Input your option: '))
                if option == 1:
                    n = 0
                    scout_leader_user_list = []
                    for user in users['scout leader']:
                        n+=1
                        print(f"\nSelect which user to disable:\n[{n}] {user['username']}")
                        scout_leader_user_list.append(user)
                    option5 = int(input('\nInput your option: '))

                    if option5<= len(scout_leader_user_list):
                        user_to_disable = users['scout leader'][option5 -1]
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
                        n+=1
                        print(f"\nSelect which user to disable:\n[{n}] {user['username']}")
                        logistics_coordinator_user_list.append(user)
                    
                    option6 = int(input('\nInput your option: '))

                    if option6<= len(logistics_coordinator_user_list):
                        user_to_disable = users['logistics coordinator'][option6 - 1]
                        disabled_logins(user_to_disable['username'])
                        print(f'\nUser disabled successfully')
                        save_logins()
                        break
                    else:
                        print('\nInvalid input. Please try again.')
        
        elif choice == 6:
           continue 

        elif choice == 7:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')

            print('\nWelcome to CampTrack! Please select a user.')
            return

        else: print('Invald input. Please try again.')


def login_admin():
    login = True
    while login == True:
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
    while login == True:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        user = users['scout leader']
        if check_disabled_logins(ask_username):
            print("This account has been disabled.")
            return
        elif user['username'] == ask_username and user['password'] == ask_password:
            print('\nLogin successful! Welcome Scout Leader.\n')
            login = False
        else:
            print('\nInvalid username or password.\n')

        
def login_logisticscoordinator():
    login = True
    while login == True:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        user = users['logistics coordinator']
        if check_disabled_logins(ask_username):
            print("This account has been disabled.")
            return       
        if user['username'] == ask_username and user['password'] == ask_password:
            print('\nLogin successful! Welcome Logistics Coordinator.\n')
            login = False
        else:
            print('\nInvalid username or password.\n')
    

while True:
    option = int(input("\nChoose [1] for Application Administrator\n" \
    "Choose [2] for Scout Leader\n" \
    "Choose [3] for Logistics Coordinator\n\n" \
    "Input your option: "))
    if option == 1:
        login_admin()
    elif option == 2:
        login_scoutleader()
    elif option == 3:
        login_logisticscoordinator()
    else:
        print('Invalid input. Please try again.')

    

        
