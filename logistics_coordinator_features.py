from camp_class import Camp, save_to_file, read_from_file
from datetime import datetime, timedelta
import pandas as pd
import json
import matplotlib.pyplot as plt


def _engagement_score(camp):
    """Simple engagement proxy based on recorded activities and daily reports."""
    activity_events = sum(len(events) for events in camp.activities.values())
    record_entries = sum(len(entries) for entries in camp.daily_records.values())
    return activity_events + record_entries

#The function :counts how many activities a camp has, counts how many notes a camp has,
# adds them together, returns that number as an “engagement score”
# It’s a quick indicator of how involved and active a camp is.


#Tops up the food stock
def top_up_food(camp_name, amount):
    if not isinstance(amount, int) or amount < 0:
        print("Top-up amount must be a non-negative whole number.")
        return
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            camp.food_stock += amount
            save_to_file()
            print(f"Food stock for {camp_name} increased by {amount}.")
            return
    print("Camp not found.")

#Sets the daily food stock 
def set_food_stock(camp_name, new_stock):
    if not isinstance(new_stock, int) or new_stock < 0:
        print("Food stock must be a non-negative whole number.")
        return
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            camp.food_stock = new_stock
            save_to_file()
            print(f"Daily food stock for {camp_name} set to {new_stock}.")
            return
    print("Camp not found.")

#Shows a dashboard using Pandas
def dashboard():
    camps = read_from_file()
    if not camps:
        print("No camps found.")
        return None

    total_campers = sum(len(camp.campers) for camp in camps)
    total_leaders = sum(len(camp.scout_leaders) for camp in camps)

    data = []
    for camp in camps:
        campers = len(camp.campers)
        leaders = len(camp.scout_leaders)
        engagement = _engagement_score(camp)
        camper_pct = round((campers / total_campers) * 100, 2) if total_campers else 0
        leader_ratio = round(leaders / campers, 2) if campers else 0
        data.append({
            "Camp": camp.name,
            "Location": camp.location,
            "Type": camp.camp_type,
            "Start Date": camp.start_date,
            "End Date": camp.end_date,
            "Leaders": leaders,
            "Campers": campers,
            "Camper %": camper_pct,
            "Leader/Camper Ratio": leader_ratio,
            "Engagement Score": engagement,
            "Food Stock": camp.food_stock,
            "Pay Rate": getattr(camp, "pay_rate", 0)
        })

    df = pd.DataFrame(data)
    print("\n--- Camp Dashboard ---")
    print(df.to_string(index=False))

    print("\n--- Summary ---")
    summary = {
        "Total Campers": total_campers,
        "Total Leaders": total_leaders,
        "Average Engagement": round(df["Engagement Score"].mean(), 2) if not df.empty else 0,
        "Average Leader/Camper Ratio": round(df["Leader/Camper Ratio"].mean(), 2) if not df.empty else 0
    }
    for label, value in summary.items():
        print(f"{label}: {value}")

    return df


# Visualisations
def _ensure_dataframe(df):
    if df is None:
        print("No data available for visualisation.")
        return None
    if df.empty:
        print("No data available for visualisation.")
        return None
    return df


def plot_food_stock(df=None):
    df = _ensure_dataframe(df or dashboard())
    if df is None:
        return
    df.plot(kind="bar", x="Camp", y="Food Stock", title="Food Stock per Camp")
    plt.ylabel("Units")
    plt.tight_layout()
    plt.show()


def plot_camper_distribution(df=None):
    df = _ensure_dataframe(df or dashboard())
    if df is None:
        return
    df.set_index("Camp")["Campers"].plot(kind="pie", autopct="%1.1f%%", title="Camper Distribution", ylabel="")
    plt.tight_layout()
    plt.show()


def plot_leaders_per_camp(df=None):
    df = _ensure_dataframe(df or dashboard())
    if df is None:
        return
    df.plot(kind="bar", x="Camp", y="Leaders", title="Leaders per Camp", color="orange")
    plt.ylabel("Leaders")
    plt.tight_layout()
    plt.show()


def plot_engagement_scores(df=None):
    df = _ensure_dataframe(df or dashboard())
    if df is None:
        return
    df.plot(kind="bar", x="Camp", y="Engagement Score", title="Engagement Score per Camp", color="green")
    plt.ylabel("Engagement Score")
    plt.tight_layout()
    plt.show()

#Shortage Notifications
def check_food_shortage(camp_name, required_amount):
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            if camp.food_stock < required_amount:
                notify(f"Food shortage at {camp_name}! Only {camp.food_stock} units left.")
            return
    print("Camp not found.")
#Note - required ammount should be computed as campers * food_per_camper * camp_duration_days
 #Scout Leaders assign food required per camper per day and coordinator checks shortages
 #adjust this function later to calculate required amount automatically - once leader features are ready




def notify(message):
    try:
        with open("notifications.json", "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(message)

    with open("notifications.json", "w") as f:
        json.dump(data, f, indent=4)

#Sets Daily Pay Rate 
def set_pay_rate(camp_name, rate):
    if not isinstance(rate, int) or rate < 0:
        print("Pay rate must be a non-negative whole number.")
        return
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            camp.pay_rate = rate
            save_to_file()
            print(f"Pay rate for {camp_name} set to {rate}.")
            return
    print("Camp not found.")

#Check that dates entered match camp type (eg overnight = 1 night, multiday = at least 2)
def get_dates(camp_type):
    start_date = input('\nPlease enter the start date (YYYY-MM-DD): ')

    valid = False
    while not valid:
        try:
            first_date = datetime.strptime(start_date, "%Y-%m-%d")
            if camp_type == 1:
                nights = 0
                second_date = first_date + timedelta(days=nights)
                valid = True
            elif camp_type == 2:
                nights = 1
                second_date = first_date + timedelta(days=nights)
                valid = True
            elif camp_type == 3:
                nights = int(input("\nHow many nights is the camp? "))
                if nights < 2:
                    print("A multi-day camp must be at least 2 nights.")
                    continue
                second_date = first_date + timedelta(days=nights)
                valid = True
        except ValueError:
            print('Invalid date format! Please use YYYY-MM-DD.')
            start_date = input('\nPlease enter the start date (YYYY-MM-DD): ')

    start_date = first_date.strftime("%Y-%m-%d")
    end_date = second_date.strftime("%Y-%m-%d")

    return start_date, end_date
