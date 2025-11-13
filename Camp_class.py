import json

class Camp():
    
    all_camps=[]
    
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
            "daily_records": camp.daily_records
        }
        data.append(camp_data)
    try:
        with open("camp_data.json","w") as file:
            json.dump(data, file, indent=4)
    except FileNotFoundError:
        print('\n camp_data.json not found')

def read_from_file():
    try:
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
                camp_data["food_stock"]
            )
            camp.scout_leaders = camp_data["scout_leaders"]
            camp.campers = camp_data["campers"]
            camp.activities = camp_data["activities"]
            camp.daily_food_usage = camp_data["daily_food_usage"]
            camp.daily_records = camp_data["daily_records"]
        return Camp.all_camps
    except FileNotFoundError:
        print('\n camp_data.json not found')
        
        
read_from_file()            

camp2 = Camp(
    name="beach Scouts",
    location="yellowwood National Park",
    camp_type="Overnight",
    start_date="2025-07-01",
    end_date="2025-07-10",
    initial_food_stock=150
    )


camp2.assign_leader("Leader John")
camp2.assign_campers(["Alice", "Ben", "Charlie", "Daisy"])
camp2.assign_activity("Hiking", "2025-07-02")
camp2.calc_daily_food(food_per_camper=2)
camp2.allocate_extra_food(20)
camp2.note_daily_record("2025-07-02", "Great hike, no incidents.")


for i in range (len(Camp.all_camps)):
    Camp.all_camps[i].summary()
save_to_file()

        
    
    
