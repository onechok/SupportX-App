import os
import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip
from PIL import Image, ImageTk
import logging

def build_main_tab(self, tab):
    """Construit l'onglet principal de l'interface pour le SupportX APP Launcher."""

    # Configuration du journal de logs
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Conteneur principal avec du padding
    main_frame = ttk.Frame(tab, padding=30)
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_columnconfigure(0, weight=1)

    # Cadre de contenu centré
    content_frame = ttk.Frame(main_frame)
    content_frame.grid(row=0, column=0, sticky="nsew")
    content_frame.grid_columnconfigure(0, weight=1)

    # Section du logo avec chemin relatif
    try:
        logo_path = os.path.join("image", "logo", "Supportx_dark.png")
        img = Image.open(logo_path)
        img = img.resize((300, 100), Image.LANCZOS)
        self.logo = ImageTk.PhotoImage(img)
        logo_label = ttk.Label(content_frame, image=self.logo)
        logo_label.grid(row=0, column=0, pady=(0, 20))
        ToolTip(logo_label, text="Logo de l'application SupportX")
    except Exception as e:
        logger.error(f"Échec du chargement du logo : {e}")
        logo_label = ttk.Label(
            content_frame,
            text="🚀",
            font=("Arial", 48),
            bootstyle=PRIMARY
        )
        logo_label.grid(row=0, column=0, pady=(0, 20))
        ToolTip(logo_label, text="Icône par défaut du logo")

    # Titre principal
    title = ttk.Label(
        content_frame,
        text="L’outil tout-en-un pensé pour simplifier votre expérience avec SupportX",
        font=("Arial", 10, "bold"),
        bootstyle=PRIMARY
    )
    title.grid(row=1, column=0, pady=(0, 10))

    # Informations sur la version
    version_frame = ttk.Frame(content_frame)
    version_frame.grid(row=2, column=0, pady=5)
    version_frame.grid_columnconfigure(0, weight=0)
    version_frame.grid_columnconfigure(1, weight=0)

    ttk.Label(
        version_frame,
        text="Version :",
        font=("Arial", 10)
    ).grid(row=0, column=0, sticky="e")

    self.version_label = ttk.Label(
        version_frame,
        text=self.current_version,
        font=("Arial", 10, "bold"),
        bootstyle=INFO
    )
    self.version_label.grid(row=0, column=1, padx=5, sticky="w")
    ToolTip(self.version_label, text="Version actuelle de l'application")

    # Section des boutons d'action
    btn_frame = ttk.Frame(content_frame)
    btn_frame.grid(row=3, column=0, pady=20)
    btn_frame.grid_columnconfigure(0, weight=1)

    boutons = [
        {
            "text": "Vérifier les mises à jour",
            "style": SUCCESS,
            "command": lambda: self.check_for_updates(manual=True),
            "tooltip": "Vérifie les dernières mises à jour de l'application"
        },
        {
            "text": "Ouvrir SupportX",
            "style": PRIMARY,
            "command": self.open_web_tab,
            "tooltip": "Ouvre SupportX dans l'application"
        },
        {
            "text": "Ouvrir dans le navigateur",
            "style": (OUTLINE, PRIMARY),
            "command": self.open_in_browser,
            "tooltip": "Ouvre SupportX dans le navigateur par défaut"
        }
    ]

    for idx, btn_config in enumerate(boutons):
        btn = ttk.Button(
            btn_frame,
            text=btn_config["text"],
            command=btn_config["command"],
            bootstyle=btn_config["style"],
            width=20
        )
        btn.grid(row=idx, column=0, pady=8, padx=10, sticky="ew")
        ToolTip(btn, text=btn_config["tooltip"])

    # Section de statut des mises à jour
    update_frame = ttk.Labelframe(
        content_frame,
        text="Statut des mises à jour",
        bootstyle=INFO,
        padding=10
    )
    update_frame.grid(row=4, column=0, pady=20, sticky="ew")
    update_frame.grid_columnconfigure(0, weight=1)

    self.update_status = ttk.Label(
        update_frame,
        text="Dernière vérification : jamais",
        bootstyle=INFO,
        font=("Arial", 9)
    )
    self.update_status.grid(row=0, column=0, pady=5, padx=15, sticky="w")
    ToolTip(self.update_status, text="Date de la dernière vérification de mise à jour")

    self.progress = ttk.Progressbar(
        update_frame,
        bootstyle="info-striped",
        mode="determinate",
        maximum=100
    )
    self.progress.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")

    # Lier l'événement de redimensionnement pour un layout réactif
    main_frame.bind("<Configure>", lambda e: self._adjust_layout(content_frame))


def _adjust_layout(self, content_frame):
    """Ajuste dynamiquement le layout selon la taille de la fenêtre."""
    window_width = self.winfo_width()
    padding = max(20, window_width // 20)  # Padding dynamique
    content_frame.configure(padding=padding)
