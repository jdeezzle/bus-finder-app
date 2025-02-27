import pandas as pd

def clean_and_reformat_csv(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file, header=None, dtype=str)
    
    # Fill forward the bus route names (assumes route names appear in column 0)
    df[0] = df[0].fillna(method='ffill')
    
    # Remove empty rows and columns
    df = df.dropna(how='all', axis=0)
    df = df.dropna(how='all', axis=1)
    
    # Rename columns for clarity (assumes first row is header after route names are filled)
    headers = ["Route"] + list(df.iloc[0, 1:].values)
    df.columns = headers
    df = df[1:]  # Drop the first row as it's now the header
    
    # Reset index
    df.reset_index(drop=True, inplace=True)
    
    # Save cleaned file
    df.to_csv(output_file, index=False)
    print(f"✅ Cleaned CSV saved as: {output_file}")

# Usage example
input_csv = "BusRoutes.csv"  # Change this to your actual file path
output_csv = "BusRoutes_Cleaned.csv"
clean_and_reformat_csv(input_csv, output_csv)
