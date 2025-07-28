from tkinter import ttk
from ttkbootstrap.constants import *
from tkinterweb import HtmlFrame

def build_web_tab(self):
    toolbar = ttk.Frame(self.web_tab, padding=10)
    toolbar.pack(fill="x", padx=10, pady=(10, 5))

    actions = [
        ("Actualiser", "info", self.refresh_webview, 10),
        ("Accueil", "secondary", lambda: self.load_webview(self.supportx_url), 10),
        ("Ouvrir navigateur", "primary", self.open_in_browser, 18)
    ]

    for text, style, command, width in actions:
        btn = ttk.Button(
            toolbar,
            text=text,
            bootstyle=style,
            command=command,
            width=width
        )
        if text == "Ouvrir navigateur":
            btn.pack(side="right", padx=5)
        else:
            btn.pack(side="left", padx=5)

    self.web_frame = HtmlFrame(self.web_tab, messages_enabled=False)
    self.web_frame.load_website(self.supportx_url)
    self.web_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
