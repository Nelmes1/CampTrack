from messaging import messaging_menu
from utils import get_int
from features.scout import (
    assign_camps_to_leader_ui,
    bulk_assign_campers_ui,
    assign_food_amount,
    record_daily_activity,
    show_engagement_scores,
    show_money_per_camp,
    show_total_money,
    view_activity_stats,
    view_activity_list,
    view_incident_list,
    incident_summary,
    stats_summary_all,
    stats_summary_one,
)
from features.notifications import count_unread


def run(leader_username):
    while True:
        unread = count_unread(leader_username)
        badge = f" (unread notifications: {unread})" if unread else ""
        print(f'\nScout Leader Menu{badge}')
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
                  '\nChoose [2] to See Money a Specific Camp Earned'
                  '\nChoose [3] to See Total Money Earned'
                  '\nChoose [4] to See Activity Summary (by camp)'
                  '\nChoose [5] to See Incident Summary (by camp)'
                  '\nChoose [6] to View activity list (with delete)'
                  '\nChoose [7] to View incident list (with delete)'
                  '\nChoose [8] to View stats for one camp'
                  '\nChoose [9] to View stats for all camps')
            choice = get_int('Input your option: ', 1, 9)

            if choice == 1:
                show_engagement_scores()

            if choice == 2:
                show_money_per_camp()

            if choice == 3:
                show_total_money()

            if choice == 4:
                view_activity_stats()

            if choice == 5:
                incident_summary()

            if choice == 6:
                view_activity_list()

            if choice == 7:
                view_incident_list()

            if choice == 8:
                stats_summary_one()

            if choice == 9:
                stats_summary_all()

        elif choice == 6:
            from user_logins import users
            messaging_menu(leader_username, users)

        elif choice == 7:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
            print('\nWelcome to CampTrack! Please select a user.')
            return

        else:
            print('Invalid input. Please try again.')
