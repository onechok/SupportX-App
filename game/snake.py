
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QKeyEvent
import random

SPEED = 120  # ms

class SnakeGameWidget(QWidget):
    back_to_lobby = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 240)
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_step)
        self.base_grid_width = 20
        self.base_grid_height = 16
        self.pseudo = "Joueur"
        self._build_ui()
        self.reset_game()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.title = QLabel("Snake")
        self.title.setFont(QFont('Arial', 18, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # Conteneur central pour le jeu (remplit tout l'espace)
        self.game_container = QWidget()
        self.game_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.game_container, stretch=1)

        self.restart_btn = QPushButton("Rejouer")
        self.restart_btn.clicked.connect(self.reset_game)
        self.back_btn = QPushButton("Retour lobby")
        self.back_btn.clicked.connect(self.back_to_lobby.emit)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.restart_btn)
        btn_row.addWidget(self.back_btn)
        layout.addLayout(btn_row)

    def resizeEvent(self, event):
        self.setFocus()  # Toujours garder le focus pour le contrôle clavier
        super().resizeEvent(event)

    def set_player(self, pseudo):
        self.pseudo = pseudo
        self.update()

    def get_grid_size(self):
        grid_width = max(10, self.width() // 20)
        grid_height = max(10, self.height() // 20)
        cell_size = int(min(self.width() / grid_width, self.height() / grid_height))
        return grid_width, grid_height, cell_size

    def reset_game(self):
        grid_width, grid_height, _ = self.get_grid_size()
        self.snake = [QPoint(grid_width // 2, grid_height // 2)]
        self.direction = QPoint(1, 0)
        self.next_direction = QPoint(1, 0)
        self.spawn_food()
        self.score = 0
        self.game_over = False
        self.timer.start(SPEED)
        self.update()

    def spawn_food(self):
        grid_width, grid_height, _ = self.get_grid_size()
        while True:
            self.food = QPoint(random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
            if self.food not in self.snake:
                break

    def game_step(self):
        grid_width, grid_height, _ = self.get_grid_size()
        if self.game_over:
            self.timer.stop()
            return
        self.direction = self.next_direction
        new_head = self.snake[0] + self.direction
        # Check collisions
        if (new_head.x() < 0 or new_head.x() >= grid_width or
            new_head.y() < 0 or new_head.y() >= grid_height or
            new_head in self.snake):
            self.game_over = True
            self.update()
            return
        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()
        self.update()

    def paintEvent(self, event):
        grid_width, grid_height, cell_size = self.get_grid_size()
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        # Draw food
        painter.setBrush(QColor(0, 200, 0))
        painter.drawRect(self.food.x() * cell_size, self.food.y() * cell_size, cell_size, cell_size)
        # Draw snake
        painter.setBrush(QColor(200, 200, 0))
        for part in self.snake:
            painter.drawRect(part.x() * cell_size, part.y() * cell_size, cell_size, cell_size)
        # Draw score
        painter.setPen(QColor(255,255,255))
        painter.setFont(QFont('Arial', 12))
        painter.drawText(8, 18, f"{self.pseudo} | Score : {self.score}")
        if self.game_over:
            painter.setFont(QFont('Arial', 24, QFont.Bold))
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(self.rect(), Qt.AlignCenter, "GAME OVER\n[Entrée] pour rejouer")

    def keyPressEvent(self, event: QKeyEvent):
        if self.game_over and event.key() == Qt.Key_Return:
            self.reset_game()
            return
        if event.key() == Qt.Key_Up and self.direction != QPoint(0, 1):
            self.next_direction = QPoint(0, -1)
        elif event.key() == Qt.Key_Down and self.direction != QPoint(0, -1):
            self.next_direction = QPoint(0, 1)
        elif event.key() == Qt.Key_Left and self.direction != QPoint(1, 0):
            self.next_direction = QPoint(-1, 0)
        elif event.key() == Qt.Key_Right and self.direction != QPoint(-1, 0):
            self.next_direction = QPoint(1, 0)
