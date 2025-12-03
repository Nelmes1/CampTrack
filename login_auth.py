from menus.admin_menu import run as admin_menu
from menus.logistics_menu import run as logistics_coordinator_menu
from menus.scout_menu import run as scout_leader_menu
from user_logins import users, check_disabled_logins
from utils import get_int


def login_admin():
    login = True
    while login:
        print('Please login.')
        ask_username = str(input('\nUsername: '))
        ask_password = str(input('Password: '))
        if check_disabled_logins(ask_username):
            print("This account has been disabled.")
            return
        matched = False
        for admin in users['admin']:
            if admin['username'] == ask_username and admin['password'] == ask_password:
                print('\nLogin successful! Welcome Application Administrator.\n')
                matched = True
                login = False
                admin_menu()
                break
        if not matched:
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
        matched = False
        for user in users['scout leader']:
            if user['username'] == ask_username and user['password'] == ask_password:
                print('\nLogin successful! Welcome Scout Leader.\n')
                matched = True
                login = False
                scout_leader_menu(ask_username)
                break
        if not matched:
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
        matched = False
        for user in users['logistics coordinator']:
            if user['username'] == ask_username and user['password'] == ask_password:
                print('\nLogin successful! Welcome Logistics Coordinator.\n')
                matched = True
                login = False
                logistics_coordinator_menu(users)
                break
        if not matched:
            print('\nInvalid username or password.\n')


def login_loop():
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
