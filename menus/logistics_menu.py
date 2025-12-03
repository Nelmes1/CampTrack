from messaging import messaging_menu
from camp_ops import create_camp, edit_camp, delete_camp
from features.logistics import (
    top_up_food,
    set_food_stock,
    check_food_shortage,
    dashboard,
    plot_food_stock,
    plot_camper_distribution,
    plot_leaders_per_camp,
    plot_engagement_scores,
    set_pay_rate,
)
from features.notifications import load_notifications
from camp_class import read_from_file
from utils import get_int


def run(users):
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
                  '\nChoose [3] to Delete Camp'
                  '\nChoose [4] to Return to Main Menu')
            choice = get_int("\nInput your option: ", 1, 4)

            if choice == 1:
                create_camp()
            elif choice == 2:
                edit_camp()
            elif choice == 3:
                delete_camp()
            elif choice == 4:
                continue
            else:
                print('Invalid input. Please try again.')

        elif choice == 2:
            print("\nFood Allocation Menu")
            print("(Leave camp name blank to cancel.)")
            print("[1] Set Daily Food Stock")
            print("[2] Top-Up Food Stock")
            print("[3] Check Food Shortage")
            print("[4] Return")
            sub = get_int("Choice: ", 1, 4)

            if sub == 1:
                camp = input("Camp name: ").strip()
                if camp == "":
                    print("Cancelled.")
                    continue
                while True:
                    try:
                        new_stock = int(input("New daily stock: "))
                        break
                    except ValueError:
                        print("Please enter a valid whole number!")
                set_food_stock(camp, new_stock)

            elif sub == 2:
                camp = input("Camp name: ").strip()
                if camp == "":
                    print("Cancelled.")
                    continue
                while True:
                    try:
                        amount = int(input("Amount to add: "))
                        break
                    except ValueError:
                        print("Please enter a valid whole number!")
                top_up_food(camp, amount)

            elif sub == 3:
                camp = input("Camp name: ").strip()
                if camp == "":
                    print("Cancelled.")
                    continue
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
            camps = read_from_file()
            if not camps:
                print("\nNo camps exist yet.")
                continue

            print("\n--- Existing Camps ---")
            for i, camp in enumerate(camps, start=1):
                print(f"[{i}] {camp.name} ({camp.location})")

            sel = input("\nSelect a camp to set pay rate (or press Enter to cancel): ").strip()
            if sel == "":
                print("Cancelled.")
                continue
            if not sel.isdigit() or not (1 <= int(sel) <= len(camps)):
                print("Invalid selection.")
                continue
            camp = camps[int(sel) - 1].name

            rate = get_int("Daily pay rate: ", 0)
            set_pay_rate(camp, rate)

        elif choice == 6:
            notes = load_notifications()
            if notes:
                print("\n--- Notifications ---")
                for n in notes:
                    print("-", n)
            else:
                print("No notifications found.")
        elif choice == 7:
            messaging_menu("logistics", users)


        elif choice == 8:
            print('╔═══════════════╗\n║   CampTrack   ║\n╚═══════════════╝')
            print('\nWelcome to CampTrack! Please select a user.')
            return

        else:
            print('Invalid input. Please try again.')
