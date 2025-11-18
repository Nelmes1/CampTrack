from camp_class import Camp, save_to_file, read_from_file
from datetime import datetime, timedelta
import pandas as pd
import json


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
        return
    
    data = [{
        "Camp": camp.name,
        "Location": camp.location,
        "Type": camp.camp_type,
        "Start Date": camp.start_date,
        "End Date": camp.end_date,
        "Leaders": len(camp.scout_leaders),
        "Campers": len(camp.campers),
        "Food Stock": camp.food_stock,
        "Pay Rate": getattr(camp, "pay_rate", 0)
    } for camp in camps]

    df = pd.DataFrame(data)
    print("\n--- Camp Dashboard ---")
    print(df)
    return df   

# Visualisations
import matplotlib.pyplot as plt

def plot_food_stock():
    df = dashboard()
    df.plot(kind="bar", x="Camp", y="Food Stock", title="Food Stock per Camp")
    plt.show()

#Shortage Notifications
def check_food_shortage(camp_name, food_per_camper):
    if not isinstance(food_per_camper, int) or food_per_camper < 0:
        print("Food per camper must be a non-negative whole number.")
        return
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            try:
                start = datetime.strptime(camp.start_date, "%Y-%m-%d")
                end = datetime.strptime(camp.end_date, "%Y-%m-%d")
                camp_duration_days = max((end - start).days + 1, 1)
            except (TypeError, ValueError):
                camp_duration_days = 1

            required_amount = len(camp.campers) * food_per_camper * camp_duration_days
            print(f"{camp.name} requires {required_amount} units for {len(camp.campers)} campers over {camp_duration_days} day(s).")
            if camp.food_stock < required_amount:
                notify(f"Food shortage at {camp_name}! Only {camp.food_stock} units left but {required_amount} needed.")
            else:
                print("Food stock is sufficient.")
            return
    print("Camp not found.")
#check_food_shortage takes food_per_camper, validates it, computes the total requirement (campers × per-day × duration), 
# prints that forecast, and either logs a detailed shortage notification or confirms stock sufficiency. 
# It also guards against malformed dates while calculating the duration. 
# Also, adds +1 so a camp starting and ending on the same day = 1 day.  
# and if dates are invalid camp_duration_days = 1. 
# #Scout Leaders assign food required per camper per day and coordinator checks shortages
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
