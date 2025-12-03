import os
#os.path.dirname(__file__) is the folder containing utils.py (project root).
#os.path.join(..., "data") builds a path to a subfolder named data in that directory.
#This last line guarantees the directory is there before the first file operation, 
#and exist_ok=True avoids errors if it already exists.
#It’s just a guard to prevent “No such file or directory” on first run.

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# func to build full paths to files in the data directory
# i.e. data_path("messages.json") -> "/Users/student/Desktop/CampTrack/data/messages.json"

def data_path(filename):
    return os.path.join(DATA_DIR, filename)

def get_int(prompt, min_val=None, max_val=None):
    while True:
        user_input = input(prompt)

        if not user_input.isdigit():
            print("Invalid input. Please enter a number.")
            continue

        value = int(user_input)

        if (min_val is not None and value < min_val) or \
           (max_val is not None and value > max_val):
            print("Invalid option. Please choose a valid number.")
            continue

        return value