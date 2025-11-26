# CampTrack

CLI tool to manage camps for Admin, Scout Leader, and Logistics Coordinator roles.

## Setup

1) Create/activate a virtualenv (optional but recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:
```bash
pip install -r requirements.txt
```

## Running

CLI:
```bash
python app.py
```

GUI (Tkinter):
```bash
python gui.py
```

Default accounts (empty passwords):
- admins: `admin`
- logistics coordinator: `coordinator`
- scout leaders: `leader1`, `leader2`, `leader3`, `leader4`

## Data files

Runtime data is stored under `data/`:
- `camp_data.json` – camps, leaders, campers, activities, records
- `messages.json` – messaging threads
- `notifications.json` – system notifications
- `food_requirements.json` – per-camp food requirements

User/login data remains in `logins.txt` and `disabled_logins.txt` at the project root.

CSV bulk import expects `campers/` (sibling to `data/`) with CSV files containing `Name,Age,Activities` columns.
