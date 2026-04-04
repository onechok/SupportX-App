from __future__ import annotations

from PySide6.QtGui import QGuiApplication, QPalette


BRAND = {
    "primary": "#0A6EB6",
    "primary_hover": "#085A95",
    "primary_pressed": "#064977",
    "accent": "#1DA7D6",
}


def is_system_dark() -> bool:
    palette = QGuiApplication.palette()
    window_color = palette.color(QPalette.Window)
    return window_color.lightness() < 128


def stylesheet_for(mode: str) -> str:
    resolved = "dark" if (mode == "dark" or (mode == "system" and is_system_dark())) else "light"

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

    return f"""
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
