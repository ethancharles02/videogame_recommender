import tkinter as tk
from PIL import Image, ImageTk
import urllib.request
from io import BytesIO

from data_collection.json_utils import load_json_file

if __name__ == "__main__":
    ratings_filename = "rated_games.json"
    rating_data = load_json_file(ratings_filename)

    game_data_filename = "filtered_games.json"
    game_data = load_json_file(game_data_filename)