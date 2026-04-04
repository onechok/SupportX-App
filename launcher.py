import json
import os
import sys
import webbrowser
from pathlib import Path

import requests
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QGuiApplication, QPalette
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
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
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


DEFAULT_CONFIG = {
    "theme": "system",
    "auto_update": True,
    "simulate_updates": False,
    "app_name": "SupportX App",
    "app_version": "1.0.0",
    "supportx_url": "https://supportx.ch/",
    "history_url": "https://supportx.ch/",
    "update_server_url": "https://supportx.ch/updates/version.json",
}


BRAND = {
    "primary": "#0A6EB6",
    "primary_hover": "#085A95",
    "primary_pressed": "#064977",
    "accent": "#1DA7D6",
}


def normalize_url(url: str, fallback: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return fallback
    if not cleaned.startswith(("http://", "https://")):
        return f"https://{cleaned}"
    return cleaned


def parse_version(version: str) -> list[int]:
    return [int(part) for part in version.split(".") if part.isdigit()]


class InternalWebPage(QWebEnginePage):
    def createWindow(self, _type):
        page = QWebEnginePage(self.profile(), self)
        page.urlChanged.connect(lambda url: webbrowser.open(url.toString()))
        return page


class OverlayWebView(QWidget):
    def __init__(self, home_url: str, status_callback) -> None:
        super().__init__()
        self.home_url = QUrl(normalize_url(home_url, DEFAULT_CONFIG["supportx_url"]))
        self.status_callback = status_callback

        self.web = QWebEngineView(self)
        self.web.setPage(InternalWebPage(self.web))

        self.loader = QFrame(self)
        self.loader.setObjectName("loaderOverlay")
        loader_layout = QVBoxLayout(self.loader)
        loader_layout.setContentsMargins(20, 20, 20, 20)
        loader_layout.setSpacing(10)
        self.loader_label = QLabel("Chargement de la page...")
        self.loader_label.setObjectName("overlayTitle")
        self.loader_progress = QProgressBar()
        self.loader_progress.setRange(0, 100)
        loader_layout.addWidget(self.loader_label)
        loader_layout.addWidget(self.loader_progress)
        self.loader.hide()

        self.error_overlay = QFrame(self)
        self.error_overlay.setObjectName("errorOverlay")
        error_layout = QVBoxLayout(self.error_overlay)
        error_layout.setContentsMargins(26, 26, 26, 26)
        error_layout.setSpacing(8)
        self.error_title = QLabel("Impossible d'afficher la page")
        self.error_title.setObjectName("overlayTitle")
        self.error_message = QLabel("Vérifiez la connexion internet puis réessayez.")
        self.error_message.setWordWrap(True)
        retry_btn = QPushButton("Réessayer")
        retry_btn.clicked.connect(self.web.reload)
        error_layout.addWidget(self.error_title)
        error_layout.addWidget(self.error_message)
        error_layout.addWidget(retry_btn)
        self.error_overlay.hide()

        self.nav_overlay = QFrame(self)
        self.nav_overlay.setObjectName("navOverlay")
        nav_layout = QHBoxLayout(self.nav_overlay)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(6)

        self.back_btn = self._tool_button("←", "Retour", self.web.back)
        self.forward_btn = self._tool_button("→", "Avancer", self.web.forward)
        self.reload_btn = self._tool_button("⟳", "Recharger", self.web.reload)

        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.reload_btn)

        self.web.loadStarted.connect(self.on_load_started)
        self.web.loadProgress.connect(self.on_load_progress)
        self.web.loadFinished.connect(self.on_load_finished)
        self.web.urlChanged.connect(self.on_url_changed)
        self.web.titleChanged.connect(self.on_title_changed)

        self.open_home()

    def _tool_button(self, text: str, tooltip: str, slot):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        btn.setObjectName("overlayToolButton")
        return btn

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.web.setGeometry(self.rect())

        overlay_width = max(260, min(440, self.width() - 60))
        overlay_x = (self.width() - overlay_width) // 2
        overlay_y = max(70, self.height() // 6)

        self.loader.setGeometry(overlay_x, overlay_y, overlay_width, 110)
        self.error_overlay.setGeometry(overlay_x, overlay_y, overlay_width, 180)

        nav_w = 170
        nav_h = 50
        self.nav_overlay.setGeometry(self.width() - nav_w - 16, 16, nav_w, nav_h)

    def open_home(self):
        self.web.setUrl(self.home_url)

    def open_external(self):
        webbrowser.open(self.web.url().toString())

    def on_load_started(self):
        self.error_overlay.hide()
        self.loader_progress.setRange(0, 0)
        self.loader_label.setText("Chargement de la page...")
        self.loader.show()

    def on_load_progress(self, value: int):
        if self.loader_progress.maximum() == 0:
            self.loader_progress.setRange(0, 100)
        self.loader_progress.setValue(value)
        self.loader_label.setText(f"Chargement... {value}%")

    def on_load_finished(self, ok: bool):
        self.loader.hide()
        self.back_btn.setEnabled(self.web.history().canGoBack())
        self.forward_btn.setEnabled(self.web.history().canGoForward())
        if not ok:
            self.error_message.setText(
                "La page n'a pas pu être chargée. Vérifiez le réseau, puis cliquez sur Réessayer."
            )
            self.error_overlay.show()

    def on_url_changed(self, _url: QUrl):
        self.back_btn.setEnabled(self.web.history().canGoBack())
        self.forward_btn.setEnabled(self.web.history().canGoForward())

    def on_title_changed(self, title: str):
        if self.status_callback:
            self.status_callback(f"SupportX Web: {title}")


class SupportXApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config_path = Path(__file__).resolve().parent / "config.json"
        self.config = self.load_config()

        self.setWindowTitle(f"{self.config['app_name']} - v{self.config['app_version']}")
        self.resize(1360, 840)
        self.setMinimumSize(1100, 720)

        self._build_ui()
        self.apply_theme(self.config.get("theme", "system"))

        if self.config.get("auto_update", True):
            QTimer.singleShot(1000, lambda: self.check_for_updates(manual=False))

    def load_config(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as handle:
                config = json.load(handle)
        else:
            config = {}

        changed = False
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                changed = True

        if changed:
            with open(self.config_path, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=4, ensure_ascii=False)
        return config

    def save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as handle:
            json.dump(self.config, handle, indent=4, ensure_ascii=False)

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

        sidebar = self._build_sidebar()
        content_layout.addWidget(sidebar)

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

        self.status.showMessage(f"Prêt • {self.config['app_name']} • Version {self.config['app_version']}")

        self._build_menu()
        self._set_active_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        app_title = QLabel(self.config["app_name"])
        app_title.setObjectName("sidebarTitle")
        app_version = QLabel(f"v{self.config['app_version']}")
        app_version.setObjectName("sidebarSubtitle")

        layout.addWidget(app_title)
        layout.addWidget(app_version)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        nav_items = [
            "Accueil",
            "SupportX Web",
            "Historique",
            "Paramètres",
            "À propos",
        ]

        for index, label in enumerate(nav_items):
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

        hero = QLabel("Expérience web native intégrée pour SupportX (Next.js complet)")
        hero.setObjectName("cardHeadline")
        hero.setWordWrap(True)
        ov.addWidget(hero)

        version = QLabel(f"Version active: {self.config['app_version']}")
        version.setObjectName("mutedLabel")
        ov.addWidget(version)

        actions = QWidget()
        actions_layout = QVBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        check_update = QPushButton("Vérifier les mises à jour")
        check_update.clicked.connect(lambda: self.check_for_updates(manual=True))
        open_web = QPushButton("Aller à SupportX Web")
        open_web.clicked.connect(lambda: self._set_active_page(1))

        actions_layout.addWidget(check_update)
        actions_layout.addWidget(open_web)
        ov.addWidget(actions)

        update_card = self._card("État des mises à jour")
        upd = update_card.layout()
        self.update_status_label = QLabel("Dernière vérification: jamais")
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
        self.web_widget = OverlayWebView(self.config["supportx_url"], self.status.showMessage)
        layout.addWidget(self.web_widget)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.history_widget = OverlayWebView(self.config.get("history_url", self.config["supportx_url"]), self.status.showMessage)
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
        ap.addWidget(QLabel("Mode de thème"))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        self.theme_combo.setCurrentText(self.config.get("theme", "system"))
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        ap.addWidget(self.theme_combo)

        updates = self._card("Mises à jour")
        up = updates.layout()

        self.auto_update_check = QCheckBox("Vérifier automatiquement les mises à jour")
        self.auto_update_check.setChecked(bool(self.config.get("auto_update", True)))
        self.auto_update_check.toggled.connect(self.save_auto_update_setting)

        self.simulate_check = QCheckBox("Activer le mode simulation")
        self.simulate_check.setChecked(bool(self.config.get("simulate_updates", False)))
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

        subtitle = QLabel(f"Version {self.config['app_version']}")
        subtitle.setObjectName("cardHeadline")

        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(
            "Application reconstruite avec PySide6 + QWebEngineView.\n\n"
            "• Sidebar moderne pour la navigation\n"
            "• Vue web intégrée plein écran dans l'onglet\n"
            "• Loader visuel et gestion élégante des erreurs réseau\n"
            "• Contrôles overlay minimal (retour, avant, refresh)\n"
            "• Thèmes light / dark / system avec palette de marque"
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

    def _is_system_dark(self) -> bool:
        palette = QGuiApplication.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128

    def apply_theme(self, mode: str) -> None:
        mode = mode if mode in ("system", "light", "dark") else "system"
        resolved = "dark" if (mode == "dark" or (mode == "system" and self._is_system_dark())) else "light"

        if resolved == "dark":
            tokens = {
                "bg": "#11161d",
                "panel": "#1b2430",
                "panel2": "#202b39",
                "text": "#e8eff7",
                "muted": "#9db0c3",
                "border": "#2f3f52",
                "content": "#121a24",
            }
        else:
            tokens = {
                "bg": "#eef3f8",
                "panel": "#ffffff",
                "panel2": "#f7fbff",
                "text": "#1c2a38",
                "muted": "#5e7388",
                "border": "#d2deea",
                "content": "#f9fbfd",
            }

        qss = f"""
            QMainWindow {{ background: {tokens['bg']}; color: {tokens['text']}; }}
            #contentStack {{ background: {tokens['content']}; }}
            #sidebar {{
                background: {tokens['panel']};
                border-right: 1px solid {tokens['border']};
            }}
            #sidebarTitle {{ font-size: 22px; font-weight: 700; color: {BRAND['primary']}; }}
            #sidebarSubtitle {{ font-size: 12px; color: {tokens['muted']}; margin-bottom: 6px; }}
            #navButton {{
                text-align: left;
                min-height: 38px;
                border: 1px solid transparent;
                border-radius: 10px;
                background: transparent;
                color: {tokens['text']};
                padding-left: 12px;
                font-weight: 600;
            }}
            #navButton:hover {{ background: {tokens['panel2']}; border-color: {tokens['border']}; }}
            #navButton:checked {{
                background: {BRAND['primary']};
                border-color: {BRAND['primary']};
                color: white;
            }}
            #secondaryButton {{
                min-height: 34px;
                border-radius: 8px;
                border: 1px solid {tokens['border']};
                background: {tokens['panel2']};
                color: {tokens['text']};
                font-weight: 600;
            }}
            #secondaryButton:hover {{ border-color: {BRAND['accent']}; }}
            #card {{
                background: {tokens['panel']};
                border: 1px solid {tokens['border']};
                border-radius: 14px;
            }}
            #cardTitle {{ font-size: 14px; font-weight: 700; color: {tokens['text']}; }}
            #cardHeadline {{ font-size: 13px; font-weight: 600; color: {tokens['text']}; }}
            #mutedLabel {{ font-size: 12px; color: {tokens['muted']}; }}
            #heroTitle {{ font-size: 26px; font-weight: 800; color: {BRAND['primary']}; }}
            QPushButton {{
                min-height: 34px;
                border: 1px solid {BRAND['primary']};
                border-radius: 8px;
                background: {BRAND['primary']};
                color: #ffffff;
                font-weight: 700;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background: {BRAND['primary_hover']}; border-color: {BRAND['primary_hover']}; }}
            QPushButton:pressed {{ background: {BRAND['primary_pressed']}; border-color: {BRAND['primary_pressed']}; }}
            QTextEdit, QComboBox {{
                background: {tokens['panel2']};
                color: {tokens['text']};
                border: 1px solid {tokens['border']};
                border-radius: 10px;
                padding: 6px;
            }}
            QLabel, QCheckBox {{ color: {tokens['text']}; }}
            QStatusBar {{
                background: {tokens['panel']};
                color: {tokens['muted']};
                border-top: 1px solid {tokens['border']};
            }}
            #navOverlay {{
                background: rgba(11, 21, 32, 170);
                border: 1px solid rgba(255,255,255,45);
                border-radius: 12px;
            }}
            #overlayToolButton {{
                min-width: 36px;
                min-height: 32px;
                border-radius: 8px;
                background: rgba(255,255,255,25);
                color: #ffffff;
                border: 1px solid rgba(255,255,255,35);
                font-size: 16px;
                font-weight: 700;
            }}
            #overlayToolButton:hover {{ background: rgba(255,255,255,45); }}
            #loaderOverlay, #errorOverlay {{
                background: rgba(8, 15, 24, 214);
                border: 1px solid rgba(255,255,255,45);
                border-radius: 12px;
                color: #ffffff;
            }}
            #overlayTitle {{ color: #ffffff; font-size: 15px; font-weight: 700; }}
        """
        self.setStyleSheet(qss)

    def change_theme(self, value: str) -> None:
        self.config["theme"] = value
        self.save_config()
        self.apply_theme(value)
        self.status.showMessage("Thème appliqué")

    def save_auto_update_setting(self, state: bool) -> None:
        self.config["auto_update"] = bool(state)
        self.save_config()
        self.status.showMessage("Mises à jour automatiques sauvegardées")

    def save_simulate_setting(self, state: bool) -> None:
        self.config["simulate_updates"] = bool(state)
        self.save_config()
        self.status.showMessage("Mode simulation mis à jour")

    def open_in_browser(self) -> None:
        webbrowser.open(self.web_widget.web.url().toString() or self.config["supportx_url"])

    def check_for_updates(self, manual: bool) -> None:
        self.update_status_label.setText("Vérification des mises à jour en cours...")
        self.status.showMessage("Vérification des mises à jour...")

        if self.config.get("simulate_updates", False):
            self._show_update_result("1.3.0", "Version simulée: améliorations visuelles et stabilité.", manual)
            return

        try:
            update_url = normalize_url(self.config.get("update_server_url", ""), DEFAULT_CONFIG["update_server_url"])
            response = requests.get(update_url, timeout=12)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get("version", self.config["app_version"])
            notes = data.get("notes", "Aucune note fournie.")
            self._show_update_result(latest_version, notes, manual)
        except Exception as exc:
            self.update_status_label.setText("Échec de la vérification des mises à jour")
            self.status.showMessage("Erreur de vérification")
            if manual:
                QMessageBox.warning(self, "Mises à jour", f"Impossible de vérifier les mises à jour.\n\n{exc}")

    def _show_update_result(self, latest_version: str, notes: str, manual: bool) -> None:
        current = parse_version(self.config["app_version"])
        incoming = parse_version(latest_version)

        if incoming > current:
            self.update_status_label.setText(f"Nouvelle version disponible: {latest_version}")
            self.status.showMessage(f"Version {latest_version} disponible")
            if manual:
                QMessageBox.information(
                    self,
                    "Mise à jour disponible",
                    f"Version {latest_version} disponible.\n\nNotes:\n{notes}",
                )
        else:
            self.update_status_label.setText(f"Vous êtes à jour (v{self.config['app_version']})")
            self.status.showMessage("Application à jour")
            if manual:
                QMessageBox.information(self, "Mises à jour", "Vous utilisez déjà la dernière version.")


def main() -> None:
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --disable-gpu-compositing")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SupportXApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
