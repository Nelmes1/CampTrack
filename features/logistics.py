from datetime import datetime, timedelta
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from camp_ops import create_camp, edit_camp, delete_camp, get_dates
from camp_class import Camp, save_to_file, read_from_file
from features.notifications import add_notification
from utils import get_int, data_path


def _engagement_score(camp):
    """Simple engagement proxy based on recorded activities and daily reports."""
    activity_events = sum(len(events) for events in camp.activities.values())
    record_entries = sum(len(entries) for entries in camp.daily_records.values())
    return activity_events + record_entries


def top_up_food_data(camp_name, amount):
    if not isinstance(amount, int) or amount < 0:
        return {"status": "invalid_amount"}
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            camp.food_stock += amount
            save_to_file()
            return {"status": "ok", "camp_name": camp_name, "amount": amount}
    return {"status": "camp_not_found"}


def top_up_food(camp_name, amount):
    res = top_up_food_data(camp_name, amount)
    status = res.get("status")
    if status == "invalid_amount":
        print("Top-up amount must be a non-negative whole number.")
    elif status == "camp_not_found":
        print("Camp not found.")
    elif status == "ok":
        print(f"Food stock for {camp_name} increased by {amount}.")


def set_food_stock_data(camp_name, new_stock):
    if not isinstance(new_stock, int) or new_stock < 0:
        return {"status": "invalid_amount"}
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            camp.food_stock = new_stock
            save_to_file()
            return {"status": "ok", "camp_name": camp_name, "new_stock": new_stock}
    return {"status": "camp_not_found"}


def set_food_stock(camp_name, new_stock):
    res = set_food_stock_data(camp_name, new_stock)
    status = res.get("status")
    if status == "invalid_amount":
        print("Food stock must be a non-negative whole number.")
    elif status == "camp_not_found":
        print("Camp not found.")
    elif status == "ok":
        print(f"Daily food stock for {camp_name} set to {new_stock}.")

#Shortage Notifications
def load_food_requirement(camp_name):
    try:
        with open(data_path("food_requirements.json"), "r") as file:
            data = json.load(file)
        return data.get(camp_name)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def compute_food_shortage(camp_name):
    """Pure helper returning status/info about food shortage."""
    food_per_camper = load_food_requirement(camp_name)
    if food_per_camper is None:
        return {"status": "missing_requirement"}
    if not isinstance(food_per_camper, int) or food_per_camper < 0:
        return {"status": "invalid_requirement"}
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            try:
                start = datetime.strptime(camp.start_date, "%Y-%m-%d")
                end = datetime.strptime(camp.end_date, "%Y-%m-%d")
                camp_duration_days = max((end - start).days + 1, 1)
            except (TypeError, ValueError):
                camp_duration_days = 1

            camper_count = len(camp.campers)

            total_available = camp.food_stock * camp_duration_days
            required_amount = camper_count * food_per_camper * camp_duration_days
            status = "shortage" if total_available < required_amount else "ok"
            return {
                "status": status,
                "required": required_amount,
                "available": total_available,
                "camp_name": camp.name,
                "campers": camper_count,
                "days": camp_duration_days,
                "food_per_camper": food_per_camper,
                "camp_food_stock": camp.food_stock,
            }
    return {"status": "camp_not_found"}


def check_food_shortage(camp_name):
    res = compute_food_shortage(camp_name)
    status = res.get("status")
    if status == "missing_requirement":
        print("No food requirement set for this camp. Ask the scout leader to set daily food per camper.")
        return
    if status == "invalid_requirement":
        print("Food per camper must be a non-negative whole number.")
        return
    if status == "camp_not_found":
        print("Camp not found.")
        return
    print(f"{res['camp_name']} requires {res['required']} units for {res['campers']} campers over {res['days']} day(s).")
    if status == "shortage":
        add_notification(f"Food shortage at {camp_name}! Only {res['camp_food_stock']} units left but {res['required']} needed.")
    else:
        print("Food stock is sufficient.")
#check_food_shortage takes food_per_camper, validates it, computes the total requirement (campers × per-day × duration), 
# prints that forecast, and either logs a detailed shortage notification or confirms stock sufficiency. 
# It also guards against malformed dates while calculating the duration. 
# Also, adds +1 so a camp starting and ending on the same day = 1 day.  
# and if dates are invalid camp_duration_days = 1. 
# #Scout Leaders assign food required per camper per day and coordinator checks shortages
 #adjust this function later to calculate required amount automatically - once leader features are ready


#Shows a dashboard using Pandas
def build_dashboard_data():
    """Return (df, summary) for camps without printing/plotting."""
    camps = read_from_file()
    if not camps:
        return None, None

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
    summary = {
        "Total Campers": total_campers,
        "Total Leaders": total_leaders,
        "Average Engagement": round(df["Engagement Score"].mean(), 2) if not df.empty else 0,
        "Average Leader/Camper Ratio": round(df["Leader/Camper Ratio"].mean(), 2) if not df.empty else 0
    }
    return df, summary


def dashboard():
    df, summary = build_dashboard_data()
    if df is None:
        print("\nNo camps found.")
        return None

    print("\n--- Camp Dashboard ---")
    print(df.to_string(index=False))

    print("\n--- Summary ---")
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


def plot_food_stock(df=None, show=True):
    df = _ensure_dataframe(df or build_dashboard_data()[0])
    if df is None:
        return
    ax = df.plot(kind="bar", x="Camp", y="Food Stock", title="Food Stock per Camp")
    ax.set_ylabel("Units")
    plt.tight_layout()
    if show:
        plt.show()
    return ax


def plot_camper_distribution(df=None, show=True):
    df = _ensure_dataframe(df or build_dashboard_data()[0])
    if df is None:
        return
    ax = df.set_index("Camp")["Campers"].plot(kind="pie", autopct="%1.1f%%", title="Camper Distribution", ylabel="")
    plt.tight_layout()
    if show:
        plt.show()
    return ax


def plot_leaders_per_camp(df=None, show=True):
    df = _ensure_dataframe(df or build_dashboard_data()[0])
    if df is None:
        return
    ax = df.plot(kind="bar", x="Camp", y="Leaders", title="Leaders per Camp", color="orange")
    ax.set_ylabel("Leaders")
    plt.tight_layout()
    if show:
        plt.show()
    return ax


def plot_engagement_scores(df=None, show=True):
    df = _ensure_dataframe(df or build_dashboard_data()[0])
    if df is None:
        return
    ax = df.plot(kind="bar", x="Camp", y="Engagement Score", title="Engagement Score per Camp", color="green")
    ax.set_ylabel("Engagement Score")
    plt.tight_layout()
    if show:
        plt.show()
    return ax


def set_pay_rate_data(camp_name, rate):
    if not isinstance(rate, int) or rate < 0:
        return {"status": "invalid_amount"}
    camps = read_from_file()
    for camp in camps:
        if camp.name == camp_name:
            camp.pay_rate = rate
            save_to_file()
            return {"status": "ok", "camp_name": camp_name, "rate": rate}
    return {"status": "camp_not_found"}


def set_pay_rate(camp_name, rate):
    res = set_pay_rate_data(camp_name, rate)
    status = res.get("status")
    if status == "invalid_amount":
        print("Pay rate must be a non-negative whole number.")
    elif status == "camp_not_found":
        print("Camp not found.")
    elif status == "ok":
        print(f"Pay rate for {camp_name} set to {rate}.")
