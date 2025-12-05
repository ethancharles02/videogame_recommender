from enum import Enum
from io import BytesIO
from PIL import Image, ImageTk
from random import choice, randint
from tkhtmlview import HTMLScrolledText, HTMLLabel
import os
import tkinter as tk
import urllib.request
import numpy as np

from .data_collection import load_json_file, write_json_to_file

def load_image_from_url(root: tk.Tk, url: str) -> ImageTk.PhotoImage:
    """Loads an image from the given URL

    Arguments:
        root {tk.Tk} -- Root to destroy in the case of an error
        url {str} -- URL to get image from

    Returns:
        ImageTk.PhotoImage -- Image
    """
    try:
        with urllib.request.urlopen(url) as u:
            raw_data = u.read()
    except Exception as e:
        print(f"Error fetching image: {e}")
        root.destroy()
        exit()

    im = Image.open(BytesIO(raw_data))

    photo = ImageTk.PhotoImage(im)
    return photo

sentiment_order = ["anger", "disgust", "fear", "happiness", "sadness", "surprise"]
def get_sentiment_vector(sentiment_dict: dict) -> np.ndarray:
    """Converts a sentiment dictionary into a numpy array

    Arguments:
        sentiment_dict {dict} -- Dictionary to convert

    Returns:
        np.ndarray -- Sentiment array
    """
    vec = np.zeros(shape=(1, len(sentiment_order)))
    for i in range(len(sentiment_order)):
        vec[i] = sentiment_dict[sentiment_order[i]]

    return vec

def get_sentiment_matrix(analyzed_game_data: dict) -> tuple[list[str], dict[str, int], np.ndarray]:
    """Converts the analyzed game data dictionary into a sentiment matrix where
    each row is a game

    Arguments:
        analyzed_game_data {dict} -- Game data to convert

    Returns:
        tuple[list[str], dict[str, int], np.ndarray] --
            The list of game ids,
            lookup dictionary of ID to indice for the array,
            the array itself
    """
    game_id_list = list(analyzed_game_data.keys())
    # Lookup dict for id to index in the matrix
    sentiment_ids = {}
    num_games = len(game_id_list)

    # Generates the empty matrix
    sentiment_matrix = np.zeros(shape=(num_games, len(sentiment_order)))

    # Fills in the matrix with the values
    for y in range(num_games):
        sentiment_ids[game_id_list[y]] = y
        for x in range(len(sentiment_order)):
            sentiment_matrix[y][x] = analyzed_game_data[game_id_list[y]][sentiment_order[x]]

    return game_id_list, sentiment_ids, sentiment_matrix
class GameRecommendationStatus(int, Enum):
    Played = 0
    NotPlayed = 1

class UserProfile:
    def __init__(self, name: str):
        """The user profile is used for storing a users preferred games

        Arguments:
            name {str} -- Name of the user
        """
        self._name: str = name
        # There could be setters added for game ratings such that it automatically
        # updates rated games and performs verification on attempts to add ratings
        # to the dict
        self._game_ratings: dict = {}
        self.default_filename: str = self._get_default_filename()
        self.rated_games = set()

    def _verify_game_rating(self, id: str, rating: list[GameRecommendationStatus, int]) -> bool:
        """Checks that a given game rating is valid

        Arguments:
            id {str} -- Game ID
            rating {list[GameRecommendationStatus, int]} -- Rating for the game

        Returns:
            bool -- Is valid
        """
        if not (isinstance(id, str) and isinstance(rating, list)):
            return False

        if len(rating) != 2:
            return False

        if not (0 <= rating[0] <= 1 and 0 <= rating[1] <= 10):
            return False

        return True

    def _verify_game_ratings(self, game_ratings: dict) -> bool:
        """Verifies a dictionary of game ratings to make sure they are valid

        Arguments:
            game_ratings {dict} -- Game ratings to validate

        Returns:
            bool -- Whether or not they are valid
        """
        for key in game_ratings.keys():
            value = game_ratings[key]

            if not self._verify_game_rating(key, value):
                return False

        return True

    def _get_default_filename(self) -> str:
        """Gets the default filename for saving/loading

        Returns:
            str -- Filename
        """
        return f"profile_{self.name}.json"

    def add_rating(self, id: str, rating: tuple[GameRecommendationStatus, int]):
        """Adds a rating to the rated games

        Arguments:
            id {str} -- ID of the game
            rating {tuple[GameRecommendationStatus, int]} -- Rating to add
        """
        if self._verify_game_rating(id, rating):
            self._game_ratings[id] = rating
            self.rated_games.add(id)
        else:
            print("Invalid id : rating pair was attempted to be added to rated games")

    def add_ratings(self, ratings: dict[str, tuple[GameRecommendationStatus, int]]):
        """Adds multiple user ratings from a dictionary

        Arguments:
            ratings {dict[str, tuple[GameRecommendationStatus, int]]} -- Ratings to add
        """
        for key in ratings.keys():
            value = ratings[key]
            self.add_rating(key, value)

    def load(self, filename: str = None):
        """Loads user ratings from a file

        Keyword Arguments:
            filename {str} -- File to load from (default: {None})
        """
        if filename is None:
            filename = self.default_filename

        if os.path.exists(filename):
            game_ratings = load_json_file(filename)
            self.add_ratings(game_ratings)

    def save(self, filename: str = None):
        """Saves user ratings to a file

        Keyword Arguments:
            filename {str} -- File to save to (default: {None})
        """
        if filename is None:
            filename = self.default_filename

        write_json_to_file(filename, self._game_ratings)

    def get_recommendation(self, game_ids: list[str], sentiment_indices: dict[str, int], sentiment_matrix: np.ndarray) -> str:
        """Gets a recommendation ID to display on the UI

        Arguments:
            game_ids {list[str]} -- List of possible game IDs
            sentiment_indices {dict[str, int]} -- Lookup dictionary for game ID
                to indice in the sentiment matrix
            sentiment_matrix {np.ndarray} -- Sentiment matrix to perform
                calculations on

        Raises:
            Exception: No recommendation was found

        Returns:
            str -- ID of game recommendation
        """
        recommendation_list = self._generate_recommendation_list(game_ids, sentiment_indices, sentiment_matrix)
        id = self._select_from_recommendation_list(recommendation_list, True)
        if id == -1:
            raise Exception("No valid game recommendation found")
        return id

    def _select_from_recommendation_list(self, recommendation_list: list[tuple[str, float]], is_exploratory: bool) -> str:
        """Selects an ID from the given recommendation list

        Arguments:
            recommendation_list {list[tuple[str, float]]} -- Sorted list of
                recommendations
            is_exploratory {bool} -- Whether or not it should randomly choose
                from a top percentage of recommendations instead of the very top

        Returns:
            str -- Game ID
        """
        num_recommendations = len(recommendation_list)
        indice = 0 if not is_exploratory else randint(0, num_recommendations // 30)

        return recommendation_list[indice][0]

    def _generate_recommendation_list(self, game_ids: list[str], sentiment_indices: dict[str, int], sentiment_matrix: np.ndarray) -> list[tuple[str, float]]:
        """Generates a sorted recommendation list with game IDs and scores

        Arguments:
            game_ids {list[str]} -- List of available game IDs
            sentiment_indices {dict[str, int]} -- Lookup dictionary from game ID
                to sentiment matrix row indice
            sentiment_matrix {np.ndarray} -- Sentiment matrix where each row is
                a game and columns are emotional ratings

        Returns:
            list[tuple[str, float]] -- Sorted list of Game IDs and Scores
        """
        recommendation_pool = {}
        for rated_id in self._game_ratings.keys():
            if rated_id not in self.rated_games:
                recommendation_pool[rated_id] = 0

        for rated_id in self._game_ratings.keys():
            rec_status, rating = self._game_ratings[rated_id]
            # Sets the multiplier for if the user played the game or not
            #   (playing the game is worth 10 times the weight)
            has_played_modifier = 10 if rec_status == GameRecommendationStatus.Played else 1

            # Gets the row for the given vector
            rated_vector = sentiment_matrix[sentiment_indices[rated_id]]
            similarities_vector = sentiment_matrix.dot(rated_vector) / (np.linalg.norm(sentiment_matrix, axis=1) * np.linalg.norm(rated_vector))

            # Sort them based on most similar
            top_similarities = np.argsort(similarities_vector)[::-1]
            sorted_ids = np.array(game_ids)[top_similarities]
            sorted_sims = similarities_vector[top_similarities]

            # Remove the existing game and get top 5 entries
            mask = (sorted_ids != rated_id) & (~np.isin(sorted_ids, list(self.rated_games)))
            filtered_ids = sorted_ids[mask]
            filtered_sims = sorted_sims[mask]

            # Add scores for all the games
            # num_games_to_add = len(filtered_ids)
            # Add scores for just the top # of similar games
            temp_num_games_to_add = 100
            num_games_to_add = temp_num_games_to_add if len(filtered_ids) >= temp_num_games_to_add else len(filtered_ids)
            for i in range(num_games_to_add):
                game_id = filtered_ids[i]
                # Sets a score for the game based on how similar it it, how much
                # the user liked it, and if they played it or not. The rating is
                # adjusted such that 4 or below becomes negative and detracts
                # from the overall score
                score = filtered_sims[i] * (rating - 5) * has_played_modifier
                if game_id in recommendation_pool:
                    recommendation_pool[game_id] += score
                else:
                    recommendation_pool[game_id] = score

        # Converts the dictionary to a sorted list
        recommendation_list = []
        for key in recommendation_pool.keys():
            recommendation_list.append((key, recommendation_pool[key]))
        recommendation_list.sort(key=lambda val: val[1], reverse=True)

        return recommendation_list

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self.default_filename = self._get_default_filename()

# Optimally, the UI elements would be separated into a different class like
# VideoGameRecommenderUI and that would handle all tk calls and formatting
class VideoGameRecommender:
    def __init__(self, root: tk.Tk,
                 analyzed_game_data: dict,
                 game_data: dict,
                 game_label: tk.Label,
                 image_label: tk.Label,
                 rating_label: HTMLLabel,
                 description_label: HTMLScrolledText,
                 genre_label: HTMLLabel,
                 users: dict[str, UserProfile] = {},
                 display_ratings: bool = False):
        """Videogame recommender that handles UI changes and getting game
        recommendations based on user preferences

        Arguments:
            root {tk.Tk} -- Tkinter root
            analyzed_game_data {dict} -- Game data with emotional ratings
            game_data {dict} -- Original game data
            game_label {tk.Label} -- Game name label to update
            image_label {tk.Label} -- Image label to update
            rating_label {HTMLLabel} -- Rating label to update
            description_label {HTMLScrolledText} -- Description label to update
            genre_label {HTMLLabel} -- Genre label to update

        Keyword Arguments:
            users {dict[str, UserProfile]} -- Dictionary of user names and
                profiles (default: {{}})
            display_ratings {bool} -- Whether or not emotional ratings should be
                displayed (meant for debugging) (default: {False})
        """
        self.root = root
        self.analyzed_game_data = analyzed_game_data
        self.game_id_list, self.sentiment_indices, self.sentiment_matrix = get_sentiment_matrix(self.analyzed_game_data)
        self.game_data = game_data
        self.game_label = game_label
        self.image_label = image_label
        self.rating_label = rating_label
        self.description_label = description_label
        self.genre_label = genre_label
        self.current_game_id = None
        self.game_ids: set = set(analyzed_game_data.keys())
        self.users: dict[str, UserProfile] = users
        self.display_ratings = display_ratings

        # Add a default user if one isn't found
        names = list(self.users.keys())
        if len(names) == 0:
            default_name = "default"
            default_user = UserProfile(default_name)
            # There is a safety check built into load in case there isn't an
            # existing profile at the file path
            default_user.load()
            self.users[default_name] = default_user
            self.current_user_name = default_name
        else:
            self.current_user_name: str = names[0]

        self.current_user = self.users[self.current_user_name]

    def get_new_game(self):
        """Gets a new game recommendation and updates the UI for that
        recommendation
        """
        # In the event the game was skipped, still add it to the rated games so
        # it doesn't show up again. (It will still show up in future reloads of
        # the recommender)
        if self.current_game_id is not None and self.current_game_id not in self.current_user.rated_games:
            self.current_user.rated_games.add(self.current_game_id)

        if len(self.current_user.rated_games) < 1:
        # if len(self.current_user.rated_games) < 5:
            available_ids = list(self.game_ids.difference(self.current_user.rated_games))
            self.current_game_id = choice(available_ids)
        else:
            self.current_game_id = self.current_user.get_recommendation(self.game_id_list, self.sentiment_indices, self.sentiment_matrix)
        # self.current_game_id = "48000"

        current_game_data = self.game_data[self.current_game_id]["data"]
        image_url = current_game_data["header_image"]

        self.game_label.configure(text=current_game_data["name"])

        photo = load_image_from_url(self.root, image_url)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

        if self.display_ratings:
            rating_str = str(self.analyzed_game_data[self.current_game_id])
            self.rating_label.set_html(rating_str)

        description = current_game_data["detailed_description"]
        self.description_label.set_html(description)

        genres = [genre["description"] for genre in current_game_data["genres"]]
        genre_str = "/".join(genres)
        self.genre_label.set_html(f"<u>{genre_str}</u>")

    def toggle(self, button: tk.Button):
        """Toggles the given button to be raised of sunken

        Arguments:
            button {tk.Button} -- Button to toggle
        """
        button.config(relief="raised" if button.config("relief")[-1]=="sunken" else "sunken")

    def submit(self, slider: tk.Scale, played_button: tk.Button):
        """Submits a rating and saves the user profile

        Arguments:
            slider {tk.Scale} -- Scale to get value from
            played_button {tk.Button} -- Button to identify if the user played
                the game
        """
        status = GameRecommendationStatus.Played if played_button.config("relief")[-1] == "sunken" else GameRecommendationStatus.NotPlayed
        self.current_user._game_ratings[self.current_game_id] = (status, slider.get())
        self.current_user.save()
        self.get_new_game()

def run_recommender():
    # Get the data for emotional ratings
    # ratings_filename = "temp_rated_games.json"
    ratings_filename = "rated_games.json"
    rating_data = load_json_file(ratings_filename)

    # Get the game data
    game_data_filename = "filtered_games.json"
    game_data = load_json_file(game_data_filename)

    root = tk.Tk()

    # Set up the grid for displaying the UI
    root.title("Video Game Recommender")
    root.rowconfigure(0, weight=3)
    root.rowconfigure(1, weight=0)
    root.rowconfigure(2, weight=2)
    root.rowconfigure(3, weight=0)
    root.rowconfigure(4, weight=0)
    root.rowconfigure(5, weight=0)
    root.rowconfigure(6, weight=0)
    root.rowconfigure(7, weight=0)
    root.rowconfigure(8, weight=0)
    for i in range(4):
        root.columnconfigure(i, weight=1)

    # Image label used for showing the main image for the game
    game_label = tk.Label(root, font=("Arial", 20, "bold"))
    game_label.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w")

    # Image label used for showing the main image for the game
    image_label = tk.Label(root)
    image_label.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Ratings listed for the game
    rating_label = HTMLLabel(root)
    rating_label.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    rating_label.configure(height=2)

    # Genres listed for the game
    genre_label = HTMLLabel(root)
    genre_label.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    genre_label.configure(height=2)

    # Description of the game
    description_label = HTMLScrolledText(root)
    description_label.configure(state="disabled")
    description_label.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Initialize the recommender and get a new recommendation
    recommender = VideoGameRecommender(root, rating_data, game_data, game_label, image_label, rating_label, description_label, genre_label, display_ratings=False)
    recommender.get_new_game()

    button_row = 5
    # Button used to indicate if the user has played the game before
    played_btn = tk.Button(root, text="I Have Played This Game")
    played_btn.configure(command=lambda b=played_btn: recommender.toggle(b))
    played_btn.grid(row=button_row, column=0, columnspan=4, padx=5, pady=5, sticky="ns")

    # Instructions related to using the slider
    instruction_label = tk.Label(root, text="Use the slider below to indicate how much you like this game (or think you would like it if you haven't played it)")
    instruction_label.grid(row=button_row + 1, column=0, columnspan=4, padx=5, pady=5, sticky="nswe")

    # Scale to indicate how much the user likes a game
    scale = tk.Scale(root, orient="horizontal", sliderlength=100, to=10)
    scale.grid(row=button_row + 2, column=0, columnspan=4, padx=5, pady=5, sticky="nswe")

    # Submits the users feedback
    submit_btn = tk.Button(root,
                           text="Submit",
                           command=lambda s=scale, b=played_btn: recommender.submit(s, b))
    submit_btn.grid(row=button_row + 3, column=2, columnspan=2, padx=5, pady=5, sticky="ns")

    # Skips to generate a new game recommendation
    skip_btn = tk.Button(root,
                           text="Skip",
                           command=recommender.get_new_game)
    skip_btn.grid(row=button_row + 3, column=0, columnspan=2, padx=5, pady=5, sticky="ns")

    root.mainloop()