# Onglet TikTok Connector (PySide6) - Version Dark Dashboard
# Ce module crée un nouvel onglet pour l'UI SupportX, communique avec le backend Node.js via WebSocket

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, 
                               QTabWidget, QHeaderView, QFrame, QSplitter, QGridLayout,
                               QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QIcon
from PySide6.QtMultimedia import QSoundEffect
from pathlib import Path
import websocket
import threading
import json
from datetime import datetime

class TikTokConnectorClient(QThread):
    event_received = Signal(str, dict)
    connected = Signal()
    disconnected = Signal()
    error = Signal(str)
    ready = Signal()

    def __init__(self, url="ws://localhost:8765"):
        super().__init__()
        self.url = url
        self.ws = None
        self.running = False

    def run(self):
        def on_message(ws, message):
            try:
                msg = json.loads(message)
                if msg['type'] == 'ready':
                    self.ready.emit()
                elif msg['type'] == 'connected':
                    self.connected.emit()
                elif msg['type'] == 'disconnected':
                    self.disconnected.emit()
                elif msg['type'] == 'error':
                    self.error.emit(str(msg['data']))
                else:
                    self.event_received.emit(msg['type'], msg['data'])
            except Exception as e:
                self.error.emit(str(e))

        def on_error(ws, error):
            self.error.emit(str(error))

        def on_close(ws, close_status_code, close_msg):
            self.disconnected.emit()

        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)
        self.running = True
        self.ws.run_forever()

    def send(self, msg):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(msg))

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

class StatsCard(QFrame):
    """Carte de statistiques moderne dark"""
    def __init__(self, title, icon="📊", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.value = "0"
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setMinimumHeight(100)
        self.setStyleSheet("""
            StatsCard {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Header avec icône et titre
        header_layout = QHBoxLayout()
        self.icon_label = QLabel(self.icon)
        self.icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-weight: bold; color: #a0a0a0; background: transparent; font-size: 12px;")
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Valeur
        self.value_label = QLabel(self.value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #00a8ff; background: transparent;")
        
        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        
    def set_value(self, value):
        self.value = str(value)
        self.value_label.setText(self.value)
        
        # Animation de clignotement
        original_style = self.value_label.styleSheet()
        self.value_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #00ff88; background: transparent;")
        QTimer.singleShot(200, lambda: self.value_label.setStyleSheet(original_style))

class TikTokConnectorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = TikTokConnectorClient()
        self.stats = {"viewers": 0, "likes": 0, "gifts": 0, "messages": 0}
        self._init_sounds()
        self.init_ui()
        self.connect_signals()
        self.client.start()

    def _init_sounds(self):
        base = Path(__file__).parent.parent.parent / "sound" / "tiktok_connector"
        self.sounds = {}
        def load_sound(name, filename):
            path = base / filename
            effect = QSoundEffect()
            effect.setSource(path.as_uri() if path.exists() else "")
            effect.setVolume(0.7)
            self.sounds[name] = effect
        load_sound("chat", "chat_message.wav")
        load_sound("gift", "gift_received.wav")
        load_sound("member", "member_joined.wav")
        load_sound("like", "like_received.wav")
        
    def play_sound(self, name):
        effect = self.sounds.get(name)
        if effect and effect.source().isValid():
            effect.play()

    def init_ui(self):
        # Style principal dark moderne
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5d60;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #7f8c8d;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #2d2d2d;
                color: #e0e0e0;
                selection-background-color: #0d7377;
            }
            QLineEdit:focus {
                border-color: #00a8ff;
            }
            QLineEdit::placeholder {
                color: #7f8c8d;
            }
            QTextEdit {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #2d2d2d;
                color: #e0e0e0;
                font-family: monospace;
            }
            QTableWidget {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #2d2d2d;
                alternate-background-color: #252525;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0d7377;
                color: white;
            }
            QHeaderView::section {
                background-color: #0d7377;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #252525;
                color: #a0a0a0;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
                color: #e0e0e0;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #0d7377;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #14a085;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QSplitter::handle {
                background-color: #3d3d3d;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== Header avec connexion ==========
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Titre du dashboard
        title_label = QLabel("🎬 TikTok Live Dashboard")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00a8ff; background: transparent;")
        
        # Zone de connexion
        conn_widget = QWidget()
        conn_widget.setStyleSheet("background: transparent;")
        conn_layout = QHBoxLayout(conn_widget)
        conn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur TikTok")
        self.username_input.setMinimumWidth(200)
        
        self.connect_btn = QPushButton("🔗 Connecter")
        self.disconnect_btn = QPushButton("⛔ Déconnecter")
        self.disconnect_btn.setEnabled(False)
        
        conn_layout.addWidget(QLabel("@"))
        conn_layout.addWidget(self.username_input)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addWidget(self.disconnect_btn)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(conn_widget)
        
        main_layout.addWidget(header_frame)
        
        # ========== Section Statistiques (Grid de cartes) ==========
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: transparent;")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(15)
        
        # Création des cartes de statistiques
        self.stats_cards = {
            "viewers": StatsCard("Spectateurs", "👥"),
            "likes": StatsCard("Likes", "❤️"),
            "gifts": StatsCard("Cadeaux", "🎁"),
            "messages": StatsCard("Messages", "💬")
        }
        
        stats_layout.addWidget(self.stats_cards["viewers"], 0, 0)
        stats_layout.addWidget(self.stats_cards["likes"], 0, 1)
        stats_layout.addWidget(self.stats_cards["gifts"], 0, 2)
        stats_layout.addWidget(self.stats_cards["messages"], 0, 3)
        
        main_layout.addWidget(stats_frame)
        
        # ========== Splitter principal ==========
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setHandleWidth(5)
        
        # Section Logs
        logs_frame = QFrame()
        logs_layout = QVBoxLayout(logs_frame)
        
        logs_header = QLabel("📝 Journal des événements")
        logs_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #00a8ff;")
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(150)
        
        logs_layout.addWidget(logs_header)
        logs_layout.addWidget(self.log_box)
        
        # Section Chat & Gifts (Tabs)
        tabs_frame = QFrame()
        tabs_frame.setStyleSheet("background: transparent;")
        tabs_layout = QVBoxLayout(tabs_frame)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        
        # Onglet Chat
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        self.chat_table = QTableWidget(0, 3)
        self.chat_table.setHorizontalHeaderLabels(["👤 Utilisateur", "💬 Message", "🕐 Heure"])
        self.chat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chat_table.setAlternatingRowColors(True)
        chat_layout.addWidget(self.chat_table)
        self.tab_widget.addTab(chat_widget, "💬 Chat en direct")
        
        # Onglet Cadeaux
        gift_widget = QWidget()
        gift_layout = QVBoxLayout(gift_widget)
        self.gift_table = QTableWidget(0, 4)
        self.gift_table.setHorizontalHeaderLabels(["👤 Utilisateur", "🎁 Cadeau", "🔢 Quantité", "🕐 Heure"])
        self.gift_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.gift_table.setAlternatingRowColors(True)
        gift_layout.addWidget(self.gift_table)
        self.tab_widget.addTab(gift_widget, "🎁 Cadeaux reçus")
        
        tabs_layout.addWidget(self.tab_widget)
        
        # Ajout des sections au splitter
        main_splitter.addWidget(logs_frame)
        main_splitter.addWidget(tabs_frame)
        
        # Ajustement des proportions
        main_splitter.setSizes([200, 600])
        
        main_layout.addWidget(main_splitter)
        
        # ========== Section Envoi de message ==========
        send_frame = QFrame()
        send_layout = QHBoxLayout(send_frame)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Écrire un message...")
        self.send_btn = QPushButton("📤 Envoyer")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
            }
            QPushButton:hover {
                background-color: #0097e6;
            }
            QPushButton:pressed {
                background-color: #0086cc;
            }
        """)
        
        send_layout.addWidget(self.message_input)
        send_layout.addWidget(self.send_btn)
        
        main_layout.addWidget(send_frame)
        
        # Status bar
        self.status_label = QLabel("⚫ Déconnecté")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px; background: transparent;")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)

    def connect_signals(self):
        self.connect_btn.clicked.connect(self.on_connect)
        self.disconnect_btn.clicked.connect(self.on_disconnect)
        self.send_btn.clicked.connect(self.on_send)
        self.message_input.returnPressed.connect(self.on_send)
        
        self.client.event_received.connect(self.on_event)
        self.client.connected.connect(self.on_ws_connected)
        self.client.disconnected.connect(self.on_ws_disconnected)
        self.client.error.connect(self.on_ws_error)
        self.client.ready.connect(self.on_ws_ready)

    def on_ws_connected(self):
        self.log_box.append("<span style='color: #00ff88;'>✅ Connecté au serveur WebSocket !</span>")
        self.status_label.setText("🟢 Connecté au serveur")
        self.status_label.setStyleSheet("color: #00ff88; padding: 5px; background: transparent;")
        
    def on_ws_disconnected(self):
        self.log_box.append("<span style='color: #ff4444;'>⚠️ Déconnecté du serveur.</span>")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_label.setText("🔴 Déconnecté")
        self.status_label.setStyleSheet("color: #ff4444; padding: 5px; background: transparent;")
        
    def on_ws_error(self, error):
        self.log_box.append(f"<span style='color: #ff4444;'>❌ Erreur: {error}</span>")
        
    def on_ws_ready(self):
        self.log_box.append("<span style='color: #00a8ff;'>🎯 Serveur WebSocket prêt.</span>")

    def on_connect(self):
        username = self.username_input.text().strip()
        if username:
            self.log_box.append(f"🔌 Connexion à @{username}...")
            self.client.send({"type": "connect", "username": username})
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.status_label.setText("🟡 Connexion en cours...")
            self.status_label.setStyleSheet("color: #ffaa00; padding: 5px; background: transparent;")
        else:
            self.log_box.append("<span style='color: #ff4444;'>⚠️ Veuillez entrer un nom d'utilisateur</span>")

    def on_disconnect(self):
        self.client.send({"type": "disconnect"})
        self.log_box.append("🔌 Déconnexion demandée...")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    def on_send(self):
        msg = self.message_input.text().strip()
        if msg:
            self.client.send({"type": "sendMessage", "content": msg})
            self.message_input.clear()
            self.log_box.append(f"💬 Message envoyé: {msg}")

    def update_stats(self, stat_type, value=None):
        if stat_type in self.stats_cards:
            if value is not None:
                self.stats_cards[stat_type].set_value(value)
                self.stats[stat_type] = value
            else:
                self.stats[stat_type] += 1
                self.stats_cards[stat_type].set_value(self.stats[stat_type])

    def on_event(self, event_type, data):
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if event_type == "chat":
            user = data.get("user", {}).get("uniqueId", "?")
            comment = data.get("comment", "")
            row = self.chat_table.rowCount()
            self.chat_table.insertRow(row)
            self.chat_table.setItem(row, 0, QTableWidgetItem(user))
            self.chat_table.setItem(row, 1, QTableWidgetItem(comment))
            self.chat_table.setItem(row, 2, QTableWidgetItem(current_time))
            self.chat_table.scrollToBottom()
            self.play_sound("chat")
            self.update_stats("messages")
            self.log_box.append(f"💬 [{current_time}] <span style='color: #00a8ff;'><b>{user}</b></span>: {comment}")
            
        elif event_type == "gift":
            user = data.get("user", {}).get("uniqueId", "?")
            gift = data.get("giftDetails", {}).get("giftName", "?")
            count = data.get("repeatCount", 1)
            row = self.gift_table.rowCount()
            self.gift_table.insertRow(row)
            self.gift_table.setItem(row, 0, QTableWidgetItem(user))
            self.gift_table.setItem(row, 1, QTableWidgetItem(gift))
            self.gift_table.setItem(row, 2, QTableWidgetItem(str(count)))
            self.gift_table.setItem(row, 3, QTableWidgetItem(current_time))
            self.gift_table.scrollToBottom()
            self.play_sound("gift")
            self.update_stats("gifts")
            self.log_box.append(f"🎁 [{current_time}] <span style='color: #ffaa00;'><b>{user}</b></span> a offert {gift} x{count}!")
            
        elif event_type == "member":
            user = data.get("user", {}).get("uniqueId", "?")
            self.play_sound("member")
            self.log_box.append(f"👤 [{current_time}] <span style='color: #00ff88;'><b>{user}</b></span> a rejoint le live")
            self.update_stats("viewers")
            
        elif event_type == "like":
            user = data.get("user", {}).get("uniqueId", "?")
            count = data.get("likeCount", 1)
            self.play_sound("like")
            for _ in range(min(count, 5)):
                self.update_stats("likes")
            self.log_box.append(f"❤️ [{current_time}] <span style='color: #ff6b6b;'><b>{user}</b></span> a aimé x{count}")
            
        elif event_type == "roomUser":
            viewers = data.get("viewerCount", 0)
            self.update_stats("viewers", viewers)
            self.log_box.append(f"👥 [{current_time}] Spectateurs actuels: <span style='color: #00a8ff;'>{viewers}</span>")
            
        elif event_type == "connected":
            self.log_box.append("<span style='color: #00ff88;'>✅ Connecté au live !</span>")
            self.status_label.setText("🟢 En live - Connecté")
            self.status_label.setStyleSheet("color: #00ff88; padding: 5px; background: transparent; font-weight: bold;")
            
        elif event_type == "disconnected":
            self.log_box.append("<span style='color: #ff4444;'>⚠️ Déconnecté du live.</span>")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.status_label.setText("🔴 Déconnecté")
            self.status_label.setStyleSheet("color: #ff4444; padding: 5px; background: transparent;")
            
        elif event_type == "error":
            self.log_box.append(f"<span style='color: #ff4444;'>❌ Erreur: {data}</span>")
        else:
            self.log_box.append(f"ℹ️ [{current_time}] Event {event_type}: {data}")

    def closeEvent(self, event):
        """Fermeture propre de la connexion"""
        if self.client:
            self.client.stop()
            self.client.quit()
            self.client.wait()
        event.accept()