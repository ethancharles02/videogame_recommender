# from openai import OpenAI
# client = OpenAI()
# response = client.responses.create(model="gpt-5", input="What is 1 + 1")

# print(response.output_text)

import json
with open("game_dump.json", "r") as f:
    game_dump = json.load(f)
    
with open("new_game_dump.json", "w") as f:
    for game in game_dump:
        f.write(json.dumps(game))
        f.write("\n")