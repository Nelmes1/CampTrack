from datetime import datetime, timedelta
import json
import os
from utils import data_path

class Camp:
    all_camps = []

    def __init__(self, name, location, camp_type, start_date, end_date, initial_food_stock):
        self.name = name
        self.location = location
        self.camp_type = camp_type
        self.start_date = start_date
        self.end_date = end_date
        self.food_stock = initial_food_stock

        # Always start empty – system fills these later
        self.scout_leaders = []
        self.campers = []
        self.activities = {}
        self.daily_food_usage = {}
        self.daily_records = {}
        self.pay_rate = 0
        self.group_chat = []  # Add group chat to each camp

        Camp.all_camps.append(self)

    # --------------- CAMP OPERATIONS --------------- #

    def assign_leader(self, leader_choice):
        if leader_choice not in self.scout_leaders:
            self.scout_leaders.append(leader_choice)
            self.message_group_chat("System", f"{leader_choice} has joined the group chat.")
        else:
            print(f"\nLeader '{leader_choice}' is already assigned to this camp.")

    def assign_campers(self, camper_list):
        for camper in camper_list:
            if camper not in self.campers:
                self.campers.append(camper)
            else:
                print(f"\nCamper '{camper}' is already assigned to this camp.")

    def assign_activity(self, activity, date):
        if date not in self.activities:
            self.activities[date] = []
        self.activities[date].append(activity)

    def allocate_extra_food(self, amount):
        self.food_stock += amount

    def note_daily_record(self, date, notes):
        if date not in self.daily_records:
            self.daily_records[date] = []
        self.daily_records[date].append(notes)

    def message_group_chat(self, from_user, message_text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = {
            "from": from_user,
            "text": message_text,
            "timestamp": timestamp
        }
        self.group_chat.append(message)
        save_to_file()

    def get_group_chat(self):
        return self.group_chat

    def summary(self):
        print("\n--- Camp Summary ---")
        print(f"Name: {self.name}")
        print(f"Location: {self.location}")
        print(f"Type: {self.camp_type}")
        print(f"Start Date: {self.start_date}")
        print(f"End Date: {self.end_date}")
        print(f"Leaders: {self.scout_leaders}")
        print(f"Campers: {len(self.campers)}")
        print(f"Current Food Stock: {self.food_stock}")


# -------------------------------------------------
# SAVE / LOAD FUNCTIONS
# -------------------------------------------------

def save_to_file():
    data = []
    for camp in Camp.all_camps:
        data.append({
            "name": camp.name,
            "location": camp.location,
            "camp_type": camp.camp_type,
            "start_date": camp.start_date,
            "end_date": camp.end_date,
            "food_stock": camp.food_stock,
            "scout_leaders": camp.scout_leaders,
            "campers": camp.campers,
            "activities": camp.activities,
            "daily_food_usage": camp.daily_food_usage,
            "daily_records": camp.daily_records,
            "pay_rate": camp.pay_rate,
            "group_chat": camp.group_chat
        })

    with open(data_path("camp_data.json"), "w") as file:
        json.dump(data, file, indent=4)


def read_from_file():
    if not os.path.exists(data_path("camp_data.json")):
        print("\ncamp_data.json not found")
        return []

    if os.path.getsize(data_path("camp_data.json")) == 0:
        return []

    try:
        with open(data_path("camp_data.json"), "r") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        print("\nError reading camp_data.json — file is corrupted.")
        return []

    Camp.all_camps = []

    for camp_data in data:
        camp = Camp(
            camp_data["name"],
            camp_data["location"],
            camp_data["camp_type"],
            camp_data["start_date"],
            camp_data["end_date"],
            camp_data["food_stock"]
        )

        # Restore saved values
        camp.scout_leaders = camp_data.get("scout_leaders", [])
        camp.campers = camp_data.get("campers", [])
        camp.activities = camp_data.get("activities", {})
        camp.daily_food_usage = camp_data.get("daily_food_usage", {})
        camp.daily_records = camp_data.get("daily_records", {})
        camp.pay_rate = camp_data.get("pay_rate", 0)
        camp.group_chat = camp_data.get("group_chat", [])

    return Camp.all_camps
