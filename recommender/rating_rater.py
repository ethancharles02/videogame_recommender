import tkinter as tk
from PIL import ImageTk
from random import choice
from tkhtmlview import HTMLScrolledText, HTMLLabel
import os

from .data_collection import load_json_file, write_json_to_file
from .recommender import load_image_from_url

class RatingRater:
    def __init__(self,
                 root: tk.Tk,
                 analyzed_game_data: dict,
                 game_data: dict,
                 image_label: tk.Label,
                 description_label: HTMLScrolledText,
                 rating_label: HTMLLabel):
        """Rating rater for use in getting human ratings for the model emotional
        analysis ratings

        Arguments:
            root {tk.Tk} -- Tk root object
            analyzed_game_data {dict} -- Game data that has the model emotional
                ratings
            game_data {dict} -- Game data the contains general game information
            image_label {tk.Label} -- Image label to update
            description_label {HTMLScrolledText} -- Description label to update
            rating_label {HTMLLabel} -- Rating label to update
        """
        self.game_dict = {}
        self.current_game_id = None
        self.analyzed_game_data = analyzed_game_data
        self.game_data = game_data
        self.game_ids = list(analyzed_game_data.keys())
        self.root = root
        self.image_label = image_label
        self.description_label = description_label
        self.rating_label = rating_label

    def get_new_game(self):
        """Gets a new game from the available list and updates the UI for it
        """
        self.current_game_id = choice(self.game_ids)
        self.game_ids.remove(self.current_game_id)
        current_game_data = self.game_data[self.current_game_id]["data"]
        image_url = current_game_data["header_image"]

        photo = load_image_from_url(image_url)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

        description = current_game_data["detailed_description"]
        self.description_label.set_html(description)

        rating_str = str(self.analyzed_game_data[self.current_game_id])
        self.rating_label.set_html(rating_str)

    def submit(self, slider: tk.Scale, num_games_rated_label: tk.Label):
        """Submits the human rating for the model given rating

        Arguments:
            slider {tk.Scale} -- Scale to get value from
            num_games_rated_label {tk.Label} -- Label to update for number of
                games rated
        """
        self.game_dict[self.current_game_id] = slider.get()
        num_games_rated_label.configure(text=len(self.game_dict.keys()))
        self.get_new_game()

    def load(self, filename: str):
        """Loads a saved file of ratings to the game dictionary

        Arguments:
            filename {str} -- File to load
        """
        if os.path.exists(filename):
            self.game_dict = load_json_file(filename)

    def save(self, filename: str):
        """Saves current human ratings to a file

        Arguments:
            filename {str} -- File to save to
        """
        write_json_to_file(filename, self.game_dict)

def run_rating_rater():
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
    for i in range(4):
        root.columnconfigure(i, weight=1)

    num_games_rated_label = tk.Label(root)
    num_games_rated_label.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w")

    # Image label used for showing the main image for the game
    image_label = tk.Label(root)
    image_label.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Ratings listed for the game
    rating_label = HTMLLabel(root)
    rating_label.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    rating_label.configure(height=2)

    # Description of the game
    description_label = HTMLScrolledText(root)
    description_label.configure(state="disabled")
    description_label.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    ratings_filename = "rating_ratings.json"
    # Initialize the recommender and get a new recommendation
    rater = RatingRater(root, rating_data, game_data, image_label, description_label, rating_label)
    rater.load(ratings_filename)
    rater.get_new_game()

    button_row = 4

    # Scale to indicate how much the user likes a game
    scale = tk.Scale(root, orient="horizontal", sliderlength=100, to=10)
    scale.grid(row=button_row, column=0, columnspan=4, padx=5, pady=5, sticky="nswe")

    # Submits the users feedback
    submit_btn = tk.Button(root,
                           text="Submit",
                           command=lambda s=scale, num_ratings_label=num_games_rated_label: rater.submit(s, num_ratings_label))
    submit_btn.grid(row=button_row + 1, column=0, columnspan=4, padx=5, pady=5, sticky="ns")

    save_btn = tk.Button(root,
                         text="Save",
                         command=lambda: rater.save(ratings_filename))
    save_btn.grid(row=button_row + 2, column=0, columnspan=4, padx=5, pady=5, sticky="ns")

    root.mainloop()