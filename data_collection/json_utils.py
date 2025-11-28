import requests
import json
import time

def get_json_from_url(url):
    success = False
    while not success:
        try:
            response = requests.get(url)
            response.raise_for_status()
            json_data = response.json()
            success = True
            return json_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
        except requests.exceptions.JSONDecodeError as e:
            print(f"Error decoding JSON from {url}: {e}")
        time.sleep(5)

def write_json_to_file(filename, json_dict):
    with open(filename, "a") as f:
        for item in json_dict:
            f.write(json.dumps(item))
            f.write("\n")

def load_ndjson_file(filename):
    apps_dump_data = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            apps_dump_data.append(obj)
    return apps_dump_data

def load_json_file(filename: str):
    with open(filename, "r") as f:
        json_dict = json.load(f)

    return json_dict

def convert_ndjson_to_json(read_filename: str, write_filename: str):
    lines: list[dict] = load_ndjson_file(read_filename)
    json_dict = {}
    for line in lines:
        id = list(line.keys())[0]
        json_dict[id] = line[id]

    with open(write_filename, "w") as f:
        json.dump(json_dict, f)

if __name__ == "__main__":
    convert_ndjson_to_json("filtered_games.ndjson", "filtered_games.json")
    # convert_ndjson_to_json("rated_games.ndjson", "rated_games.json")