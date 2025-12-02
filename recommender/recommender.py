from enum import Enum
from io import BytesIO
from PIL import Image, ImageTk
from random import choice
from tkhtmlview import HTMLScrolledText, HTMLLabel
import os
import tkinter as tk
import urllib.request

from .data_collection import load_json_file, write_json_to_file

def load_image_from_url(root: tk.Tk, url: str) -> ImageTk.PhotoImage:
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

class GameRecommendationStatus(int, Enum):
    Played = 0
    NotPlayed = 1

class UserProfile:
    def __init__(self, name: str):
        self._name: str = name
        # There could be setters added for game ratings such that it automatically
        # updates rated games and performs verification on attempts to add ratings
        # to the dict
        self._game_ratings: dict = {}
        self.default_filename: str = self._get_default_filename()
        self.rated_games = set()

    def _verify_game_rating(self, id: str, rating: list[GameRecommendationStatus, int]):
        if not (isinstance(id, str) and isinstance(rating, list)):
            return False

        if len(rating) != 2:
            return False

        if not (0 <= rating[0] <= 1 and 0 <= rating[1] <= 10):
            return False

        return True

    def _verify_game_ratings(self, game_ratings: dict) -> bool:
        for key in game_ratings.keys():
            value = game_ratings[key]

            if not self._verify_game_rating(key, value):
                return False

        return True

    def _get_default_filename(self):
        return f"profile_{self.name}.json"

    def add_rating(self, id: str, rating: tuple[GameRecommendationStatus, int]):
        if self._verify_game_rating(id, rating):
            self._game_ratings[id] = rating
            self.rated_games.add(id)
        else:
            print("Invalid id : rating pair was attempted to be added to rated games")

    def add_ratings(self, ratings: dict[str, tuple[GameRecommendationStatus, int]]):
        for key in ratings.keys():
            value = ratings[key]
            self.add_rating(key, value)

    def load(self, filename: str = None):
        if filename is None:
            filename = self.default_filename

        if os.path.exists(filename):
            game_ratings = load_json_file(filename)
            self.add_ratings(game_ratings)

    def save(self, filename: str = None):
        if filename is None:
            filename = self.default_filename

        write_json_to_file(filename, self._game_ratings)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self.default_filename = self._get_default_filename()

class VideoGameRecommender:
    def __init__(self, root: tk.Tk, games: dict, game_data: dict, game_label: tk.Label, image_label: tk.Label, description_label: HTMLScrolledText, genre_label: HTMLLabel, users: dict[str, UserProfile] = {}):
        self.root = root
        self.games = games
        self.game_data = game_data
        self.game_label = game_label
        self.image_label = image_label
        self.description_label = description_label
        self.genre_label = genre_label
        self.current_game_id = None
        self.game_ids: set = set(games.keys())
        self.users: dict[str, UserProfile] = users

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
        # In the event the game was skipped, still add it to the rated games so
        # it doesn't show up again. (It will still show up in future reloads of
        # the recommender)
        if self.current_game_id not in self.current_user.rated_games:
            self.current_user.rated_games.add(self.current_game_id)

        available_ids = self.game_ids.difference(self.current_user.rated_games)

        self.current_game_id = choice(list(available_ids))
        current_game_data = self.game_data[self.current_game_id]["data"]
        image_url = current_game_data["header_image"]

        self.update_game_label(current_game_data["name"])

        photo = load_image_from_url(self.root, image_url)
        self.update_image(photo)

        description = current_game_data["detailed_description"]
        self.update_description(description)

        genres = [genre["description"] for genre in current_game_data["genres"]]
        genre_str = "/".join(genres)
        self.update_genres(f"<u>{genre_str}</u>")

    def update_game_label(self, name: str):
        self.game_label.configure(text=name)

    def update_image(self, photo: ImageTk.PhotoImage):
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def update_description(self, description: str):
        self.description_label.set_html(description)

    def update_genres(self, genres: str):
        self.genre_label.set_html(genres)

    def toggle(self, button: tk.Button):
        button.config(relief="raised" if button.config("relief")[-1]=="sunken" else "sunken")

    def submit(self, slider: tk.Scale, played_button: tk.Button):
        status = GameRecommendationStatus.Played if played_button.config("relief")[-1] == "sunken" else GameRecommendationStatus.NotPlayed
        self.current_user._game_ratings[self.current_game_id] = (status, slider.get())
        self.current_user.save()
        self.get_new_game()

def run_recommender():
    # Get the data for emotional ratings
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
    for i in range(4):
        root.columnconfigure(i, weight=1)

    # Image label used for showing the main image for the game
    game_label = tk.Label(root, font=("Arial", 20, "bold"))
    game_label.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w")

    # Image label used for showing the main image for the game
    image_label = tk.Label(root)
    image_label.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Genres listed for the game
    genre_label = HTMLLabel(root)
    genre_label.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    genre_label.configure(height=2)

    # Description of the game
    description_label = HTMLScrolledText(root)
    description_label.configure(state="disabled")
    description_label.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Initialize the recommender and get a new recommendation
    recommender = VideoGameRecommender(root, rating_data, game_data, game_label, image_label, description_label, genre_label)
    recommender.get_new_game()

    button_row = 4
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