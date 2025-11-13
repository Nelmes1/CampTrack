import json

class Camp():
    def __init__(self, name, location, camp_type, start_date, end_date, initial_food_stock):
        self.name = name
        self.location = location
        self.camp_type = camp_type
        self.start_date = start_date
        self.end_date = end_date
        self.food_stock = initial_food_stock
        self.scout_leaders = []           # List of assigned scout leaders
        self.campers = []                 # List of campers
        self.activities = {}              # Dict: {date: list of activities}
        self.daily_food_usage = {}        # Dict: {date: food used}
        self.daily_records = {}           # Dict: {date: notes}

    def assign_leader(self, leader_choice): # Function to assign leader to camp
        if leader_choice not in self.scout_leaders:
            self.scout_leaders.append(leader_choice)
        else:
            print("\nLeader:",leader_choice,"already assigned to this camp")

    def assign_campers(self, camper_list): # Function to assign campers to camp
        for i in range (len(camper_list)):
            if camper_list not in self.campers:
                self.campers.append(camper_list[i])
            else:
                print("\nCamper:",camper_list[i],"already assigned to this camp")

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

    def save_to_file(self):
        for camps in Camp
        data = {
            "name": self.name,
            "location": self.location,
            "camp_type": self.camp_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "leaders": self.scout_leaders,
            "campers": self.campers,
            "food_stock": self.food_stock,
            "activities": self.activities,
            "daily_food_usage": self.daily_food_usage,
            "daily_records": self.daily_records,
                }
        try:
            with open("camp_data.json","w") as file:
                json.dump(data, file, indent=4)
        except FileNotFoundError:
            print('\n logins.txt not found') 
            
camp1 = Camp(
    name="Forest Scouts",
    location="Greenwood National Park",
    camp_type="Overnight",
    start_date="2025-07-01",
    end_date="2025-07-10",
    initial_food_stock=150
)

camp1.assign_leader("Leader John")
camp1.assign_campers(["Alice", "Ben", "Charlie", "Daisy"])
camp1.assign_activity("Hiking", "2025-07-02")
camp1.calc_daily_food(food_per_camper=2)
camp1.allocate_extra_food(20)
camp1.note_daily_record("2025-07-02", "Great hike, no incidents.")
camp1.summary()
camp1.save_to_file()
        
    
    
