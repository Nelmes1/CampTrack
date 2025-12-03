from features.admin import (
    list_users,
    add_user,
    edit_user_password,
    delete_user,
    disable_user,
    enable_user,
)
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
              '\nChoose [7] to Messaging'
              '\nChoose [8] to Logout')
        choice = get_int("Input your option: ", 1, 8)

        if choice == 1:
            list_users()

        elif choice == 2:
            add_user()

        elif choice == 3:
            edit_user_password()

        elif choice == 4:
            delete_user()

        elif choice == 5:
            disable_user()

        elif choice == 6:
            enable_user()

        elif choice == 7:
            from messaging import messaging_menu
            from user_logins import users
            messaging_menu("admin", users)

        elif choice == 8:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
            print('\nWelcome to CampTrack! Please select a user.')
            return

        else:
            print('Invalid input. Please try again.')
