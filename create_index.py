import os
import json
from datetime import datetime

source_dir = './test'  # Adjust this path to the location of your JSON files in the repo
output_file = './index.json'  # The root folder in the main branch

# Function to extract required data from each JSON file
def extract_data(file_path, filename):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Get the last modified time
    last_modified_time = os.path.getmtime(file_path)
    timestamp = datetime.fromtimestamp(last_modified_time).isoformat()
    
    # Extracting data
    entry = {
        "id": data.get("id"),
        "pair": data.get("pair"),
        "exchange": data.get("exchange"),
        "from": data.get("from"),
        "to": data.get("to"),
        "timestamp": timestamp,  # Adding the timestamp
        "settings": {
            "BUY_METHOD": data.get("settings", {}).get("BUY_METHOD", data.get("strategySettings", {}).get("BUY_METHOD")),
            "SELL_METHOD": data.get("settings", {}).get("SELL_METHOD", data.get("strategySettings", {}).get("SELL_METHOD")),
            "PERIOD": data.get("settings", {}).get("PERIOD", data.get("strategySettings", {}).get("PERIOD"))
        },
        "performance": {
            "ROI": data.get("performance", {}).get("ROI"),
            "Sharpe ratio": data.get("performance", {}).get("Sharpe ratio"),
            "Sortino ratio": data.get("performance", {}).get("Sortino ratio"),
            "Average pnl %": data.get("performance", {}).get("Average pnl %"),
            "Volume": data.get("performance", {}).get("Volume")
        }
    }
    
    # Check if filename contains more than just an ID
    parts = filename.split('-')
    if len(parts) > 2:
        entry['filename'] = filename
    
    return entry

# Collecting all JSON files in the directory
json_files = [f for f in os.listdir(source_dir) if f.endswith('.json')]

# List to store all extracted data
index_data = []

# Extracting data from each JSON file
for json_file in json_files:
    file_path = os.path.join(source_dir, json_file)
    entry = extract_data(file_path, json_file)
    index_data.append(entry)

# Writing the final data to the output JSON file
with open(output_file, 'w') as file:
    json.dump(index_data, file, indent=4)

print(f"Index file created at {output_file}")
