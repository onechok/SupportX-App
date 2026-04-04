from __future__ import annotations

import webbrowser

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from ..config import normalize_url
from .page import QuietWebPage


class OverlayWebView(QWidget):
    def __init__(self, home_url: str, status_callback) -> None:
        super().__init__()
        self.home_url = QUrl(normalize_url(home_url, "https://supportx.ch/"))
        self.status_callback = status_callback

        self.web = QWebEngineView(self)
        self.web.setPage(QuietWebPage(self.web))

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
        self.error_message = QLabel("Verifiez la connexion internet puis reessayez.")
        self.error_message.setWordWrap(True)
        retry_btn = QPushButton("Reessayer")
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

        self.back_btn = self._tool_button("<-", "Retour", self.web.back)
        self.forward_btn = self._tool_button("->", "Avancer", self.web.forward)
        self.reload_btn = self._tool_button("R", "Recharger", self.web.reload)

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
                "La page n'a pas pu etre chargee. Verifiez le reseau, puis cliquez sur Reessayer."
            )
            self.error_overlay.show()

    def on_url_changed(self, _url: QUrl):
        self.back_btn.setEnabled(self.web.history().canGoBack())
        self.forward_btn.setEnabled(self.web.history().canGoForward())

    def on_title_changed(self, title: str):
        if self.status_callback:
            self.status_callback(f"SupportX Web: {title}")
