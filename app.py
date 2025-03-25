import pandas as pd
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from datetime import timedelta

def parse_bus_time(bus_time_obj, reference_date):
    if not pd.notna(bus_time_obj):
        return None
    return datetime.combine(reference_date, bus_time_obj)

app = Flask(__name__)

# Load the bus routes CSV
import os

CSV_PATH = os.path.join(os.getcwd(), "newBusRoutes_Cleaned.csv")
bus_data = pd.read_csv(CSV_PATH)

# Extract bus stop names from column headers
stop_columns = [col for col in bus_data.columns if "Stop " in col and "Time" not in col]
all_stops = set()


# Collect unique stop names from the CSV
for col in stop_columns:
    all_stops.update(bus_data[col].dropna().unique())

# Define on-campus stops for the "Campus" umbrella category
CAMPUS_STOPS = {"Mohawk", "Rafuse", "Union", "Return to Campus"}
DOWNTOWN_STOPS = {"Downtown", "UDC", "State & Hawley"}

remaining_stops = all_stops - CAMPUS_STOPS - DOWNTOWN_STOPS
sorted_stops = ["Campus (Includes All Campus Stops)", "Downtown (State & Hawley and UDC)"] + sorted(remaining_stops)

sorted_stops = sorted(all_stops - CAMPUS_STOPS - DOWNTOWN_STOPS)



# Convert stop times to datetime.time
for col in bus_data.columns:
    if "Time" in col:
        bus_data[col] = pd.to_datetime(bus_data[col], format="%I:%M %p", errors="coerce").dt.time

# Mapping of days for filtering
DAYS_MAP = {
    "Monday": "M", "Tuesday": "T", "Wednesday": "W", "Thursday": "Th",
    "Friday": "F", "Saturday": "Sat", "Sunday": "Sun"
}

def parse_day_schedule(day_str):
    """Parses day ranges from the CSV (e.g., "Monday-Friday") into a list of individual days."""
    if pd.isna(day_str):
        return []  # Handle NaT values gracefully
    day_str = day_str.strip()
    if "-" in day_str:  # Handle ranges like "Monday-Friday"
        start_day, end_day = day_str.split("-")
        start_index = list(DAYS_MAP.keys()).index(start_day.strip())
        end_index = list(DAYS_MAP.keys()).index(end_day.strip())
        return list(DAYS_MAP.values())[start_index : end_index + 1]
    return [DAYS_MAP.get(day_str, day_str)]  # Return single day if no range

# Filter buses based on user input
def parse_user_time(user_time_str):
    """
    Tries multiple time formats (12-hour with AM/PM and 24-hour).
    Returns a datetime.time() if successful, or None if parsing fails.
    """
    formats_to_try = ["%I:%M %p", "%H:%M"]  # 12-hour, then 24-hour
    for fmt in formats_to_try:
        try:
            return datetime.strptime(user_time_str.strip(), fmt).time()
        except ValueError:
            continue
    return None  # If all formats fail

def compute_next_bus_datetime(bus_time_obj, user_datetime):
    """
    Given a bus time (a time object) and a user's datetime,
    returns the next datetime occurrence of the bus time after user_datetime.
    """
    if not pd.notna(bus_time_obj):
        return None
    # Combine the bus time with the user's date.
    bus_dt = datetime.combine(user_datetime.date(), bus_time_obj)
    # If the bus time has already passed on that day, use the next day.
    if bus_dt < user_datetime:
        bus_dt += timedelta(days=1)
    return bus_dt

def fix_stop_display(original_name):
    name_lower = original_name.strip().lower()
    if name_lower == "downtown":
        return "State & Hawley"
    elif name_lower == "return to campus":
        return "Campus"
    else:
        return original_name

@app.route("/", methods=["GET", "POST"])
def index():
    buses = []  # Default empty list for buses
    user_day = None
    start_location = request.form.get("start_location", "Campus (Includes All Campus Stops)")
    end_location = request.form.get("end_location", "Campus (Includes All Campus Stops)")
    user_time_str = request.form.get("time", "")
    user_date_str = request.form.get("date", datetime.today().strftime("%Y-%m-%d"))

    try:
        user_date = datetime.strptime(user_date_str, "%Y-%m-%d")
        user_day = DAYS_MAP[user_date.strftime("%A")]
    except ValueError:
        user_day = None

    user_time = parse_user_time(user_time_str)  # using your parse_user_time helper

    if start_location == "Campus":
        start_locations = CAMPUS_STOPS
    elif start_location == "Downtown":
        start_locations = DOWNTOWN_STOPS
    else:
        start_locations = {start_location}

    if end_location == "Campus":
        end_locations = CAMPUS_STOPS
    elif end_location == "Downtown":
        end_locations = DOWNTOWN_STOPS
    else:
        end_locations = {end_location}

    remaining_stops = all_stops - CAMPUS_STOPS - DOWNTOWN_STOPS
    sorted_stops = sorted(remaining_stops)
    
    for _, row in bus_data.iterrows():
        route_name = row["Route"]
        route_days = row["Day"]
        valid_days = parse_day_schedule(route_days)
        if user_day not in valid_days:
            continue

        stops_times = [
            (row[stop], row[f"{stop} Time"])
            for stop in stop_columns
            if pd.notna(row[stop])
        ]

        # This inner loop is now inside the row loop:
        for i in range(len(stops_times)):
            stop_name, start_time = stops_times[i]
            if stop_name in start_locations and pd.notna(start_time):
                for j in range(i + 1, len(stops_times)):
                    end_stop_name, end_time = stops_times[j]
                    if end_stop_name in end_locations and pd.notna(end_time):
                        if user_time is None:
                            start_stop_display = fix_stop_display(stop_name)
                            end_stop_display = fix_stop_display(end_stop_name)                            
                            buses.append({
                                "route": route_name,
                                "start_stop": start_stop_display,
                                "end_stop": end_stop_display,
                                "start_time": start_time.strftime("%I:%M %p"),
                                "end_time": end_time.strftime("%I:%M %p"),
                                "sort_time": start_time,  # Used for sorting
                                "full_schedule": [
                                    {"stop": row[stop], "time": row[f"{stop} Time"].strftime("%I:%M %p")}
                                    for stop in stop_columns
                                    if pd.notna(row[stop]) and pd.notna(row[f"{stop} Time"])
                                ],
                            })
                        else:
                            user_datetime = datetime.combine(user_date, user_time)
                            bus_start_dt = compute_next_bus_datetime(start_time, user_datetime)
                            if bus_start_dt and bus_start_dt >= user_datetime and bus_start_dt < (user_datetime + timedelta(days=1)):
                                start_stop_display = fix_stop_display(stop_name)
                                end_stop_display = fix_stop_display(end_stop_name)
                                buses.append({
                                    "route": route_name,
                                    "start_stop": start_stop_display,
                                    "end_stop": end_stop_display,
                                    "start_time": start_time.strftime("%I:%M %p"),
                                    "end_time": end_time.strftime("%I:%M %p"),
                                    "sort_time": bus_start_dt,  # Use datetime for accurate sorting
                                    "full_schedule": [
                                        {"stop": row[stop], "time": row[f"{stop} Time"].strftime("%I:%M %p")}
                                        for stop in stop_columns
                                        if pd.notna(row[stop]) and pd.notna(row[f"{stop} Time"])
                                    ],
                                })
                        break  # Stop searching for an end stop after the first match

    buses = sorted(buses, key=lambda x: x["sort_time"])
    sorted_stops = ["Campus"] + sorted(all_stops - CAMPUS_STOPS)
    return render_template("index.html", stops=sorted_stops, buses=buses, 
                           start_location=start_location, end_location=end_location, 
                           date=user_date_str, time=user_time_str)

if __name__ == "__main__":
    app.run(debug=True)