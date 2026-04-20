from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class ClickerGameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 240)
        self.count = 0
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.title = QLabel("Clicker")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title)
        self.score_label = QLabel("Score : 0")
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        self.btn = QPushButton("Clique-moi !")
        self.btn.clicked.connect(self.increment)
        layout.addWidget(self.btn)
        self.reset_btn = QPushButton("Remise à zéro")
        self.reset_btn.clicked.connect(self.reset)
        layout.addWidget(self.reset_btn)

    def increment(self):
        self.count += 1
        self.score_label.setText(f"Score : {self.count}")

    def reset(self):
        self.count = 0
        self.score_label.setText("Score : 0")
