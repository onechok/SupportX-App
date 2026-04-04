from __future__ import annotations

import webbrowser
from pathlib import Path
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    from ..config import AppConfig, normalize_url
    from ..theme import stylesheet_for
    from ..updates import UpdateService
    from ..web.overlay_view import OverlayWebView
except ImportError:
    from supportx_app.config import AppConfig, normalize_url
    from supportx_app.theme import stylesheet_for
    from supportx_app.updates import UpdateService
    from supportx_app.web.overlay_view import OverlayWebView


class MainWindow(QMainWindow):
    def __init__(self, app_dir: Path) -> None:
        super().__init__()
        self.config_path = app_dir / "config.json"
        self.config = AppConfig.load(self.config_path)

        self.setWindowTitle(f"{self.config.app_name} - v{self.config.app_version}")
        self.resize(1360, 840)
        self.setMinimumSize(1100, 720)

        self._build_ui()
        self.apply_theme(self.config.theme)

        if self.config.auto_update:
            QTimer.singleShot(1000, lambda: self.check_for_updates(manual=False))

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
        self.home_page = self._build_home_page()
        self.web_page = self._build_web_page()
        self.history_page = self._build_history_page()
        self.settings_page = self._build_settings_page()
        self.about_page = self._build_about_page()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.web_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.about_page)
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self.status.showMessage(f"Pret • {self.config.app_name} • Version {self.config.app_version}")
        self._build_menu()
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

        for index, label in enumerate(["Accueil", "SupportX Web", "Historique", "Parametres", "A propos"]):
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

    def _build_menu(self) -> None:
        app_menu = self.menuBar().addMenu("Application")

        refresh_action = QAction("Recharger SupportX Web", self)
        refresh_action.triggered.connect(self.web_widget.web.reload)
        app_menu.addAction(refresh_action)

        open_browser = QAction("Ouvrir dans le navigateur externe", self)
        open_browser.triggered.connect(self.open_in_browser)
        app_menu.addAction(open_browser)

    def _set_active_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        overview = self._card("Dashboard")
        ov = overview.layout()

        hero = QLabel("Architecture modulaire PySide6 + rendu web natif QWebEngineView")
        hero.setObjectName("cardHeadline")
        hero.setWordWrap(True)
        ov.addWidget(hero)

        version = QLabel(f"Version active: {self.config.app_version}")
        version.setObjectName("mutedLabel")
        ov.addWidget(version)

        actions = QWidget()
        actions_layout = QVBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        check_update = QPushButton("Verifier les mises a jour")
        check_update.clicked.connect(lambda: self.check_for_updates(manual=True))
        open_web = QPushButton("Aller a SupportX Web")
        open_web.clicked.connect(lambda: self._set_active_page(1))
        actions_layout.addWidget(check_update)
        actions_layout.addWidget(open_web)
        ov.addWidget(actions)

        update_card = self._card("Etat des mises a jour")
        upd = update_card.layout()
        self.update_status_label = QLabel("Derniere verification: jamais")
        self.update_status_label.setWordWrap(True)
        upd.addWidget(self.update_status_label)

        layout.addWidget(overview, 0, 0)
        layout.addWidget(update_card, 0, 1)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)
        return page

    def _build_web_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web_widget = OverlayWebView(self.config.supportx_url, self.status.showMessage)
        layout.addWidget(self.web_widget)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        history_url = self.config.history_url or self.config.supportx_url
        self.history_widget = OverlayWebView(history_url, self.status.showMessage)
        layout.addWidget(self.history_widget)
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
        self.auto_update_check = QCheckBox("Verifier automatiquement les mises a jour")
        self.auto_update_check.setChecked(self.config.auto_update)
        self.auto_update_check.toggled.connect(self.save_auto_update_setting)

        self.simulate_check = QCheckBox("Activer le mode simulation")
        self.simulate_check.setChecked(self.config.simulate_updates)
        self.simulate_check.toggled.connect(self.save_simulate_setting)

        up.addWidget(self.auto_update_check)
        up.addWidget(self.simulate_check)

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

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("SupportX App")
        title.setObjectName("heroTitle")
        subtitle = QLabel(f"Version {self.config.app_version}")
        subtitle.setObjectName("cardHeadline")

        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(
            "Architecture recommandee pour evoluer proprement:\n\n"
            "- supportx_app/config.py: config et persistance\n"
            "- supportx_app/updates.py: verification updates\n"
            "- supportx_app/theme.py: design system et themes\n"
            "- supportx_app/web/: composants web integres\n"
            "- supportx_app/ui/main_window.py: composition de l'interface\n"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(details)
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

    def save_simulate_setting(self, state: bool) -> None:
        self.config.simulate_updates = bool(state)
        self.config.save(self.config_path)
        self.status.showMessage("Mode simulation mis a jour")

    def open_in_browser(self) -> None:
        url = self.web_widget.web.url().toString() or self.config.supportx_url
        webbrowser.open(normalize_url(url, self.config.supportx_url))

    def check_for_updates(self, manual: bool) -> None:
        self.update_status_label.setText("Verification des mises a jour en cours...")
        self.status.showMessage("Verification des mises a jour...")

        service = UpdateService(
            current_version=self.config.app_version,
            update_url=normalize_url(self.config.update_server_url, AppConfig().update_server_url),
            simulate=self.config.simulate_updates,
        )

        try:
            has_update, latest_version, notes = service.check()
        except Exception as exc:
            self.update_status_label.setText("Echec de la verification des mises a jour")
            self.status.showMessage("Erreur de verification")
            if manual:
                QMessageBox.warning(self, "Mises a jour", f"Impossible de verifier les mises a jour.\n\n{exc}")
            return

        if has_update:
            self.update_status_label.setText(f"Nouvelle version disponible: {latest_version}")
            self.status.showMessage(f"Version {latest_version} disponible")
            if manual:
                QMessageBox.information(
                    self,
                    "Mise a jour disponible",
                    f"Version {latest_version} disponible.\n\nNotes:\n{notes}",
                )
        else:
            self.update_status_label.setText(f"Vous etes a jour (v{self.config.app_version})")
            self.status.showMessage("Application a jour")
            if manual:
                QMessageBox.information(self, "Mises a jour", "Vous utilisez deja la derniere version.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_dir = Path(__file__).resolve().parents[2]
    window = MainWindow(app_dir)
    window.show()
    raise SystemExit(app.exec())
