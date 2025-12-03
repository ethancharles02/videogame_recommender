import json

def get_genres(games: list) -> set[str]:
    """Gets all genres from a games list

    Arguments:
        games {list} -- Games to pull genres from

    Returns:
        set[str] -- ~ delimited string for genre id and genre description
    """
    genres = set()
    for game in games:
        key_list = list(game.keys())
        id = key_list[0]
        data = game[id]
        if "data" in data:
            data = data["data"]
            if "genres" in data:
                for genre in data["genres"]:
                    genres.add(f"{genre['id']}~{genre['description']}")
    return genres

def get_types(games: list) -> set[str]:
    """Gets all types from a games list

    Arguments:
        games {list} -- Games to pull types from

    Returns:
        set[str] -- Set of types
    """
    types = set()
    for game in games:
        key_list = list(game.keys())
        id = key_list[0]
        data = game[id]
        if "data" in data:
            data = data["data"]
            types.add(data["type"])
    return types

if __name__ == "__main__":
    filename = "new_game_dump.ndjson"
    games = []
    num_to_grab = 100
    with open(filename, "r") as f:
        # games = [json.loads(line) for line in f.readlines(num_to_grab)]
        for line in f:
            games.append(json.loads(line))

    # Banned ids = 71 (Sexual content), 72 (Nudity)
    banned_genre_ids = ["71", "72"]
    min_required_recommendations = 10000
    # Currently bans based off number of recommendations, genre, type (is it a game), and if it actually has data
    banned_indices = []
    for i, game in enumerate(games):
        key_list = list(game.keys())
        id = key_list[0]
        data = game[id]
        if "data" in data:
            data = data["data"]
            type = data["type"]
            if type != "game":
                banned_indices.append(i)
                continue
            if "recommendations" not in data:
                banned_indices.append(i)
                continue
            recommendations = data["recommendations"]["total"]
            if recommendations < min_required_recommendations:
                banned_indices.append(i)
                continue
            if "genres" in data:
                for genre in data["genres"]:
                    if genre["id"] in banned_genre_ids:
                        banned_indices.append(i)
                        break
        else:
            banned_indices.append(i)

    num_indices = len(banned_indices)
    print(num_indices)
    banned_indices.reverse()
    for i in banned_indices:
        games.pop(i)

    new_filename = "filtered_games.ndjson"
    with open(new_filename, "w") as f:
        for game in games:
            f.write(json.dumps(game))
            f.write("\n")