import json
import os
import time

from .json_utils import load_ndjson_file, get_json_from_url, write_ndjson_to_file

if __name__ == "__main__":
    # steam_game_data = get_json_from_url("http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json")
    with open("game_list.json", "r") as f:
        steam_game_data = json.load(f)

    apps_data = []
    game_count = len(steam_game_data["applist"]["apps"])
    game_dump_filename = "new_game_dump.ndjson"

    apps_dump_data = []
    # Gets the length of the previous game_dump if it exists
    if os.path.exists(game_dump_filename):
        apps_dump_data = load_ndjson_file(game_dump_filename)

    start = len(apps_dump_data)

    # Figures out the amount of calls we can do with our given run_time and rate_limit
    rate_limit = 1.5
    time_to_run_in_minutes = 24 * 60
    update_time_in_seconds = 10
    amount = int((time_to_run_in_minutes*60) // rate_limit)
    # amount = 10
    end = amount + start
    end = end if end < game_count else game_count

    # One hour worth of downloads will be appended to the file at a time. Set to 0 to disable
    num_downloads_till_update = 2400

    print(f"Downloading {amount} entries from Steam. {start}/{game_count} downloaded already which is {(start/game_count):.2%}")

    # Goes through and requests the data and adds it to our list
    time_elapsed_since_update = 0
    for i in range(start, end):
        # Number of actual downloaded in this run
        adjusted_i = i - start
        if time_elapsed_since_update >= update_time_in_seconds:
            time_elapsed_since_update = 0
            print(f" --- {(adjusted_i / amount):.2%} {adjusted_i}/{amount} ---", end="\r")
        app_id = steam_game_data['applist']['apps'][i]['appid']
        apps_data.append(get_json_from_url(f"https://store.steampowered.com/api/appdetails?appids={app_id}"))

        if num_downloads_till_update > 0:
            num_downloads = adjusted_i + 1
            if num_downloads % num_downloads_till_update == 0:
                print(f"Updating game data at {num_downloads} downloads")
                write_ndjson_to_file(game_dump_filename, apps_data)
                apps_data.clear()

        time.sleep(rate_limit)
        time_elapsed_since_update += rate_limit

    # Get previous dump to add to it
    write_ndjson_to_file(game_dump_filename, apps_data)