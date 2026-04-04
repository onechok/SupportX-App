from __future__ import annotations

import webbrowser

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage


IGNORED_JS_PATTERNS = (
    "Multiple GoTrueClient instances detected",
    "Failed to create WebGPU Context Provider",
    "Blocked aria-hidden on a <body>",
)


class QuietWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        for pattern in IGNORED_JS_PATTERNS:
            if pattern in message:
                return
        super().javaScriptConsoleMessage(level, message, line_number, source_id)

    def createWindow(self, _type):
        page = QWebEnginePage(self.profile(), self)
        page.urlChanged.connect(lambda url: webbrowser.open(url.toString()))
        return page
