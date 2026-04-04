from tkinter import StringVar, ttk

from tkinterweb import HtmlFrame
from ttkbootstrap.constants import *


def build_history_tab(app, tab):
    shell = ttk.Frame(tab)
    shell.pack(fill="both", expand=True)

    top = ttk.Labelframe(shell, text="Historique SupportX", style="Card.TLabelframe", bootstyle=PRIMARY)
    top.pack(fill="x", padx=8, pady=(4, 8))
    top.grid_columnconfigure(0, weight=1)

    ttk.Label(
        top,
        text="Consultez les informations recentes sans quitter l'application.",
        style="CardTitle.TLabel",
    ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

    history_url = "https://supportx.ch/"
    url_var = StringVar(value=history_url)
    ttk.Entry(top, textvariable=url_var).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    actions = ttk.Frame(top)
    actions.grid(row=1, column=1, padx=10, pady=(0, 10))

    frame = HtmlFrame(shell, messages_enabled=False)
    frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    frame.load_website(history_url)

    ttk.Button(actions, text="Charger", bootstyle=PRIMARY, command=lambda: frame.load_url(url_var.get())).pack(
        side="left", padx=(0, 6)
    )
    ttk.Button(actions, text="Actualiser", bootstyle=INFO, command=frame.reload).pack(side="left")
