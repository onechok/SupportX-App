from tkinter import ttk
import tkinter as tk
import os
from ttkbootstrap.constants import *

def build_about_tab(self, tab):
    about_frame = ttk.Frame(tab, padding=30)
    about_frame.pack(fill="both", expand=True)

    ttk.Label(
        about_frame,
        text="SupportX App Launcher (beta)",
        font=("Arial", 22, "bold"),
        bootstyle=PRIMARY
    ).pack(pady=(10, 5))

    ttk.Label(
        about_frame,
        text=f"Version {self.current_version}",
        font=("Arial", 12),
        bootstyle=INFO
    ).pack(pady=5)

    ttk.Label(
        about_frame,
        text="Cette application permet de lancer et de maintenir à jour\nSuperApp avec un accès intégré à SupportX.",
        font=("Arial", 11),
        justify="center"
    ).pack(pady=20)

    ttk.Label(
        about_frame,
        text="Fonctionnalités:",
        font=("Arial", 12, "bold")
    ).pack(pady=10, anchor="w")

    features = [
        "✓ Mises à jour automatiques de l'application",
        "✓ Interface intégrée pour SupportX",
        "✓ Vérification périodique des versions",
        "✓ Processus de mise à jour sécurisé",
        "✓ Interface utilisateur moderne et intuitive"
    ]

    for feature in features:
        ttk.Label(
            about_frame,
            text=feature,
            font=("Arial", 10)
        ).pack(anchor="w", padx=20, pady=2)

    ttk.Separator(about_frame, orient="horizontal").pack(fill="x", pady=25)

    # --- Logo PNG centré au-dessus du copyright ---
    image_path = os.path.join("image", "logo", "Supportx_dark.png")
    if os.path.exists(image_path):
        logo_img = tk.PhotoImage(file=image_path)
        logo_label = ttk.Label(about_frame, image=logo_img)
        logo_label.image = logo_img  # garder une référence à l'image
        logo_label.pack(pady=(0, 10))

    # Copyright en bas
    ttk.Label(
        about_frame,
        text="© 2025 SupportX - Tous droits réservés",
        font=("Arial", 9),
        bootstyle=SECONDARY
    ).pack(side="bottom", pady=10)
