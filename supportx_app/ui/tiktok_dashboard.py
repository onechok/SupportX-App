from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import json
import os
from supportx_app.tiktok_process import start_tiktok_process


class TikTokDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tiktok_proc = None
        self.tiktok_queue = None
        self.is_connected = False
        self.events_log = []
        self.log_file = os.path.join(os.getcwd(), "tiktok_events.json")
        self.users_file = os.path.join(os.getcwd(), "tiktok_users.json")
        self.users = self.load_users()
        self.setLayout(QVBoxLayout())

        # Options sons + volume
        options_box = QGroupBox("Options sons")
        options_layout = QHBoxLayout(options_box)
        self.sound_chat_cb = QCheckBox("Son sur chat")
        self.sound_like_cb = QCheckBox("Son sur like")
        self.sound_gift_cb = QCheckBox("Son sur cadeau")
        options_layout.addWidget(self.sound_chat_cb)
        from PySide6.QtWidgets import QSlider
        self.sound_chat_vol = QSlider(Qt.Horizontal)
        self.sound_chat_vol.setRange(0, 100)
        self.sound_chat_vol.setValue(80)
        options_layout.addWidget(QLabel("Volume chat"))
        options_layout.addWidget(self.sound_chat_vol)
        options_layout.addWidget(self.sound_like_cb)
        self.sound_like_vol = QSlider(Qt.Horizontal)
        self.sound_like_vol.setRange(0, 100)
        self.sound_like_vol.setValue(80)
        options_layout.addWidget(QLabel("Volume like"))
        options_layout.addWidget(self.sound_like_vol)
        options_layout.addWidget(self.sound_gift_cb)
        self.sound_gift_vol = QSlider(Qt.Horizontal)
        self.sound_gift_vol.setRange(0, 100)
        self.sound_gift_vol.setValue(80)
        options_layout.addWidget(QLabel("Volume cadeau"))
        options_layout.addWidget(self.sound_gift_vol)
        self.layout().addWidget(options_box)

        # Connexion + gestion utilisateurs
        conn_box = QGroupBox("Connexion TikTok")
        conn_layout = QHBoxLayout(conn_box)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur TikTok")
        self.connect_btn = QPushButton("Connexion")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.status_label = QLabel("Déconnecté")
        # Liste utilisateurs favoris
        self.users_list = QListWidget()
        self.users_list.setMaximumWidth(180)
        self.users_list.addItems(self.users)
        self.users_list.itemDoubleClicked.connect(self.select_user)
        # Ajout/suppression utilisateur
        self.add_user_btn = QPushButton("Ajouter aux favoris")
        self.add_user_btn.clicked.connect(self.add_user)
        self.del_user_btn = QPushButton("Supprimer")
        self.del_user_btn.clicked.connect(self.delete_user)
        # Layout utilisateurs à gauche
        user_col = QVBoxLayout()
        user_col.addWidget(QLabel("Favoris :"))
        user_col.addWidget(self.users_list)
        user_col.addWidget(self.add_user_btn)
        user_col.addWidget(self.del_user_btn)
        user_col.addStretch(1)
        # Layout principal connexion à droite
        conn_right = QVBoxLayout()
        conn_right.addWidget(QLabel("Utilisateur :"))
        conn_right.addWidget(self.username_input)
        conn_right.addWidget(self.connect_btn)
        conn_right.addWidget(self.status_label)
        conn_right.addStretch(1)
        # Fusionne les deux colonnes
        conn_layout.addLayout(user_col)
        conn_layout.addLayout(conn_right)
        self.layout().addWidget(conn_box)

        # Chat
        chat_box = QGroupBox("Chat")
        chat_layout = QVBoxLayout(chat_box)
        self.chat_list = QListWidget()
        chat_layout.addWidget(self.chat_list)
        self.layout().addWidget(chat_box)

        # Likes
        like_box = QGroupBox("Likes")
        like_layout = QVBoxLayout(like_box)
        self.like_label = QLabel("Total likes : 0")
        self.like_users = QListWidget()
        like_layout.addWidget(self.like_label)
        like_layout.addWidget(self.like_users)
        self.layout().addWidget(like_box)

        # Cadeaux
        gift_box = QGroupBox("Cadeaux")
        gift_layout = QVBoxLayout(gift_box)
        self.gift_list = QListWidget()
        gift_layout.addWidget(self.gift_list)
        self.layout().addWidget(gift_box)

        # Sauvegarde
        save_btn = QPushButton("Enregistrer l'historique")
        save_btn.clicked.connect(self.save_events)
        self.layout().addWidget(save_btn)

        # Timer de rafraîchissement
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self.refresh_ui)

        self.total_likes = 0

        # Initialisation audio unique et robuste
        from PySide6.QtCore import QUrl
        self.player_chat = QMediaPlayer(self)
        self.audio_chat = QAudioOutput(self)
        self.player_chat.setAudioOutput(self.audio_chat)
        self.audio_chat.setVolume(self.sound_chat_vol.value() / 100)
        self.sound_chat_vol.valueChanged.connect(lambda v: self.audio_chat.setVolume(v / 100))

        self.player_like = QMediaPlayer(self)
        self.audio_like = QAudioOutput(self)
        self.player_like.setAudioOutput(self.audio_like)
        self.audio_like.setVolume(self.sound_like_vol.value() / 100)
        self.sound_like_vol.valueChanged.connect(lambda v: self.audio_like.setVolume(v / 100))

        self.player_gift = QMediaPlayer(self)
        self.audio_gift = QAudioOutput(self)
        self.player_gift.setAudioOutput(self.audio_gift)
        self.audio_gift.setVolume(self.sound_gift_vol.value() / 100)
        self.sound_gift_vol.valueChanged.connect(lambda v: self.audio_gift.setVolume(v / 100))

        def find_sound(prefix):
            sound_dir = os.path.join(os.getcwd(), "sound")
            path = os.path.join(sound_dir, prefix + ".wav")
            if os.path.isfile(path):
                return QUrl.fromLocalFile(path)
            test_path = os.path.join(sound_dir, "test.wav")
            if os.path.isfile(test_path):
                return QUrl.fromLocalFile(test_path)
            return None
        self._find_sound = find_sound


    def load_users(self):
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_users(self):
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_user(self):
        username = self.username_input.text().strip()
        if username and username not in self.users:
            self.users.append(username)
            self.users_list.addItem(username)
            self.save_users()

    def delete_user(self):
        selected = self.users_list.currentItem()
        if selected:
            username = selected.text()
            self.users = [u for u in self.users if u != username]
            self.users_list.takeItem(self.users_list.currentRow())
            self.save_users()

    def select_user(self, item):
        self.username_input.setText(item.text())
    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_api()
        else:
            self.disconnect_from_api()

    def connect_to_api(self):
        username = self.username_input.text().strip()
        if not username:
            self.status_label.setText("Erreur : nom d'utilisateur !")
            return
        self.tiktok_proc, self.tiktok_queue = start_tiktok_process(username)
        self.is_connected = True
        self.connect_btn.setText("Déconnexion")
        self.status_label.setText(f"Connecté à {username}")
        self.chat_list.clear()
        self.like_users.clear()
        self.gift_list.clear()
        self.total_likes = 0
        self.like_label.setText("Total likes : 0")
        self.events_log.clear()
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


    def refresh_ui(self):
        if self.tiktok_queue:
            while not self.tiktok_queue.empty():
                try:
                    event_type, user, content = self.tiktok_queue.get_nowait()
                    dt = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                    event = {"type": event_type, "user": user, "content": content, "datetime": dt}
                    self.events_log.append(event)
                    if event_type == "chat":
                        self.chat_list.addItem(QListWidgetItem(f"[{dt}] {user}: {content}"))
                        self.chat_list.scrollToBottom()
                        if self.sound_chat_cb.isChecked():
                            url = self._find_sound("chat")
                            if url:
                                self.player_chat.stop()
                                self.player_chat.setSource(url)
                                self.player_chat.play()
                                self.status_label.setText(f"Lecture son chat : {os.path.basename(url.toLocalFile())}")
                            else:
                                self.status_label.setText("Aucun fichier chat.wav ou test.wav trouvé")
                    elif event_type == "like":
                        self.total_likes += 1
                        self.like_label.setText(f"Total likes : {self.total_likes}")
                        self.like_users.addItem(QListWidgetItem(f"[{dt}] {user} ({content})"))
                        self.like_users.scrollToBottom()
                        if self.sound_like_cb.isChecked():
                            url = self._find_sound("like")
                            if url:
                                self.player_like.stop()
                                self.player_like.setSource(url)
                                self.player_like.play()
                                self.status_label.setText(f"Lecture son like : {os.path.basename(url.toLocalFile())}")
                            else:
                                self.status_label.setText("Aucun fichier like.wav ou test.wav trouvé")
                    elif event_type == "cadeau":
                        # user = "expediteur → destinataire"
                        if "→" in user:
                            from_user, to_user = [u.strip() for u in user.split("→", 1)]
                        else:
                            from_user, to_user = user, "?"
                        self.gift_list.addItem(QListWidgetItem(f"[{dt}] {from_user} a offert '{content}' à {to_user}"))
                        self.gift_list.scrollToBottom()
                        if self.sound_gift_cb.isChecked():
                            url = self._find_sound("gift")
                            if url:
                                self.player_gift.stop()
                                self.player_gift.setSource(url)
                                self.player_gift.play()
                                self.status_label.setText(f"Lecture son cadeau : {os.path.basename(url.toLocalFile())}")
                            else:
                                self.status_label.setText("Aucun fichier gift.wav ou test.wav trouvé")
                except Exception as e:
                    self.status_label.setText(f"Erreur audio : {e}")

    def save_events(self):
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self.events_log, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"Historique enregistré dans {self.log_file}")
        except Exception as e:
            self.status_label.setText(f"Erreur sauvegarde : {e}")

        # Chat
        chat_box = QGroupBox("Chat")
        chat_layout = QVBoxLayout(chat_box)
        self.chat_list = QListWidget()
        chat_layout.addWidget(self.chat_list)
        self.layout().addWidget(chat_box)

        # Likes
        like_box = QGroupBox("Likes")
        like_layout = QVBoxLayout(like_box)
        self.like_label = QLabel("Total likes : 0")
        self.like_users = QListWidget()
        like_layout.addWidget(self.like_label)
        like_layout.addWidget(self.like_users)
        self.layout().addWidget(like_box)

        # Cadeaux
        gift_box = QGroupBox("Cadeaux")
        gift_layout = QVBoxLayout(gift_box)
        self.gift_list = QListWidget()
        gift_layout.addWidget(self.gift_list)
        self.layout().addWidget(gift_box)

        # Sauvegarde
        save_btn = QPushButton("Enregistrer l'historique")
        save_btn.clicked.connect(self.save_events)
        self.layout().addWidget(save_btn)

        # Timer de rafraîchissement
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self.refresh_ui)

        self.total_likes = 0

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_api()
        else:
            self.disconnect_from_api()

    def connect_to_api(self):
        username = self.username_input.text().strip()
        if not username:
            self.status_label.setText("Erreur : nom d'utilisateur !")
            return
        self.tiktok_proc, self.tiktok_queue = start_tiktok_process(username)
        self.is_connected = True
        self.connect_btn.setText("Déconnexion")
        self.status_label.setText(f"Connecté à {username}")
        self.chat_list.clear()
        self.like_users.clear()
        self.gift_list.clear()
        self.total_likes = 0
        self.like_label.setText("Total likes : 0")
        self.events_log.clear()
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

    def refresh_ui(self):
        if self.tiktok_queue:
            while not self.tiktok_queue.empty():
                try:
                    event_type, user, content = self.tiktok_queue.get_nowait()
                    dt = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                    event = {"type": event_type, "user": user, "content": content, "datetime": dt}
                    self.events_log.append(event)
                    if event_type == "chat":
                        self.chat_list.addItem(QListWidgetItem(f"[{dt}] {user}: {content}"))
                    elif event_type == "like":
                        self.total_likes += 1
                        self.like_label.setText(f"Total likes : {self.total_likes}")
                        self.like_users.addItem(QListWidgetItem(f"[{dt}] {user} ({content})"))
                    elif event_type == "cadeau":
                        # user = "expediteur → destinataire"
                        if "→" in user:
                            from_user, to_user = [u.strip() for u in user.split("→", 1)]
                        else:
                            from_user, to_user = user, "?"
                        self.gift_list.addItem(QListWidgetItem(f"[{dt}] {from_user} a offert '{content}' à {to_user}"))
                except Exception:
                    pass

    def save_events(self):
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self.events_log, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"Historique enregistré dans {self.log_file}")
        except Exception as e:
            self.status_label.setText(f"Erreur sauvegarde : {e}")
