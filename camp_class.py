from datetime import datetime, timedelta
import os
import json


class Camp():
    
    all_camps=[]
    
    def __init__(self, name, location, camp_type, start_date, end_date, initial_food_stock, scout_leaders, campers, activities, daily_food_usage, daily_records, pay_rate):
        self.name = name
        self.location = location
        self.camp_type = camp_type
        self.start_date = start_date
        self.end_date = end_date
        self.food_stock = initial_food_stock
        self.scout_leaders = scout_leaders           # List of assigned scout leaders
        self.campers = campers                       # List of campers
        self.activities = activities                 # Dict: {date: list of activities}
        self.daily_food_usage = daily_food_usage     # Dict: {date: food used}
        self.daily_records = daily_records           # Dict: {date: notes}
        self.pay_rate = pay_rate
        
        Camp.all_camps.append(self)

    def assign_leader(self, leader_choice): # Function to assign leader to camp
        if leader_choice not in self.scout_leaders:
            self.scout_leaders.append(leader_choice)
        else:
            print("\nLeader:",leader_choice,"already assigned to this camp")

    def assign_campers(self, camper_list): # Function to assign campers to camp
        for camper in camper_list:
            if camper not in self.campers:
                self.campers.append(camper)
            else:
                print("\nCamper:",camper,"already assigned to this camp")

    def assign_activity(self, activity_names, date): # Function to assign activies to dictionary with key 'Date'
        if date not in self.activities:
            self.activities[date] = []
        self.activities[date].append(activity_names)
        

    def calc_daily_food(self, food_per_camper): # Function to calculate total daily food usage and remaining supply 
        pass

    def allocate_extra_food(self, food_allocation): # Function to allocate extra food to a camp
        self.food_stock += food_allocation

    def note_daily_record(self, date, notes): #Function to add notes to dictionary with key 'Date'
        if date not in self.daily_records:
            self.daily_records[date] = []
        self.daily_records[date].append(notes)

    def summary(self):
        print("\n ---Camp Summary---",
              "\nName:",self.name,
              "\nLocation:",self.location,
              "\nCamp Type:",self.camp_type,
              "\nStart Date:",self.start_date,
              "\nEnd Date:",self.end_date,
              "\nLeaders:",self.scout_leaders,
              "\nNumber of Campers:",len(self.campers),
              "\nCurrent Food Stock:",self.food_stock)

def save_to_file():
    data=[]
    for camp in Camp.all_camps:
        camp_data = {
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
            "pay_rate": camp.pay_rate
        }
        data.append(camp_data)
    
    with open("camp_data.json","w") as file:
        json.dump(data, file, indent=4)

def read_from_file():
    try:
        if os.path.getsize("camp_data.json") == 0:
            return []
        else:
            Camp.all_camps = []
            with open("camp_data.json","r") as file:
                data=json.load(file)
                Camp.all_camps = []
                for camp_data in data:
                    camp = Camp(
                        camp_data["name"],
                        camp_data["location"],
                        camp_data["camp_type"],
                        camp_data["start_date"],
                        camp_data["end_date"],
                        camp_data["food_stock"],
                        camp_data["scout_leaders"],
                        camp_data["campers"],
                        camp_data["activities"],
                        camp_data["daily_food_usage"],
                        camp_data["daily_records"],
                        camp_data["pay_rate"])
                return Camp.all_camps
    except FileNotFoundError:
        print('\ncamp_data.json not found')
