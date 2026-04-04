from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

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

    window = MainWindow(Path(__file__).resolve().parent.parent)
    window.show()
    return app.exec()
