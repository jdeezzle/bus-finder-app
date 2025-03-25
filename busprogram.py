import pandas as pd
from datetime import datetime

def load_schedule(file_path):
    """Loads the bus schedule from a CSV file."""
    df = pd.read_csv(file_path)
    return df

def find_routes(schedule, start_location, end_location, user_time):
    """Finds available routes based on user input."""
    matching_routes = []
    
    for _, row in schedule.iterrows():
        route_name = row["Route"]
        stops = row.drop("Route").dropna().to_dict()
        
        if start_location in stops.values() and end_location in stops.values():
            start_time = None
            end_time = None
            
            for time, stop in stops.items():
                if stop == start_location:
                    start_time = datetime.strptime(time, "%I:%M %p")
                if stop == end_location and start_time:
                    end_time = datetime.strptime(time, "%I:%M %p")
                    break
            
            if start_time and end_time and start_time >= user_time:
                matching_routes.append((route_name, start_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p")))
    
    return sorted(matching_routes, key=lambda x: x[1])

# Example usage
if __name__ == "__main__":
    schedule_file = "/Users/joshdweck/Desktop/bus_app/BusRoutes.csv"  # Update with correct file path
    schedule_df = load_schedule(schedule_file)
    
    # User input
    start = input("Enter starting location: ")
    end = input("Enter destination: ")
    time_input = input("Enter preferred time (HH:MM AM/PM): ")
    user_time = datetime.strptime(time_input, "%I:%M %p")
    
    results = find_routes(schedule_df, start, end, user_time)
    
    if results:
        print("\nAvailable Buses:")
        for route in results:
            print(f"Route: {route[0]} | Departure: {route[1]} | Arrival: {route[2]}")
    else:
        print("No buses available for the given criteria.")
