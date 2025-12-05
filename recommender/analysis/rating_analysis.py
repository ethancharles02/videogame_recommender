from ..data_collection import load_json_file
from bs4 import BeautifulSoup

def print_game_average_scores():
    ratings = load_json_file("rating_ratings.json")

    rating_count = len(ratings.keys())
    total_rating_score = 0
    min_score = 1000
    max_score = 0
    for key in ratings.keys():
        rating = ratings[key]
        if rating < min_score:
            min_score = rating
        if rating > max_score:
            max_score = rating
        total_rating_score += rating

    print(f"Average score: {total_rating_score / rating_count}\nMin score: {min_score}\nMax score: {max_score}")

def print_average_game_emotional_ratings():
    emotional_ratings = load_json_file("rated_games.json")

    average_dict = {
        "anger" : 0,
        "disgust" : 0,
        "fear" : 0,
        "happiness" : 0,
        "sadness" : 0,
        "surprise" : 0
    }
    emotion_list = list(average_dict.keys())

    rating_count = len(emotional_ratings.keys())

    happiness_threshhold = 3
    happiness_count = 0
    anger_threshhold = 8
    anger_count = 0
    for key in emotional_ratings.keys():
        for emotion in emotion_list:
            rating = emotional_ratings[key][emotion]
            average_dict[emotion] += rating

        if emotional_ratings[key]["happiness"] >= happiness_threshhold:
            happiness_count += 1
        if emotional_ratings[key]["anger"] >= anger_threshhold:
            anger_count += 1

    for key in average_dict.keys():
        average_dict[key] /= rating_count
        print(f"{key}: {average_dict[key]:.2f}")

    print(f"Number of games above happiness threshhold: {happiness_count}")
    print(f"Number of games above anger threshhold: {anger_count}")

def print_description_details():
    game_data = load_json_file("filtered_games.json")

    game_count = len(game_data.keys())

    largest_description_count = 0
    largest_description_id = -1
    largest_word_count = 0

    total_word_count = 0
    total_description_count = 0
    # 50 words or less will save the count
    small_description_threshold = 100
    small_description_count = 0
    for key in game_data.keys():
        description = game_data[key]["data"]["detailed_description"]
        soup = BeautifulSoup(description,  "html.parser")
        raw_description = soup.get_text().strip()
        description_length = len(raw_description)
        word_count = len(raw_description.split(" "))
        if word_count <= small_description_threshold:
            small_description_count += 1
            print(f"Game's description below threshold: {key}")

        if description_length > largest_description_count:
            largest_description_id = key
            largest_description_count = description_length
            largest_word_count = word_count

        total_word_count += word_count
        total_description_count += description_length

    print(f"Number of games below description threshhold: {small_description_count}")
    print(f"Average description length: {total_description_count / game_count}")
    print(f"Average word count: {total_word_count / game_count}")
    print(f"Largest Description Length/Word Count/Game ID: {largest_description_count}/{largest_word_count}/{largest_description_id}")

def main():
    print_average_game_emotional_ratings()

if __name__ == "__main__":
    main()