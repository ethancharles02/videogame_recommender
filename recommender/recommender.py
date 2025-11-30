import tkinter as tk
from PIL import Image, ImageTk
import urllib.request
from io import BytesIO
from enum import Enum
from random import choice
from tkhtmlview import HTMLScrolledText, HTMLLabel

from data_collection import load_json_file

def load_image_from_url(url: str) -> ImageTk.PhotoImage:
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

class GameRecommendationStatus(Enum):
    Played = 0
    NotPlayed = 1

class VideoGameRecommender:
    def __init__(self, games: dict, game_data: dict, image_label: tk.Label, description_label: HTMLScrolledText, genre_label: HTMLLabel):
        self.game_dict = {}
        self.current_game_id = None
        self.games = games
        self.game_data = game_data
        self.game_ids = list(games.keys())
        self.root = root
        self.image_label = image_label
        self.description_label = description_label
        self.genre_label = genre_label

    def get_new_game(self):
        self.current_game_id = choice(self.game_ids)
        self.game_ids.remove(self.current_game_id)
        current_game_data = self.game_data[self.current_game_id]["data"]
        image_url = current_game_data["header_image"]

        photo = load_image_from_url(image_url)
        self.update_image(photo)

        description = current_game_data["detailed_description"]
        self.update_description(description)

        genres = [genre["description"] for genre in current_game_data["genres"]]
        genre_str = "/".join(genres)
        self.update_genres(f"<u>{genre_str}</u>")

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
        self.game_dict[self.current_game_id] = (status, slider.get())
        self.get_new_game()

if __name__ == "__main__":
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

    # Image label used for showing the main image for the game
    image_label = tk.Label(root)
    image_label.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Genres listed for the game
    genre_label = HTMLLabel(root)
    genre_label.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    genre_label.configure(height=2)

    # Description of the game
    description_label = HTMLScrolledText(root)
    description_label.configure(state="disabled")
    description_label.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    # Initialize the recommender and get a new recommendation
    recommender = VideoGameRecommender(rating_data, game_data, image_label, description_label, genre_label)
    recommender.get_new_game()

    button_row = 3
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