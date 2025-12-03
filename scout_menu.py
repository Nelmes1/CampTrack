from messaging import messaging_menu
from utils import get_int
from features.scout import (
    assign_camps_to_leader_ui,
    bulk_assign_campers_ui,
    assign_food_amount,
    record_daily_activity,
    show_engagement_scores,
    info_from_json,
    show_money_per_camp,
    show_total_money,
    view_activity_stats,
)


def run(leader_username):
    while True:
        print('\nScout Leader Menu')
        print('\nChoose [1] to Select camps to supervise'
              '\nChoose [2] to Bulk assign campers from CSV'
              '\nChoose [3] to Assign food amount per camper per day'
              '\nChoose [4] to Record daily activity outcomes / incidents'
              '\nChoose [5] to View camp statistics and trends'
              '\nChoose [6] to Messaging'
              '\nChoose [7] to Logout')
        choice = get_int('Input your option: ', 1, 7)

        if choice == 1:
            assign_camps_to_leader_ui(leader_username)

        elif choice == 2:
            bulk_assign_campers_ui(leader_username)

        elif choice == 3:
            assign_food_amount()

        elif choice == 4:
            record_daily_activity()

        elif choice == 5:
            print('\nChoose [1] to See Engagement Score'
                  '\nChoose [2] to See Details for all Existing Camps'
                  '\nChoose [3] to See Money a Specific Camp Earned'
                  '\nChoose [4] to See Total Money Earned'
                  '\nChoose [5] to See Activity Summary')
            choice = get_int('Input your option: ', 1, 5)

            if choice == 1:
                show_engagement_scores()

            if choice == 2:
                info_from_json()

            if choice == 3:
                show_money_per_camp()

            if choice == 4:
                show_total_money()

            if choice == 5:
                view_activity_stats()

        elif choice == 6:
            from user_logins import users
            messaging_menu(leader_username, users)

        elif choice == 7:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
            print('\nWelcome to CampTrack! Please select a user.')
            return

        else:
            print('Invalid input. Please try again.')
