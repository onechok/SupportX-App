from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .startup import set_startup
from .ui.main_window import MainWindow


class FilteredStderr:
    def __init__(self, original):
        self.original = original
        self._ignore = (
            "Bind context provider failed",
            "GPUInfo not initialized on GpuInfoUpdate",
            "Failed to create WebGPU Context Provider",
            "Multiple GoTrueClient instances detected",
            "Blocked aria-hidden on a <body>",
        )

    def write(self, data):
        if any(token in data for token in self._ignore):
            return
        self.original.write(data)

    def flush(self):
        self.original.flush()


def run() -> int:
    # Force software-friendly rendering paths to avoid noisy WebGPU/VideoCapture errors.
    os.environ.setdefault(
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "--disable-gpu --disable-gpu-compositing --disable-webgpu "
        "--disable-webrtc --disable-logging --log-level=3 "
        "--disable-features=Vulkan,UseSkiaRenderer,MediaStream,MojoVideoCapture",
    )
    os.environ.setdefault("QT_LOGGING_RULES", "qt.webenginecontext.debug=false")
    sys.stderr = FilteredStderr(sys.stderr)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(Path(__file__).resolve().parent.parent)
    set_startup(window.config.start_with_system, window.config.app_name, window.app_dir)
    tray = _create_tray_icon(app, window)
    app._tray_icon = tray
    window.set_tray_enabled(tray is not None)
    window.show()
    return app.exec()


def _create_tray_icon(app: QApplication, window: MainWindow) -> QSystemTrayIcon | None:
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    app_dir = Path(__file__).resolve().parent.parent
    tray_icon_path = app_dir / "image" / "logo" / "logo-notification.ico"
    if tray_icon_path.exists():
        icon = QIcon(str(tray_icon_path))
    else:
        icon = _build_tray_icon()

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("SupportX App")

    menu = QMenu()
    action_show = QAction("Ouvrir la fenetre", menu)
    action_hide = QAction("Masquer en arriere-plan", menu)
    action_check_updates = QAction("Verifier les mises a jour", menu)
    action_quit = QAction("Quitter", menu)

    action_show.triggered.connect(window.show_from_tray)
    action_hide.triggered.connect(window.hide_to_tray)
    action_check_updates.triggered.connect(lambda: window.check_for_updates(manual=True))
    action_quit.triggered.connect(window.request_quit)

    menu.addAction(action_show)
    menu.addAction(action_hide)
    menu.addSeparator()
    menu.addAction(action_check_updates)
    menu.addSeparator()
    menu.addAction(action_quit)

    tray.setContextMenu(menu)

    def _on_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            window.show_from_tray()

    tray.activated.connect(_on_activated)
    tray.show()
    tray.showMessage(
        "SupportX",
        "L'application continue en arriere-plan. Clic droit pour ouvrir le menu.",
        QSystemTrayIcon.MessageIcon.Information,
        2500,
    )
    return tray


def _build_tray_icon() -> QIcon:
    """Build a square multi-resolution tray icon that fills available tray height."""
    icon = QIcon()
    for size in (16, 20, 22, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        margin = max(1, size // 12)
        stroke = max(2, size // 4)

        # Soft dark underlay keeps the icon readable on light system trays.
        shadow_pen = QPen(QColor(0, 0, 0, 150), stroke + 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(shadow_pen)
        painter.drawLine(margin + 1, margin + 1, size - margin + 1, size - margin + 1)
        painter.drawLine(size - margin + 1, margin + 1, margin + 1, size - margin + 1)

        main_pen = QPen(QColor(255, 210, 0), stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(main_pen)
        painter.drawLine(margin, margin, size - margin, size - margin)
        painter.drawLine(size - margin, margin, margin, size - margin)

        painter.end()
        icon.addPixmap(pixmap)

    return icon
