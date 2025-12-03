import json
from enum import Enum
from models.analysis_model import AnalysisModel
from models.gpt_model import GptAnalyisModel
import numpy as np

class IncorrectReturnTypes(Enum):
    """Represents the different types of errors that could come about from the
    model doing sentiment analysis
    """
    DecodeError = 0
    NoReturn = 1
    IncorrectContent = 2
    IncorrectNumEmotions = 3
    IncorrectEmotions = 4
    IncorrectValueRange = 5

class IncorrectReturnDetails:
    """The details for an incorrect return. It holds the type of error and a
    message to go with it
    """
    def __init__(self, type: IncorrectReturnTypes, message: str):
        self.type = type
        self.message = message

expected_emotions = [
    "anger",
    "disgust",
    "fear",
    "happiness",
    "sadness",
    "surprise"
]

def check_response_content(response_dict: dict) -> dict|IncorrectReturnDetails:
    """Checks the content of a response to make sure it is all formatted
    correctly

    Arguments:
        response_dict {dict} -- Response dictionary with emotions and values

    Returns:
        dict|IncorrectReturnDetails -- Either the dictionary back or details on
            what was wrong
    """
    # Checks for correct number of emotions
    if len(response_dict.keys()) != len(expected_emotions):
        return IncorrectReturnDetails(IncorrectReturnTypes.IncorrectNumEmotions, f"The model returned the incorrect number of emotions. Correct emotions are {', '.join(expected_emotions)}")

    # Makes sure all emotions are included
    for emotion in expected_emotions:
        if emotion not in response_dict:
            return IncorrectReturnDetails(IncorrectReturnTypes.IncorrectEmotions, f"The model returned incorrect emotions. Emotion was {emotion}. Correct emotions are {', '.join(expected_emotions)}")

    # Makes sure values are within the expected range
    for val in response_dict.values():
        if not (1 <= val <= 10):
            return IncorrectReturnDetails(IncorrectReturnTypes.IncorrectValueRange, f"The model returned an emotion value outside the range of 1-10. Value was {val}. It must return a value between 1 and 10 inclusive")

    return response_dict

def check_response_format(response: str) -> dict|IncorrectReturnDetails:
    """Checks a response string to make sure it is formatted correctly

    Arguments:
        response {str} -- Response to check

    Returns:
        dict|IncorrectReturnDetails -- Either dictionary or details about errors
    """
    # Means that the model decided the content should not be analyzed
    if response == "None":
        return IncorrectReturnDetails(IncorrectReturnTypes.NoReturn, "Model returned None")

    # Attempt to load the response as as dictionary
    try:
        response_dict = json.loads(response)
    except json.decoder.JSONDecodeError as e:
        print(str(e))
        return IncorrectReturnDetails(IncorrectReturnTypes.DecodeError, "Model returned an invalid formatted json response")

    # Check the content itself for correct formatting
    correct_content = check_response_content(response_dict)

    return correct_content

def save_results(results: list, filename: str):
    """Saves the results to the given filename as an ndjson file

    Arguments:
        results {list} -- Results to save
        filename {str} -- Filename to save to
    """
    with open(filename, "a") as f:
        for game in results:
            f.write(json.dumps(game))
            f.write("\n")

def perform_sentiment_analysis(model: AnalysisModel):
    """Performs analysis with the given model

    Arguments:
        model {AnalysisModel} -- Model to use
    """
    prompt_format = \
""" You will be given a text document to perform sentiment analysis on.
It will be 6 class analysis on the following emotions:
anger, disgust, fear, happiness, sadness, and surprise.
The emotion rating can be between 1 and 10. For instance, happiness of 10 means
that the description is very happy while 1 means there isn't much happiness at
all Please give the result in Json format.

Here is an example of a response:
{"anger" : 5, "disgust" : 1, "fear" : 8, "happiness" : 2, "sadness" : 10, "surprise" : 3}

If the text document contains sexual content, respond with None instead of a
sentiment analysis. Here is the text document:"""

    games_details_filename = "filtered_games.ndjson"
    games = []
    num_to_rate = np.inf
    with open(games_details_filename, "r") as f:
        # games = [json.loads(line) for line in f.readlines(num_to_grab)]
        i = 0
        for line in f:
            games.append(json.loads(line))
            i += 1
            if i >= num_to_rate:
                break

    # Number of games to be analyzed before saving them all to an ndjson file
    save_per_num_games = 50
    save_filename = "rated_games.ndjson"

    log_per_num_games = 10
    num_games = len(games)

    results = []
    # Go through each game and send the analysis request for it
    for i, game in enumerate(games):
        key_list = list(game.keys())
        id = key_list[0]
        game_data = game[id]["data"]

        # Get the description for the game
        if "detailed_description" not in game_data:
            print(f"No description found for this game: {game_data}")
            return None
        description = game_data["detailed_description"]

        # Format and send the description to the model
        query = f"{prompt_format}\n{description}"
        response = model.send_query(query)

        # Make sure the response is formatted correctly
        response = check_response_format(response)
        attempt_count = 1
        # Will allow the model to attempt analysis 3 times before failing out
        while isinstance(response, IncorrectReturnDetails):
            # If the model decided to not rate the mode, skip
            if response.type == IncorrectReturnTypes.NoReturn:
                print(f"Model decided to not rate the following game description: {description}")
                break
            model.send_query(f"There was something wrong with the response: {response.message}.\nPlease send the json response in the correct format.")
            attempt_count += 1
            if attempt_count > 3:
                raise Exception(f"The model failed multiple times to give a correctly formatted rating. Game Description: {description}\n\nQuery: {query}\n\nResult Info: {response.type}, {response.message}")

        # In the event that the model decided not to analyze the description
        if isinstance(response, IncorrectReturnDetails) and response.type == IncorrectReturnTypes.NoReturn:
            pass
        else:
            results.append({id : response})

        # Save the results every set number of requests
        if i % save_per_num_games == save_per_num_games - 1:
            print("Saving Games")
            save_results(results, save_filename)
            results.clear()

        # Log results every set number of requests
        if i % log_per_num_games == log_per_num_games - 1:
            print(f"Games Rated: {i}/{num_games} ({(i/num_games):.2%})", end="\r")

    save_results(results, save_filename)

if __name__ == "__main__":
    model = GptAnalyisModel()
    model.setup()
    model.model_type = "gpt-5-mini"
    perform_sentiment_analysis(model)