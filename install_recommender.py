import PyInstaller.__main__

# You will also need to include filtered_games.json and rated_games.json in dist/
PyInstaller.__main__.run([
    "main_recommender.py",
    "--onefile",
    "--windowed"
])