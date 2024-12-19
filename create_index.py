import os
import json
from datetime import datetime

source_dir = './tests'  # Directory containing JSON files
output_file = './index.json'  # Path to the index file

def load_existing_index(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return {entry['id']: entry for entry in json.load(f)}
    return {}

def save_index(index_data, file_path):
    with open(file_path, 'w') as f:
        json.dump(list(index_data.values()), f, indent=4)

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

def main():
    existing_index = load_existing_index(output_file)
    updated = False

    # Collect all JSON files in the directory
    try:
        json_files = [f for f in os.listdir(source_dir) if f.endswith('.json')]
    except FileNotFoundError:
        print(f"Source directory '{source_dir}' not found.")
        json_files = []

    for json_file in json_files:
        file_path = os.path.join(source_dir, json_file)
        file_id = None

        # Extract ID to check if it's already in index
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                file_id = data.get("id")
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON file: {json_file}")
            continue

        if not file_id:
            print(f"Skipping file with no ID: {json_file}")
            continue

        # Get last modified time
        last_modified_time = os.path.getmtime(file_path)
        timestamp = datetime.fromtimestamp(last_modified_time).isoformat()

        # Check if the file is already indexed and up-to-date
        if file_id in existing_index:
            if existing_index[file_id]['timestamp'] >= timestamp:
                continue  # No update needed

        # Extract and update the index
        try:
            entry = extract_data(file_path, json_file)
            existing_index[file_id] = entry
            updated = True
            print(f"Indexed/Updated: {json_file}")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue

    if updated:
        save_index(existing_index, output_file)
        print(f"Index file updated at {output_file}")
        # Indicate that changes were made
        with open(os.environ.get('GITHUB_OUTPUT', 'output.txt'), 'a') as f:
            f.write("changed=true\n")
    else:
        print("No changes to index.json")
        with open(os.environ.get('GITHUB_OUTPUT', 'output.txt'), 'a') as f:
            f.write("changed=false\n")

if __name__ == "__main__":
    main()
