# import json
# with open("game_dump.json", "r") as f:
#     game_dump = json.load(f)

# with open("new_game_dump.json", "w") as f:
#     for game in game_dump:
#         f.write(json.dumps(game))
#         f.write("\n")

import os

if __name__ == "__main__":
    print(os.getenv("OPENAI_API_KEY"))