import os
import subprocess
from tkinter import ttk
from ttkbootstrap.constants import *

GAMES = [
    ("Pong", os.path.join("game", "Pong", "code", "main.py")),
    ("Platform", os.path.join("game", "Platform", "code", "main.py")),
    ("Monster battle", os.path.join("game", "Monster battle", "code", "main.py")),
    ("Vampire survivor", os.path.join("game", "Vampire survivor", "code", "main.py")),
    ("Space shooter", os.path.join("game", "space shooter", "main.py")),
]

def launch_game(game_path):
    # Lance le jeu dans un nouveau processus
    subprocess.Popen(["python3", game_path])

def build_games_tab(self, tab):
    shell = ttk.Frame(tab)
    shell.pack(fill="both", expand=True)
    shell.grid_columnconfigure(0, weight=1)

    card = ttk.Labelframe(shell, text="Jeux intégrés", style="Card.TLabelframe", bootstyle=PRIMARY)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    for idx, (game_name, game_path) in enumerate(GAMES):
        ttk.Button(
            card,
            text=f"Lancer {game_name}",
            bootstyle=SUCCESS,
            command=lambda p=game_path: launch_game(p),
        ).pack(fill="x", padx=10, pady=8)
