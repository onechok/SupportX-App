from tkinter import ttk

from ttkbootstrap.constants import *


def build_about_tab(self, tab):
    shell = ttk.Frame(tab)
    shell.pack(fill="both", expand=True)
    shell.grid_columnconfigure(0, weight=3)
    shell.grid_columnconfigure(1, weight=2)

    intro = ttk.Labelframe(shell, text="A propos du projet", style="Card.TLabelframe", bootstyle=PRIMARY)
    intro.grid(row=0, column=0, sticky="nsew", padx=(8, 5), pady=(4, 8))

    ttk.Label(intro, text="SupportX App", style="Hero.TLabel", bootstyle=PRIMARY).pack(anchor="w", padx=10, pady=(8, 2))
    ttk.Label(intro, text=f"Version {self.current_version}", style="CardTitle.TLabel", bootstyle=INFO).pack(
        anchor="w", padx=10, pady=(0, 8)
    )
    ttk.Label(
        intro,
        text=(
            "Cette application centralise l'acces a SupportX, la verification des mises a jour "
            "et les reglages de l'environnement utilisateur."
        ),
        style="Muted.TLabel",
        wraplength=620,
        justify="left",
    ).pack(anchor="w", padx=10, pady=(0, 12))

    features = ttk.Labelframe(shell, text="Fonctionnalites", style="Card.TLabelframe", bootstyle=SUCCESS)
    features.grid(row=0, column=1, sticky="nsew", padx=(5, 8), pady=(4, 8))

    items = [
        "Interface unifiee pour SupportX",
        "Verification et installation de mises a jour",
        "Historique integre via webview",
        "Themes et options utilisateur persistantes",
        "Ouverture rapide dans le navigateur externe",
    ]
    for item in items:
        ttk.Label(features, text=f"• {item}", style="Muted.TLabel").pack(anchor="w", padx=10, pady=4)

    footer = ttk.Frame(shell)
    footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(2, 6))
    ttk.Separator(footer, orient="horizontal").pack(fill="x", pady=(0, 8))
    ttk.Label(
        footer,
        text="© 2026 SupportX - Tous droits reserves",
        style="Muted.TLabel",
        bootstyle=SECONDARY,
    ).pack(anchor="e")
