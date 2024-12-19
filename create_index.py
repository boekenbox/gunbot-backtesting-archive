import os
import json
import requests
import base64
from datetime import datetime

# GitHub repository details
REPO_OWNER = os.getenv('GITHUB_REPOSITORY').split('/')[0]
REPO_NAME = os.getenv('GITHUB_REPOSITORY').split('/')[1]
BRANCH = 'main'

# GitHub API URL
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents"

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
INDEX_FILE_PATH = 'index.json'
TESTS_DIR = 'tests'

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_file_content(file_path):
    """Fetch the content of a file from GitHub."""
    url = f"{API_URL}/{file_path}?ref={BRANCH}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_info = response.json()
        if file_info['encoding'] == 'base64':
            return base64.b64decode(file_info['content']).decode('utf-8'), file_info['sha']
        else:
            raise ValueError(f"Unsupported encoding for file {file_path}")
    elif response.status_code == 404:
        return None, None
    else:
        response.raise_for_status()

def update_file_content(file_path, content, sha=None):
    """Update or create a file in GitHub."""
    url = f"{API_URL}/{file_path}"
    data = {
        "message": "Update index.json",
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code in [200, 201]:
        return True
    else:
        response.raise_for_status()

def list_json_files():
    """List all JSON files in the tests directory."""
    url = f"{API_URL}/{TESTS_DIR}?ref={BRANCH}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    json_files = [file['path'] for file in files if file['type'] == 'file' and file['name'].endswith('.json')]
    return json_files

def load_existing_index():
    """Load existing index.json."""
    content, sha = get_file_content(INDEX_FILE_PATH)
    if content:
        index_data = json.loads(content)
        index_dict = {entry['id']: entry for entry in index_data}
        return index_dict, sha
    else:
        return {}, None

def save_index(index_data):
    """Save index.json to GitHub."""
    content = json.dumps(list(index_data.values()), indent=4)
    # Get the current sha of index.json
    _, sha = get_file_content(INDEX_FILE_PATH)
    update_success = update_file_content(INDEX_FILE_PATH, content, sha)
    return update_success

def extract_data(file_content, filename):
    """Extract required data from JSON content."""
    data = json.loads(file_content)

    # Get the last modified time from GitHub (assuming commit time as proxy)
    # Alternatively, you can include a 'last_modified' field in your JSON files
    # For simplicity, we'll use the current time
    timestamp = datetime.utcnow().isoformat()

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
    # Load existing index
    index_dict, _ = load_existing_index()
    updated = False

    # List all JSON files in tests/
    json_files = list_json_files()

    for file_path in json_files:
        # Extract ID from the JSON file
        file_content, _ = get_file_content(file_path)
        if not file_content:
            print(f"Failed to fetch {file_path}. Skipping.")
            continue

        try:
            data = json.loads(file_content)
            file_id = data.get("id")
            if not file_id:
                print(f"No ID found in {file_path}. Skipping.")
                continue
        except json.JSONDecodeError:
            print(f"Invalid JSON in {file_path}. Skipping.")
            continue

        # Check if the file is already indexed
        if file_id in index_dict:
            continue  # Already indexed

        # Extract data and update index
        try:
            entry = extract_data(file_content, os.path.basename(file_path))
            index_dict[file_id] = entry
            updated = True
            print(f"Indexed: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    if updated:
        # Save updated index.json to GitHub
        success = save_index(index_dict)
        if success:
            print("Index file updated.")
            # Indicate that changes were made
            with open(os.environ.get('GITHUB_OUTPUT', 'output.txt'), 'a') as f:
                f.write("changed=true\n")
        else:
            print("Failed to update index.json.")
            with open(os.environ.get('GITHUB_OUTPUT', 'output.txt'), 'a') as f:
                f.write("changed=false\n")
    else:
        print("No changes to index.json.")
        with open(os.environ.get('GITHUB_OUTPUT', 'output.txt'), 'a') as f:
            f.write("changed=false\n")

if __name__ == "__main__":
    main()
