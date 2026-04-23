
from __future__ import annotations
    
import os
import platform
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import requests

from PySide6.QtCore import QObject, QEvent, QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Ajout de la page TikTokApiPage
from supportx_app.ui.tiktok_api_page import TikTokApiPage
from supportx_app.ui.tiktok_dashboard import TikTokDashboard
from supportx_app.ui.anydesk_3d import Anydesk3DWidget

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    from ..config import AppConfig, normalize_url
    from ..startup import set_startup
    from ..theme import stylesheet_for
    from ..updates import UpdateInfo, UpdateService
    from ..web.overlay_view import OverlayWebView
    from ..youtube import YouTubeDownloadManager
except ImportError:
    from supportx_app.config import AppConfig, normalize_url
    from supportx_app.startup import set_startup
    from supportx_app.theme import stylesheet_for
    from supportx_app.updates import UpdateInfo, UpdateService
    from supportx_app.web.overlay_view import OverlayWebView
    from supportx_app.youtube import YouTubeDownloadManager


class UpdateCheckBridge(QObject):
    completed = Signal(bool, object, object)


class MainWindow(QMainWindow):
    def _build_diagnostic_page(self) -> QWidget:
        from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit, QWidget
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.diagnostic_output = QTextEdit()
        self.diagnostic_output.setReadOnly(True)
        run_btn = QPushButton("Lancer le diagnostic complet")
        run_btn.clicked.connect(self._run_diagnostic_cli)
        layout.addWidget(run_btn)
        layout.addWidget(self.diagnostic_output, 1)
        return page

    def _run_diagnostic_cli(self):
        import subprocess
        import sys
        self.diagnostic_output.clear()
        try:
            proc = subprocess.Popen([
                sys.executable, "-m", "diagnostic_tool.batch", "--batch"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(self.app_dir))
            for line in iter(proc.stdout.readline, b""):
                if not line:
                    break
                self.diagnostic_output.append(line.decode(errors="replace"))
        except Exception as exc:
            self.diagnostic_output.append(f"Erreur lors du lancement du diagnostic : {exc}")

    def __init__(self, app_dir: Path) -> None:
        super().__init__()
        self.app_dir = app_dir
        self._tray_enabled = False
        self._force_close = False
        self.config_path = app_dir / "config.json"
        self.config = AppConfig.load(self.config_path)
        self._pending_update: UpdateInfo | None = None
        self._update_check_in_progress = False
        self._update_check_bridge = UpdateCheckBridge(self)
        self._update_check_bridge.completed.connect(self._on_update_check_finished)
        self.youtube_manager = YouTubeDownloadManager(self)

        self.youtube_manager.task_created.connect(self._on_youtube_task_created)
        self.youtube_manager.task_updated.connect(self._on_youtube_task_updated)
        self.youtube_manager.task_removed.connect(self._on_youtube_task_removed)
        self.youtube_manager.task_log.connect(self._on_youtube_task_log)
        self.youtube_manager.availability_changed.connect(self._on_youtube_availability_changed)

        self.setWindowTitle(f"{self.config.app_name} - v{self.config.app_version}")
        self.resize(1360, 840)
        self.setMinimumSize(1100, 720)

        self._build_ui()
        self.apply_theme(self.config.theme)

        if self.config.auto_update:
            QTimer.singleShot(1200, lambda: self.check_for_updates(manual=False))

    def set_tray_enabled(self, enabled: bool) -> None:
        self._tray_enabled = bool(enabled)

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.status.showMessage("Application restauree")

    def hide_to_tray(self) -> None:
        self.hide()
        self.status.showMessage("Application active en arriere-plan")

    def request_quit(self) -> None:
        self._force_close = True
        QApplication.instance().quit()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if getattr(self, "_tray_enabled", False) and self.isMinimized():
                QTimer.singleShot(0, self.hide_to_tray)

    def closeEvent(self, event) -> None:
        if getattr(self, "_tray_enabled", False) and not getattr(self, "_force_close", False):
            self.hide_to_tray()
            event.ignore()
            return
        super().closeEvent(event)

    def _build_ui(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")

        from game.manager import GameManager
        self.web_page = self._build_web_page()
        self.anydesk_page = self._build_anydesk_page()
        self.youtube_page = self._build_youtube_page()
        self.game_page = GameManager()
        self.diagnostic_page = self._build_diagnostic_page()
        self.settings_page = self._build_settings_page()
        self.about_page = self._build_about_page()
        self.tiktok_api_page = TikTokApiPage()
        self.tiktok_dashboard = TikTokDashboard()
        from supportx_app.ui.tiktok_connector_tab import TikTokConnectorTab
        self.tiktok_connector_tab = TikTokConnectorTab()

        self.stack.addWidget(self.web_page)
        self.stack.addWidget(self.anydesk_page)
        self.stack.addWidget(self.youtube_page)
        self.stack.addWidget(self.game_page)
        self.stack.addWidget(self.diagnostic_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.about_page)
        self.stack.addWidget(self.tiktok_api_page)
        self.stack.addWidget(self.tiktok_dashboard)
        self.stack.addWidget(self.tiktok_connector_tab)
        content_layout.addWidget(self.stack, 1)


        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self.menuBar().hide()
        self.status.showMessage(f"Pret • {self.config.app_name} • Version {self.config.app_version}")
        self._set_active_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        app_title = QLabel(self.config.app_name)
        app_title.setObjectName("sidebarTitle")
        app_version = QLabel(f"v{self.config.app_version}")
        app_version.setObjectName("sidebarSubtitle")
        layout.addWidget(app_title)
        layout.addWidget(app_version)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)



        sidebar_labels = [
            "SupportX Web",
            "AnyDesk",
            "YouTube",
            "Jeux",
            "Diagnostic",
            "Parametres",
            "A propos",
            "TikTok API",
            "TikTok Dashboard",
            "TikTok Connector"
        ]
        for index, label in enumerate(sidebar_labels):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked=False, i=index: self._set_active_page(i))
            self.nav_group.addButton(btn, index)
            layout.addWidget(btn)

        layout.addStretch(1)

        quick_open = QPushButton("Ouvrir dans le navigateur")
        quick_open.setObjectName("secondaryButton")
        quick_open.clicked.connect(self.open_in_browser)
        layout.addWidget(quick_open)
        return sidebar

    def _set_active_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _build_web_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web_widget = OverlayWebView(self.config.supportx_url, self.status.showMessage)
        layout.addWidget(self.web_widget)
        return page

    def _build_anydesk_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        # Bloc info
        info_card = self._card("Installation AnyDesk")
        info = info_card.layout()
        info_text = QLabel(
            "Téléchargez puis installez AnyDesk directement depuis cette page. "
            "Le mode d'installation est adapté automatiquement à votre système."
        )
        info_text.setWordWrap(True)
        info_text.setObjectName("cardHeadline")
        info.addWidget(info_text)

        self.anydesk_status = QLabel("Statut: prêt")
        self.anydesk_status.setWordWrap(True)
        self.anydesk_status.setObjectName("mutedLabel")
        info.addWidget(self.anydesk_status)

        # Bloc actions
        actions_card = self._card("Actions")
        actions = actions_card.layout()

        btn_download = QPushButton("Télécharger AnyDesk")
        btn_download.clicked.connect(self.download_anydesk)

        self.btn_install_anydesk = QPushButton("Installer AnyDesk")
        self.btn_install_anydesk.clicked.connect(self.install_anydesk)

        btn_open_site = QPushButton("Ouvrir le site officiel")
        btn_open_site.clicked.connect(lambda: webbrowser.open("https://anydesk.com/fr/downloads"))

        actions.addWidget(btn_download)
        actions.addWidget(self.btn_install_anydesk)
        actions.addWidget(btn_open_site)


        layout.addWidget(info_card, 0, 0)
        layout.addWidget(actions_card, 0, 1)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 3)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        appearance = self._card("Apparence")
        ap = appearance.layout()
        ap.addWidget(QLabel("Mode de theme"))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        self.theme_combo.setCurrentText(self.config.theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        ap.addWidget(self.theme_combo)

        updates = self._card("Mises a jour")
        up = updates.layout()
        self.start_with_system_check = QCheckBox("Lancer l'application au demarrage du systeme")
        self.start_with_system_check.setChecked(self.config.start_with_system)
        self.start_with_system_check.toggled.connect(self.save_startup_setting)

        self.auto_update_check = QCheckBox("Verifier automatiquement les mises a jour")
        self.auto_update_check.setChecked(self.config.auto_update)
        self.auto_update_check.toggled.connect(self.save_auto_update_setting)

        self.simulate_check = QCheckBox("Activer le mode simulation")
        self.simulate_check.setChecked(self.config.simulate_updates)
        self.simulate_check.toggled.connect(self.save_simulate_setting)

        self.check_update_btn = QPushButton("Verifier maintenant")
        self.check_update_btn.clicked.connect(lambda: self.check_for_updates(manual=True))

        self.install_update_btn = QPushButton("Installer la mise a jour")
        self.install_update_btn.setEnabled(False)
        self.install_update_btn.clicked.connect(self.install_pending_update)

        up.addWidget(self.start_with_system_check)
        up.addWidget(self.auto_update_check)
        up.addWidget(self.simulate_check)
        up.addWidget(self.check_update_btn)
        up.addWidget(self.install_update_btn)

        self.update_status_label = QLabel("Derniere verification: jamais")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setObjectName("mutedLabel")
        up.addWidget(self.update_status_label)

        actions = self._card("Navigation Web")
        ac = actions.layout()
        web_reload = QPushButton("Recharger SupportX")
        web_reload.clicked.connect(self.web_widget.web.reload)
        open_external = QPushButton("Ouvrir page courante dans le navigateur")
        open_external.clicked.connect(self.web_widget.open_external)
        ac.addWidget(web_reload)
        ac.addWidget(open_external)

        layout.addWidget(appearance, 0, 0)
        layout.addWidget(updates, 0, 1)
        layout.addWidget(actions, 1, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return page

    def _build_youtube_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        controls = self._card("Telechargement YouTube")
        controls_layout = controls.layout()

        intro = QLabel(
            "Collez un lien video ou playlist, choisissez le format, puis ajoutez a la file. "
            "Le gestionnaire execute les telechargements de facon fiable et sequentielle."
        )
        intro.setWordWrap(True)
        intro.setObjectName("cardHeadline")
        controls_layout.addWidget(intro)

        self.youtube_url_input = QLineEdit()
        self.youtube_url_input.setPlaceholderText(
            "Lien YouTube (video unique, shorts, live, playlist)..."
        )
        controls_layout.addWidget(self.youtube_url_input)

        row1 = QHBoxLayout()
        self.youtube_type_combo = QComboBox()
        self.youtube_type_combo.addItems(["mp3", "mp4"])
        self.youtube_type_combo.currentTextChanged.connect(self._on_youtube_media_type_changed)

        self.youtube_quality_combo = QComboBox()
        self.youtube_quality_combo.addItems(["Best", "High", "Medium", "Low"])

        self.youtube_playlist_check = QCheckBox("Autoriser playlist")
        self.youtube_playlist_check.setChecked(True)

        row1.addWidget(QLabel("Format"))
        row1.addWidget(self.youtube_type_combo)
        row1.addWidget(QLabel("Qualite"))
        row1.addWidget(self.youtube_quality_combo)
        row1.addWidget(self.youtube_playlist_check)
        row1.addStretch(1)
        controls_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.youtube_output_input = QLineEdit()
        output_default = str(Path.home() / "Downloads" / "SupportX-Media")
        self.youtube_output_input.setText(output_default)
        row2.addWidget(self.youtube_output_input, 1)

        browse_btn = QPushButton("Choisir dossier")
        browse_btn.clicked.connect(self._browse_youtube_output_dir)
        row2.addWidget(browse_btn)
        controls_layout.addLayout(row2)

        action_row = QHBoxLayout()
        self.youtube_add_btn = QPushButton("Ajouter a la file")
        self.youtube_add_btn.clicked.connect(self._add_youtube_task)
        action_row.addWidget(self.youtube_add_btn)

        self.youtube_cancel_btn = QPushButton("Annuler selection")
        self.youtube_cancel_btn.clicked.connect(self._cancel_selected_youtube_task)
        action_row.addWidget(self.youtube_cancel_btn)

        self.youtube_retry_btn = QPushButton("Relancer echec")
        self.youtube_retry_btn.clicked.connect(self._retry_selected_youtube_task)
        action_row.addWidget(self.youtube_retry_btn)

        self.youtube_remove_btn = QPushButton("Supprimer selection")
        self.youtube_remove_btn.clicked.connect(self._remove_selected_youtube_task)
        action_row.addWidget(self.youtube_remove_btn)

        controls_layout.addLayout(action_row)

        utility_row = QHBoxLayout()
        clear_btn = QPushButton("Nettoyer termines")
        clear_btn.clicked.connect(self.youtube_manager.clear_finished)
        utility_row.addWidget(clear_btn)

        open_dir_btn = QPushButton("Ouvrir dossier")
        open_dir_btn.clicked.connect(self._open_youtube_output_dir)
        utility_row.addWidget(open_dir_btn)

        utility_row.addStretch(1)
        controls_layout.addLayout(utility_row)

        self.youtube_health_label = QLabel("Verification dependance yt-dlp...")
        self.youtube_health_label.setObjectName("mutedLabel")
        self.youtube_health_label.setWordWrap(True)
        controls_layout.addWidget(self.youtube_health_label)

        queue = self._card("Gestionnaire de telechargements")
        queue_layout = queue.layout()

        self.youtube_table = QTableWidget(0, 7)
        self.youtube_table.setHorizontalHeaderLabels(["ID", "Format", "Qualite", "Source", "Statut", "Progression", "Lecture"])
        self.youtube_table.verticalHeader().setVisible(False)
        self.youtube_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.youtube_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.youtube_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.youtube_table.setAlternatingRowColors(True)
        self.youtube_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.youtube_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.youtube_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.youtube_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.youtube_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.youtube_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.youtube_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        queue_layout.addWidget(self.youtube_table)

        self.youtube_logs = QTextEdit()
        self.youtube_logs.setReadOnly(True)
        self.youtube_logs.setPlaceholderText("Journal des telechargements")
        queue_layout.addWidget(self.youtube_logs)

        layout.addWidget(controls, 0, 0)
        layout.addWidget(queue, 1, 0)
        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)

        self.youtube_manager.refresh_availability()
        return page

    def _build_about_page(self) -> QWidget:
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame, QTextEdit
        page = QWidget()
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(18, 18, 18, 18)
        outer_layout.setSpacing(18)

        # Ligne du haut : deux colonnes
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)

        # Colonne gauche : cube 3D
        cube_frame = QFrame()
        cube_layout = QVBoxLayout(cube_frame)
        cube_layout.setContentsMargins(0, 0, 0, 0)
        cube_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        cube3d = Anydesk3DWidget()
        cube3d.setFixedSize(320, 240)
        cube_layout.addWidget(cube3d)
        main_layout.addWidget(cube_frame, 0)

        # Colonne droite : texte
        text_frame = QFrame()
        text_layout = QVBoxLayout(text_frame)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)
        text_layout.setAlignment(Qt.AlignTop)

        # Section fonctionnalités conditionnelles
        features = []
        try:
            import diagnostic_tool
            features.append("Diagnostic système & réseau")
        except ImportError:
            pass
        try:
            import game
            features.append("Jeux intégrés (Snake, Clicker, Cube3D, etc.)")
        except ImportError:
            pass
        try:
            import supportx_app.youtube
            features.append("Téléchargement YouTube avancé")
        except ImportError:
            pass
        try:
            import supportx_app.web
            features.append("Navigateur web intégré/overlay")
        except ImportError:
            pass
        try:
            import supportx_app.updates
            features.append("Mise à jour automatique")
        except ImportError:
            pass
        try:
            import vispy
            features.append("Affichage 3D (Vispy)")
        except ImportError:
            pass
        if features:
            features_label = QLabel("Fonctionnalités conditionnelles :\n- " + "\n- ".join(features))
            features_label.setObjectName("cardHeadline")
            text_layout.addWidget(features_label)
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame, QTextEdit
        page = QWidget()
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(18, 18, 18, 18)
        outer_layout.setSpacing(18)

        # Ligne du haut : deux colonnes
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)

        # Colonne gauche : cube 3D
        cube_frame = QFrame()
        cube_layout = QVBoxLayout(cube_frame)
        cube_layout.setContentsMargins(0, 0, 0, 0)
        cube_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        cube3d = Anydesk3DWidget()
        cube3d.setFixedSize(320, 240)
        cube_layout.addWidget(cube3d)
        main_layout.addWidget(cube_frame, 0)

        # Colonne droite : texte
        text_frame = QFrame()
        text_layout = QVBoxLayout(text_frame)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)
        text_layout.setAlignment(Qt.AlignTop)

        title = QLabel("SupportX App")
        title.setObjectName("heroTitle")
        subtitle = QLabel(f"Version {self.config.app_version}")
        subtitle.setObjectName("cardHeadline")
        author = QLabel("Développeur : onechok")
        author.setObjectName("cardHeadline")

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        text_layout.addWidget(author)

        # Informations complémentaires
        license_label = QLabel("Licence : MIT (voir dépôt GitHub)")
        license_label.setObjectName("cardHeadline")
        github_label = QLabel('<a href="https://github.com/onechok/SupportX-App">Dépôt GitHub</a>')
        github_label.setOpenExternalLinks(True)
        github_label.setObjectName("cardHeadline")
        website_label = QLabel('<a href="https://supportx.ch/">Site officiel</a>')
        website_label.setOpenExternalLinks(True)
        website_label.setObjectName("cardHeadline")
        deps_label = QLabel("Dépendances : PySide6, vispy, yt-dlp, requests")
        deps_label.setObjectName("cardHeadline")

        text_layout.addWidget(license_label)
        text_layout.addWidget(github_label)
        text_layout.addWidget(website_label)
        text_layout.addWidget(deps_label)
        main_layout.addWidget(text_frame, 1)

        outer_layout.addLayout(main_layout)

        # Ligne du bas : détails sur toute la largeur
        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(
            "Architecture modulaire:\n\n"
            "- supportx_app/config.py: configuration\n"
            "- supportx_app/updates.py: verification et orchestration updater\n"
            "- supportx_app/updater/: sous-application de mise a jour\n"
            "- supportx_app/web/: composant navigateur integre\n"
            "- supportx_app/ui/main_window.py: interface principale\n\n"
            "Historique des versions (essentiel):\n\n"
            "- v0.0.3: base multi-OS, tray en arriere-plan, demarrage systeme, pipeline release GitHub.\n"
            "- v0.0.4: lanceurs sans commande Linux/macOS/Windows + raccourci desktop Linux.\n"
            "- v0.0.5: installateur Windows robuste (verification Python, venv, raccourcis).\n"
            "- v0.0.6: correction dependances Windows (suppression pywebview/pythonnet) pour fiabilite d'installation.\n"
            "- v0.0.7: ajout de la generation automatique de l'installeur Windows .exe (Inno Setup).\n"
            "- v0.0.8: mise a jour uniquement sur confirmation utilisateur, verification non bloquante.\n"
            "- v0.0.9: correction des chemins Inno Setup pour une build .exe release fiable.\n"
        )
        outer_layout.addWidget(details)
        return page

    def _card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setObjectName("cardTitle")
        layout.addWidget(header)
        return frame

    def _on_youtube_media_type_changed(self, media_type: str) -> None:
        self.youtube_quality_combo.clear()
        if media_type == "mp3":
            self.youtube_quality_combo.addItems(["Best", "High", "Medium", "Low"])
            return
        self.youtube_quality_combo.addItems(["Best", "1080p", "720p", "480p", "360p"])

    def _browse_youtube_output_dir(self) -> None:
        current = self.youtube_output_input.text().strip() or str(Path.home() / "Downloads")
        target = QFileDialog.getExistingDirectory(self, "Choisir un dossier de destination", current)
        if target:
            self.youtube_output_input.setText(target)

    def _add_youtube_task(self) -> None:
        url = self.youtube_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "YouTube", "Veuillez fournir un lien YouTube valide.")
            return

        if "youtube.com" not in url and "youtu.be" not in url:
            answer = QMessageBox.question(
                self,
                "Lien non standard",
                "Ce lien ne ressemble pas a une URL YouTube. Voulez-vous continuer ?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        output_dir = self.youtube_output_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "YouTube", "Veuillez choisir un dossier de destination.")
            return

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        available, message = self.youtube_manager.get_availability()
        if not available:
            QMessageBox.warning(self, "YouTube", message)
            return

        selected_media = self.youtube_type_combo.currentText()
        ok, requirement_message = self.youtube_manager.validate_task_requirements(selected_media)
        if not ok:
            QMessageBox.warning(self, "YouTube", requirement_message)
            return
        if requirement_message:
            self.status.showMessage(requirement_message)

        self.youtube_manager.create_task(
            url=url,
            media_type=selected_media,
            quality=self.youtube_quality_combo.currentText(),
            allow_playlist=self.youtube_playlist_check.isChecked(),
            output_dir=output_dir,
            start_now=True,
        )
        self.youtube_url_input.clear()
        self.status.showMessage("Telechargement ajoute a la file")

    def _selected_youtube_task_id(self) -> int | None:
        row = self.youtube_table.currentRow()
        if row < 0:
            return None
        item = self.youtube_table.item(row, 0)
        if item is None:
            return None
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(task_id, int):
            return task_id
        return None

    def _find_youtube_row(self, task_id: int) -> int:
        for row in range(self.youtube_table.rowCount()):
            item = self.youtube_table.item(row, 0)
            if item is None:
                continue
            if item.data(Qt.ItemDataRole.UserRole) == task_id:
                return row
        return -1

    def _cancel_selected_youtube_task(self) -> None:
        task_id = self._selected_youtube_task_id()
        if task_id is None:
            QMessageBox.information(self, "YouTube", "Selectionnez une ligne a annuler.")
            return
        self.youtube_manager.cancel_task(task_id)

    def _retry_selected_youtube_task(self) -> None:
        task_id = self._selected_youtube_task_id()
        if task_id is None:
            QMessageBox.information(self, "YouTube", "Selectionnez une ligne a relancer.")
            return
        new_id = self.youtube_manager.retry_task(task_id)
        if new_id is None:
            QMessageBox.warning(self, "YouTube", "Impossible de relancer cette tache.")

    def _remove_selected_youtube_task(self) -> None:
        task_id = self._selected_youtube_task_id()
        if task_id is None:
            QMessageBox.information(self, "YouTube", "Selectionnez une ligne a supprimer.")
            return
        self.youtube_manager.remove_task(task_id)

    def _open_youtube_output_dir(self) -> None:
        target = self.youtube_output_input.text().strip()
        if not target:
            QMessageBox.information(self, "YouTube", "Aucun dossier configure.")
            return
        target_path = Path(target)
        target_path.mkdir(parents=True, exist_ok=True)
        try:
            if platform.system() == "Windows":
                os.startfile(str(target_path))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(target_path)])
            else:
                subprocess.Popen(["xdg-open", str(target_path)])
        except Exception as exc:
            QMessageBox.warning(self, "YouTube", f"Impossible d'ouvrir le dossier.\n\n{exc}")

    def _on_youtube_availability_changed(self, available: bool, message: str) -> None:
        self.youtube_health_label.setText(message)
        self.youtube_add_btn.setEnabled(available)
        self.youtube_cancel_btn.setEnabled(available)
        self.youtube_retry_btn.setEnabled(available)
        self.youtube_remove_btn.setEnabled(True)

    def _on_youtube_task_created(self, task: dict) -> None:
        row = self.youtube_table.rowCount()
        self.youtube_table.insertRow(row)

        id_item = QTableWidgetItem(str(task["task_id"]))
        id_item.setData(Qt.ItemDataRole.UserRole, task["task_id"])
        self.youtube_table.setItem(row, 0, id_item)
        self.youtube_table.setItem(row, 1, QTableWidgetItem(task["media_type"].upper()))
        self.youtube_table.setItem(row, 2, QTableWidgetItem(task["quality"]))

        source = task["url"]
        if len(source) > 110:
            source = source[:107] + "..."
        self.youtube_table.setItem(row, 3, QTableWidgetItem(source))
        self.youtube_table.setItem(row, 4, QTableWidgetItem(task["status"]))
        self.youtube_table.setItem(row, 5, QTableWidgetItem(f"{task['progress']:.1f}%"))

        # Ajout du bouton Lecture
        from PySide6.QtWidgets import QPushButton
        play_btn = QPushButton("Lecture")
        play_btn.setEnabled(task["status"] == "done")
        play_btn.clicked.connect(lambda _=None, t=task: self._play_youtube_file(t))
        self.youtube_table.setCellWidget(row, 6, play_btn)

    def _on_youtube_task_updated(self, task: dict) -> None:
        row = self._find_youtube_row(int(task["task_id"]))
        if row < 0:
            return

        status = task.get("status", "")
        message = task.get("message", "")
        progress = float(task.get("progress", 0.0))
        self.youtube_table.item(row, 4).setText(f"{status} - {message}")
        self.youtube_table.item(row, 5).setText(f"{progress:.1f}%")
        self.status.showMessage(f"YouTube: tache #{task['task_id']} {status}")

        # Activer/désactiver le bouton Lecture selon le statut
        play_btn = self.youtube_table.cellWidget(row, 6)
        if play_btn:
            play_btn.setEnabled(status == "done")

    def _play_youtube_file(self, task: dict) -> None:
        """Ouvre le fichier téléchargé avec le lecteur par défaut."""
        # Recherche du dossier de sortie et du nom de fichier attendu
        output_dir = task.get("output_dir")
        url = task.get("url")
        media_type = task.get("media_type")
        # Recherche du fichier téléchargé dans le dossier de sortie
        # On prend le fichier le plus récent correspondant au type demandé
        import glob
        import os
        from pathlib import Path
        exts = {"mp3": "*.mp3", "mp4": "*.mp4"}
        pattern = os.path.join(output_dir, exts.get(media_type, "*"))
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if not files:
            QMessageBox.warning(self, "Lecture", "Aucun fichier trouvé dans le dossier de sortie.")
            return
        target_path = Path(files[0])
        try:
            if platform.system() == "Windows":
                os.startfile(str(target_path))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(target_path)])
            else:
                subprocess.Popen(["xdg-open", str(target_path)])
        except Exception as exc:
            QMessageBox.warning(self, "Lecture", f"Impossible d'ouvrir le fichier.\n\n{exc}")

    def _on_youtube_task_removed(self, task_id: int) -> None:
        row = self._find_youtube_row(task_id)
        if row >= 0:
            self.youtube_table.removeRow(row)

    def _on_youtube_task_log(self, task_id: int, line: str) -> None:
        self.youtube_logs.append(f"#{task_id} {line}")

    def apply_theme(self, mode: str) -> None:
        self.setStyleSheet(stylesheet_for(mode))

    def change_theme(self, value: str) -> None:
        self.config.theme = value
        self.config.save(self.config_path)
        self.apply_theme(value)
        self.status.showMessage("Theme applique")

    def save_auto_update_setting(self, state: bool) -> None:
        self.config.auto_update = bool(state)
        self.config.save(self.config_path)
        self.status.showMessage("Mises a jour automatiques sauvegardees")

    def save_startup_setting(self, state: bool) -> None:
        enabled = bool(state)
        self.config.start_with_system = enabled
        self.config.save(self.config_path)
        ok, message = set_startup(enabled, self.config.app_name, self.app_dir)
        if ok:
            self.status.showMessage("Demarrage automatique sauvegarde")
        else:
            self.status.showMessage(message)

    def save_simulate_setting(self, state: bool) -> None:
        self.config.simulate_updates = bool(state)
        self.config.save(self.config_path)
        self.status.showMessage("Mode simulation mis a jour")

    def open_in_browser(self) -> None:
        url = self.web_widget.web.url().toString() or self.config.supportx_url
        webbrowser.open(normalize_url(url, self.config.supportx_url))

    def check_for_updates(self, manual: bool) -> None:
        if self._update_check_in_progress:
            if manual:
                QMessageBox.information(self, "Mises a jour", "Une verification est deja en cours.")
            return

        self._update_check_in_progress = True
        self.check_update_btn.setEnabled(False)
        self.update_status_label.setText("Verification des mises a jour en cours...")
        self.status.showMessage("Verification des mises a jour...")

        def worker() -> None:
            service = UpdateService(self.config)
            update: UpdateInfo | None = None
            error: Exception | None = None
            try:
                update = service.check()
            except Exception as exc:
                error = exc

            self._update_check_bridge.completed.emit(manual, update, error)

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_check_finished(
        self,
        manual: bool,
        update: UpdateInfo | None,
        error: Exception | None,
    ) -> None:
        self._update_check_in_progress = False
        self.check_update_btn.setEnabled(True)

        if error is not None:
            self._pending_update = None
            self.install_update_btn.setEnabled(False)
            self.update_status_label.setText("Echec de la verification des mises a jour")
            self.status.showMessage("Erreur de verification")
            if manual:
                QMessageBox.warning(self, "Mises a jour", f"Impossible de verifier les mises a jour.\n\n{error}")
            return

        if update is None:
            self._pending_update = None
            self.install_update_btn.setEnabled(False)
            self.update_status_label.setText("Aucune information de mise a jour disponible")
            self.status.showMessage("Verification des mises a jour terminee")
            return

        if update.has_update:
            self._pending_update = update
            self.install_update_btn.setEnabled(True)
            self.update_status_label.setText(f"Nouvelle version disponible: {update.latest_version}")
            self.status.showMessage(f"Version {update.latest_version} disponible")

            if manual:
                answer = QMessageBox.question(
                    self,
                    "Mise a jour disponible",
                    f"Version {update.latest_version} disponible.\n\nNotes:\n{update.notes}\n\n"
                    "Lancer l'installation maintenant ?",
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self.install_pending_update()
        else:
            self._pending_update = None
            self.install_update_btn.setEnabled(False)
            self.update_status_label.setText(f"Vous etes a jour (v{self.config.app_version})")
            self.status.showMessage("Application a jour")
            if manual:
                QMessageBox.information(self, "Mises a jour", "Vous utilisez deja la derniere version.")

    def install_pending_update(self, silent: bool = False) -> None:
        if not self._pending_update:
            QMessageBox.information(self, "Mises a jour", "Aucune mise a jour en attente.")
            return

        if not silent:
            answer = QMessageBox.question(
                self,
                "Confirmer la mise a jour",
                "Voulez-vous lancer la mise a jour maintenant ?\n\n"
                "L'application se fermera pendant l'installation.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        service = UpdateService(self.config)
        entrypoint = self.app_dir / "launcher.py"
        ok, message = service.launch_updater(
            update=self._pending_update,
            app_dir=self.app_dir,
            config_path=self.config_path,
            entrypoint_path=entrypoint,
            parent_pid=os.getpid(),
        )

        if not ok:
            if not silent:
                QMessageBox.warning(self, "Updater", message)
            self.status.showMessage("Impossible de lancer Updater")
            return

        self.status.showMessage("Updater lance, fermeture de l'application...")
        if not silent:
            QMessageBox.information(
                self,
                "Updater",
                "Le module Updater va installer la nouvelle version puis redemarrer SupportX.",
            )
        QTimer.singleShot(300, QApplication.instance().quit)

    def _anydesk_deb_path(self) -> Path:
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return downloads_dir / "anydesk_amd64.deb"

    def _anydesk_download_info(self) -> tuple[str, Path, str]:
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        system = platform.system()
        if system == "Linux":
            return (
                "https://download.anydesk.com/linux/anydesk_amd64.deb",
                downloads_dir / "anydesk_amd64.deb",
                "Linux",
            )
        if system == "Windows":
            return (
                "https://download.anydesk.com/AnyDesk.exe",
                downloads_dir / "AnyDesk.exe",
                "Windows",
            )
        if system == "Darwin":
            return (
                "https://download.anydesk.com/AnyDesk.dmg",
                downloads_dir / "AnyDesk.dmg",
                "macOS",
            )
        return ("", downloads_dir / "anydesk_installer", "Inconnu")

    def download_anydesk(self) -> None:
        url, target, platform_name = self._anydesk_download_info()
        if not url:
            QMessageBox.warning(self, "AnyDesk", "Plateforme non supportee pour le telechargement automatique.")
            return

        self.anydesk_status.setText(f"Statut: telechargement AnyDesk ({platform_name}) en cours vers {target}")
        self.status.showMessage("Telechargement AnyDesk en cours...")

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(target, "wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)
            self.anydesk_status.setText(f"Statut: telechargement termine ({target})")
            self.status.showMessage("Telechargement AnyDesk termine")
        except Exception as exc:
            self.anydesk_status.setText("Statut: echec du telechargement")
            QMessageBox.warning(self, "AnyDesk", f"Impossible de telecharger AnyDesk.\n\n{exc}")

    def install_anydesk(self) -> None:
        _, target, platform_name = self._anydesk_download_info()
        if not target.exists():
            QMessageBox.information(self, "AnyDesk", "Le paquet n'est pas present. Lancez d'abord le telechargement.")
            return

        system = platform.system()
        if system == "Windows":
            self.anydesk_status.setText("Statut: lancement de l'installateur Windows...")
            try:
                os.startfile(str(target))  # type: ignore[attr-defined]
                self.status.showMessage("Installateur AnyDesk lance")
                return
            except Exception as exc:
                QMessageBox.warning(self, "AnyDesk", f"Impossible de lancer l'installateur Windows.\n\n{exc}")
                return

        if system == "Darwin":
            self.anydesk_status.setText("Statut: ouverture de l'image disque macOS...")
            try:
                subprocess.Popen(["open", str(target)])
                self.status.showMessage("Image disque AnyDesk ouverte")
                return
            except Exception as exc:
                QMessageBox.warning(self, "AnyDesk", f"Impossible d'ouvrir l'image disque macOS.\n\n{exc}")
                return

        if system != "Linux":
            QMessageBox.warning(self, "AnyDesk", f"Installation non supportee sur {platform_name}.")
            return

        self.anydesk_status.setText("Statut: preparation de l'installation...")
        command = f"sudo apt install -y '{target}'"

        if shutil.which("pkexec"):
            try:
                subprocess.Popen(["pkexec", "apt", "install", "-y", str(target)])
                self.anydesk_status.setText("Statut: installation lancee (pkexec)")
                self.status.showMessage("Installation AnyDesk lancee")
                return
            except Exception:
                pass

        terminal = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal") or shutil.which("konsole")
        if terminal:
            try:
                if "konsole" in terminal:
                    subprocess.Popen([terminal, "-e", f"bash -lc \"{command}; echo; read -n 1 -s -r -p 'Appuyez sur une touche...'\""])
                else:
                    subprocess.Popen([terminal, "-e", "bash", "-lc", f"{command}; echo; read -n 1 -s -r -p 'Appuyez sur une touche...'"])
                self.anydesk_status.setText("Statut: installation lancee dans le terminal")
                self.status.showMessage("Installation AnyDesk lancee")
                return
            except Exception:
                pass

        self.anydesk_status.setText("Statut: installation manuelle requise")
        QMessageBox.information(
            self,
            "AnyDesk",
            "Impossible de lancer l'installation automatiquement.\n\n"
            f"Executez cette commande:\n{command}",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_dir = Path(__file__).resolve().parents[2]
    window = MainWindow(app_dir)
    window.show()
    raise SystemExit(app.exec())
