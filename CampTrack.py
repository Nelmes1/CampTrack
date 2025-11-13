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


def save_logins():
    global users
    with open('logins.txt', 'w') as file:
        file.write(f'admin,{users['admin']['username']},{users['admin']['password']}\n')
        for leader in users['scout leader']:
            file.write(f'scout leader,{leader['username']}, {leader['password']}\n')
        for coordinator in users['logistics coordinator']:
            file.write(f'logistics coordinator,{coordinator['username']},{coordinator['password']}')

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
                role, username, password = line.split(',')
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
            '\nChoose [5] to Logout')
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
                '\nChoose [3] to see Logistics Coordinator logins')
                option = int(input('Input your option: '))

                if option == 1:
                    print(f'Select which user to change password:\n[1] {users["admin"]['username']}')
                    option2 = int(input('Input your option: '))
                    


def login_admin():
    login = True
    while login == True:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        user = users['admin']
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
        if user['username'] == ask_username and user['password'] == ask_password:
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
        break
    elif option == 2:
        login_scoutleader()
        break
    elif option == 3:
        login_logisticscoordinator()
        break
    else:
        print('Invalid input. Please try again.')

    

        
