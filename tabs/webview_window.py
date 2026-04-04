import os
import sys
from http.cookies import CookieError, SimpleCookie

# Stabilise le rendu QtWebEngine sur certaines configurations Linux.
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-gpu-compositing --disable-software-rasterizer",
)

import webview
import webview.util as webview_util


_original_create_cookie = webview_util.create_cookie


def _safe_create_cookie(raw_cookie):
    try:
        return _original_create_cookie(raw_cookie)
    except CookieError:
        # Certains scripts tiers (ex: Crisp) posent des cookies non RFC,
        # on les ignore pour ne pas interrompre le rendu de la page.
        return SimpleCookie()


webview_util.create_cookie = _safe_create_cookie


def normalize_url(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return "https://supportx.ch/"
    if not cleaned.startswith(("http://", "https://")):
        return f"https://{cleaned}"
    return cleaned


def main() -> None:
    target_url = normalize_url(sys.argv[1] if len(sys.argv) > 1 else "https://supportx.ch/")
    webview.create_window(
        "SupportX Web",
        url=target_url,
        width=1280,
        height=820,
        min_size=(980, 640),
        resizable=True,
        confirm_close=True,
    )
    webview.start(gui="qt", debug=False, private_mode=False)


if __name__ == "__main__":
    main()
