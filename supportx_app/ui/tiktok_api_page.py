
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime, QTimer
from supportx_app.tiktok_process import start_tiktok_process

class TikTokApiPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tiktok_proc = None
        self.tiktok_queue = None
        self.is_connected = False
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Barre de connexion
        conn_layout = QHBoxLayout()
        self.label = QLabel("Nom d'utilisateur TikTok :")
        conn_layout.addWidget(self.label)
        self.username_input = QLineEdit()
        conn_layout.addWidget(self.username_input)
        self.connect_btn = QPushButton("Connexion")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        self.layout.addLayout(conn_layout)

        # Statut
        self.status_label = QLabel("Déconnecté")
        self.layout.addWidget(self.status_label)

        # Tableau des événements
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Utilisateur",
            "Message Chat",
            "Nombre de Likes",
            "Nom du Cadeau",
            "Autre",
            "Date/Heure"
        ])
        self.layout.addWidget(self.table)

        # Timer pour rafraîchir l'UI si besoin
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self.refresh_ui)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_api()
        else:
            self.disconnect_from_api()

    def connect_to_api(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom d'utilisateur TikTok.")
            return
        self.tiktok_proc, self.tiktok_queue = start_tiktok_process(username)
        self.is_connected = True
        self.connect_btn.setText("Déconnexion")
        self.status_label.setText(f"Connecté à {username}")
        self.table.setRowCount(0)
        self.refresh_timer.start()

    def disconnect_from_api(self):
        if self.tiktok_proc:
            self.tiktok_proc.terminate()
            self.tiktok_proc = None
            self.tiktok_queue = None
        self.is_connected = False
        self.connect_btn.setText("Connexion")
        self.status_label.setText("Déconnecté")
        self.refresh_timer.stop()

    def handle_api_event(self, event_type, user, content):
        dt = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        if event_type == "like":
            self.add_api_event(user, "", str(content), "", "", dt)
        elif event_type == "chat":
            self.add_api_event(user, content, "", "", "", dt)
        elif event_type == "cadeau":
            self.add_api_event(user, "", "", content, "", dt)
        elif event_type == "error":
            self.add_api_event(user, "", "", "", content, dt)
        else:
            self.add_api_event(user, "", "", "", f"{event_type}: {content}", dt)

    def add_api_event(self, user, chat_msg, like_count, cadeau, other, date):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(user)))
        self.table.setItem(row, 1, QTableWidgetItem(str(chat_msg)))
        self.table.setItem(row, 2, QTableWidgetItem(str(like_count)))
        self.table.setItem(row, 3, QTableWidgetItem(str(cadeau)))
        self.table.setItem(row, 4, QTableWidgetItem(str(other)))
        self.table.setItem(row, 5, QTableWidgetItem(date))
        self.table.scrollToBottom()

    def refresh_ui(self):
        if self.tiktok_queue:
            while not self.tiktok_queue.empty():
                try:
                    event_type, user, content = self.tiktok_queue.get_nowait()
                    self.handle_api_event(event_type, user, content)
                except Exception:
                    pass
