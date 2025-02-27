import pandas as pd
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Load the bus routes CSV
CSV_PATH = "/Users/joshdweck/documents/bus_app/newBusRoutes_Cleaned - BusRoutes_Cleaned.csv"
bus_data = pd.read_csv(CSV_PATH)

# Extract bus stop names from column headers
stop_columns = [col for col in bus_data.columns if "Stop " in col and "Time" not in col]
all_stops = set()

# Collect unique stop names from the CSV
for col in stop_columns:
    all_stops.update(bus_data[col].dropna().unique())

# Define on-campus stops for the "Campus" umbrella category
CAMPUS_STOPS = {"Mohawk", "Rafuse", "Union", "Return to Campus"}

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

@app.route("/", methods=["GET", "POST"])
def index():
    buses = []  # Default empty list for buses
    user_day = None

    # Keep selected values persistent
    start_location = request.form.get("start_location", "Campus")
    end_location = request.form.get("end_location", "Campus")
    user_time_str = request.form.get("time", "")
    user_date_str = request.form.get("date", datetime.today().strftime("%Y-%m-%d"))

    # Convert date to weekday
    try:
        user_date = datetime.strptime(user_date_str, "%Y-%m-%d")
        user_day = DAYS_MAP[user_date.strftime("%A")]  # Convert to single-letter format
    except ValueError:
        user_day = None  # Ensure it doesn't break

    # Convert input time to datetime.time
    try:
        user_time = datetime.strptime(user_time_str, "%I:%M %p").time()
    except ValueError:
        user_time = None

    # Adjust start and end locations if "Campus" is selected
    start_locations = CAMPUS_STOPS if start_location == "Campus" else {start_location}
    end_locations = CAMPUS_STOPS if end_location == "Campus" else {end_location}

    # Filter buses based on user input
    for _, row in bus_data.iterrows():
        route_name = row["Route"]
        route_days = row["Day"]
        valid_days = parse_day_schedule(route_days)

        if user_day not in valid_days:
            continue  # Skip routes that don’t operate on selected day

        stops_times = [(row[stop], row[f"{stop} Time"]) for stop in stop_columns if pd.notna(row[stop])]

        # Find buses that start at the start location and end at the destination
        for i in range(len(stops_times)):
            stop_name, start_time = stops_times[i]

            if stop_name in start_locations and pd.notna(start_time):
                # Find the next available stop that matches the destination
                for j in range(i + 1, len(stops_times)):
                    end_stop_name, end_time = stops_times[j]

                    if end_stop_name in end_locations and pd.notna(end_time):
                        if user_time is None or start_time >= user_time:  # Ensure the bus is after user time
                            buses.append({
                                "route": route_name,
                                "start_stop": stop_name,  # Keep actual stop name
                                "end_stop": end_stop_name,  # Keep actual stop name
                                "start_time": start_time.strftime("%I:%M %p"),
                                "end_time": end_time.strftime("%I:%M %p"),
                                "sort_time": start_time,  # Used for sorting
                            })
                        break  # Stop searching for an end stop after the first match

    # ✅ Sort buses by departure time (earliest first)
    buses = sorted(buses, key=lambda x: x["sort_time"])

    # ✅ Ensure "Campus" appears first in dropdowns
    sorted_stops = ["Campus"] + sorted(all_stops - CAMPUS_STOPS)

    return render_template("index.html", stops=sorted_stops, buses=buses, 
                           start_location=start_location, end_location=end_location, 
                           date=user_date_str, time=user_time_str)

if __name__ == "__main__":
    app.run(debug=True)