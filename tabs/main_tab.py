import os
from tkinter import ttk

from PIL import Image, ImageTk
from ttkbootstrap.constants import *


def build_main_tab(self, tab):
    shell = ttk.Frame(tab)
    shell.pack(fill="both", expand=True)
    shell.grid_columnconfigure(0, weight=3)
    shell.grid_columnconfigure(1, weight=2)
    shell.grid_rowconfigure(1, weight=1)

    hero_card = ttk.Labelframe(shell, text="Tableau de bord", style="Card.TLabelframe", bootstyle=PRIMARY)
    hero_card.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=8, pady=(4, 10))
    hero_card.grid_columnconfigure(1, weight=1)

    logo_path = os.path.join("image", "logo", "Supportx_dark.png")
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path).resize((220, 70), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            ttk.Label(hero_card, image=self.logo).grid(row=0, column=0, rowspan=2, padx=(6, 18), pady=6, sticky="w")
        except Exception:
            ttk.Label(hero_card, text="SupportX", style="CardTitle.TLabel", bootstyle=PRIMARY).grid(
                row=0, column=0, padx=(6, 18), sticky="w"
            )

    ttk.Label(
        hero_card,
        text="Une interface modernisee pour piloter SupportX rapidement.",
        style="CardTitle.TLabel",
        bootstyle=PRIMARY,
    ).grid(row=0, column=1, sticky="w", pady=(4, 2))
    ttk.Label(
        hero_card,
        text=f"Version active: {self.current_version}",
        style="Muted.TLabel",
        bootstyle=SECONDARY,
    ).grid(row=1, column=1, sticky="w", pady=(0, 6))

    quick_actions = ttk.Labelframe(shell, text="Actions rapides", style="Card.TLabelframe", bootstyle=SUCCESS)
    quick_actions.grid(row=1, column=0, sticky="nsew", padx=(8, 5), pady=(0, 8))
    quick_actions.grid_columnconfigure(0, weight=1)

    ttk.Button(
        quick_actions,
        text="Verifier les mises a jour",
        bootstyle=SUCCESS,
        command=lambda: self.check_for_updates(manual=True),
    ).grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))

    ttk.Button(
        quick_actions,
        text="Ouvrir SupportX integre",
        bootstyle=PRIMARY,
        command=self.open_web_tab,
    ).grid(row=1, column=0, sticky="ew", padx=8, pady=6)

    ttk.Button(
        quick_actions,
        text="Ouvrir dans le navigateur",
        bootstyle=(OUTLINE, PRIMARY),
        command=self.open_in_browser,
    ).grid(row=2, column=0, sticky="ew", padx=8, pady=(6, 10))

    update_card = ttk.Labelframe(shell, text="Etat des mises a jour", style="Card.TLabelframe", bootstyle=INFO)
    update_card.grid(row=1, column=1, sticky="nsew", padx=(5, 8), pady=(0, 8))
    update_card.grid_columnconfigure(0, weight=1)

    self.update_status = ttk.Label(
        update_card,
        text="Derniere verification: jamais",
        style="CardTitle.TLabel",
        bootstyle=INFO,
    )
    self.update_status.grid(row=0, column=0, padx=10, pady=(10, 8), sticky="w")

    ttk.Label(
        update_card,
        text="Le telechargement et l'installation seront suivis ici en temps reel.",
        style="Muted.TLabel",
        bootstyle=SECONDARY,
        wraplength=340,
        justify="left",
    ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

    self.progress = ttk.Progressbar(update_card, bootstyle="info-striped", mode="determinate", maximum=100)
    self.progress.grid(row=2, column=0, padx=10, pady=(0, 12), sticky="ew")
