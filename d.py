import pdfplumber
import pandas as pd
import re
import csv  # Import CSV module

def extract_valid_bus_schedules(pdf_path, output_csv):
    extracted_data = []
    unique_schedules = set()
    last_known_route = "Unknown Route"

    time_pattern = r"(\d{1,2}:\d{2} (AM|PM))"

    # **Better Route Name Extraction**
    route_patterns = [
        "Westside Outbound", "Westside Inbound",
        "Downtown Center Leroy", "Main Street", "University Downtown Center",
        "ITC-UClub Shuttle", "UClub Shuttle", "Downtown Express",
        "Campus Shuttle", "Riviera Ridge", "Oakdale Commons Shuttle"
    ]

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            tables = page.extract_tables()
            route_name = last_known_route  # Use last known valid route

            # **Extract Route Name**
            for pattern in route_patterns:
                if pattern in text:
                    route_name = pattern
                    last_known_route = pattern  # Update last known route
                    break  # Stop searching once a match is found

            # **Extract Service Days (Monday - Friday, etc.)**
            service_days = re.search(r"(Monday - Friday|Saturday & Sunday|Friday & Saturday|Sunday|Saturday|Friday)", text)
            service_label = service_days.group(1) if service_days else "Unknown"

            route_name = f"{route_name} ({service_label})"

            # **Extract Tables & Stop Names**
            for table in tables:
                stop_names = []
                schedule_data = []

                for row in table:
                    if not any(re.search(time_pattern, str(cell)) for cell in row if cell):
                        stop_names = [cell.strip() if cell else "" for cell in row]
                        continue  # Save stop names and move on

                    row = [cell.strip() if isinstance(cell, str) else cell for cell in row]
                    schedule_row = [route_name] + row

                    if tuple(schedule_row) not in unique_schedules:
                        unique_schedules.add(tuple(schedule_row))
                        schedule_data.append(schedule_row)

                if schedule_data:
                    extracted_data.append([route_name] + stop_names)
                    extracted_data.extend(schedule_data)
                    extracted_data.append(["---"])  # Separator for readability

    df = pd.DataFrame(extracted_data)
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"✅ Bus schedule with properly formatted stops saved to {output_csv}")

# **Updated File Paths**
pdf_path = "/Users/joshdweck/Desktop/bus_app/OCCT+Spring+2025+Full+Master+Schedule.pdf"
output_csv = "/Users/joshdweck/Desktop/bus_app/OCCT+Spring+2025+Full+Master+Schedule.csv"

# Run Extraction
extract_valid_bus_schedules(pdf_path, output_csv)