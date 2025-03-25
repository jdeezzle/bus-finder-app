import pandas as pd

file_path = "/Users/joshdweck/Desktop/bus_app/BusRoutes.csv"

df = pd.read_csv(file_path, header=0, dtype=str)

# Clean column names (remove newlines and extra spaces)
df.columns = df.columns.str.replace("\n", " ", regex=True).str.strip()

# Extract unique stop names from all columns (except first column which is Route)
stop_columns = df.columns[1:]
all_stops = set()

for col in stop_columns:
    all_stops.update(df[col].dropna().unique())

# Print all stops detected from the CSV
print("🔹 All Stops Detected from CSV:")
for stop in sorted(all_stops):
    print(f"- {stop}")