from PySide6.QtWidgets import QStackedWidget
from .lobby import LobbyWidget
from .snake import SnakeGameWidget

class GameManager(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lobby = LobbyWidget()
        self.snake = SnakeGameWidget()
        self.addWidget(self.lobby)
        self.addWidget(self.snake)
        self.setCurrentWidget(self.lobby)
        # self.lobby.start_game.connect(self.launch_snake)
        # self.snake.back_to_lobby.connect(self.show_lobby)

    def launch_snake(self, pseudo):
        self.snake.set_player(pseudo)
        self.setCurrentWidget(self.snake)

    def show_lobby(self):
        self.setCurrentWidget(self.lobby)
