from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QComboBox
from PySide6.QtCore import Signal, Qt


class LobbyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("LobbyWidget")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        # Bloc lobby (sélection)
        self.lobby_widget = QWidget()
        lobby_layout = QVBoxLayout(self.lobby_widget)
        lobby_layout.setSpacing(20)
        lobby_layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel("Lobby du jeu")
        self.title.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.title.setAlignment(Qt.AlignCenter)
        lobby_layout.addWidget(self.title)

        self.pseudo_input = QLineEdit()
        self.pseudo_input.setPlaceholderText("Choisissez un pseudo...")
        lobby_layout.addWidget(self.pseudo_input)

        self.players_list = QListWidget()
        lobby_layout.addWidget(self.players_list)

        self.game_select = QComboBox()
        self.game_select.addItem("Snake")
        self.game_select.addItem("Clicker")
        self.game_select.addItem("Cube 3D")
        self.game_select.addItem("PyCraft")
        self.game_select.addItem("Pong")
        self.game_select.addItem("Platform")
        self.game_select.addItem("Monster battle")
        self.game_select.addItem("Vampire survivor")
        self.game_select.addItem("Space shooter")
        lobby_layout.addWidget(self.game_select)

        btn_row = QHBoxLayout()
        self.solo_btn = QPushButton("Jouer")
        btn_row.addWidget(self.solo_btn)
        lobby_layout.addLayout(btn_row)

        self.main_layout.addWidget(self.lobby_widget)

        # Widgets jeux (plein écran)
        from .snake import SnakeGameWidget
        from .clicker import ClickerGameWidget
        from .cube3d import Cube3DGameWidget
        self.snake_widget = SnakeGameWidget()
        self.clicker_widget = ClickerGameWidget()
        self.cube3d_widget = Cube3DGameWidget()
        self.snake_widget.hide()
        self.clicker_widget.hide()
        self.cube3d_widget.hide()
        self.main_layout.addWidget(self.snake_widget, stretch=1)
        self.main_layout.addWidget(self.clicker_widget, stretch=1)
        self.main_layout.addWidget(self.cube3d_widget, stretch=1)
        # PyCraft n'est pas un widget, il sera lancé en externe

        # Bouton retour lobby (affiché en mode jeu)
        self.back_btn = QPushButton("Retour lobby")
        self.back_btn.hide()
        self.back_btn.clicked.connect(self._show_lobby)
        self.main_layout.addWidget(self.back_btn)

        self.solo_btn.clicked.connect(self._start_game)
        self.game_select.currentIndexChanged.connect(self._on_game_changed)

    def set_players(self, players):
        self.players_list.clear()
        self.players_list.addItems(players)

    def _on_game_changed(self, idx):
        # Ne rien faire, l'affichage du jeu se fait uniquement après "Jouer"
        pass

    def _start_game(self):
        import subprocess, sys, os
        pseudo = self.pseudo_input.text().strip() or "Joueur"
        game = self.game_select.currentText()
        if game == "PyCraft":
            # Lancer PyCraft dans un nouveau processus (nom du module en minuscule)
            try:
                subprocess.Popen([sys.executable, '-m', 'pycraft'])
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Erreur PyCraft", f"Impossible de lancer PyCraft : {e}")
            return
        # Jeux externes (5games)
        external_games = {
            "Pong": os.path.join("game", "Pong", "code", "main.py"),
            "Platform": os.path.join("game", "Platform", "code", "main.py"),
            "Monster battle": os.path.join("game", "Monster battle", "code", "main.py"),
            "Vampire survivor": os.path.join("game", "Vampire survivor", "code", "main.py"),
            "Space shooter": os.path.join("game", "space shooter", "main.py"),
        }
        if game in external_games:
            try:
                subprocess.Popen([sys.executable, external_games[game]])
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, f"Erreur {game}", f"Impossible de lancer {game} : {e}")
            return
        self.lobby_widget.hide()
        self.back_btn.show()
        # Masquer tous les jeux
        self.snake_widget.hide()
        self.clicker_widget.hide()
        self.cube3d_widget.hide()
        if game == "Snake":
            self.snake_widget.set_player(pseudo)
            self.snake_widget.reset_game()
            self.snake_widget.show()
        elif game == "Clicker":
            self.clicker_widget.reset()
            self.clicker_widget.show()
        elif game == "Cube 3D":
            self.cube3d_widget.show()
    def _show_lobby(self):
        self.lobby_widget.show()
        self.back_btn.hide()
        self.snake_widget.hide()
        self.clicker_widget.hide()

    def set_players(self, players):
        self.players_list.clear()
        self.players_list.addItems(players)

    def _start_solo(self):
        pseudo = self.pseudo_input.text().strip() or "Joueur"
        self.start_game.emit(pseudo)

    def _start_multi(self):
        pseudo = self.pseudo_input.text().strip() or "Joueur"
        # Pour l'instant, démarre comme solo
        self.start_game.emit(pseudo)
