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
        "Interface unifiée pour SupportX",
        "Vérification et installation de mises à jour",
        "Historique intégré via webview",
        "Themes et options utilisateur persistantes",
        "Ouverture rapide dans le navigateur externe",
        "Dashboard TikTok multi-événements (chat, likes, cadeaux)",
        "Gestion multi-utilisateur TikTok (favoris, sélection rapide)",
        "Lecture audio personnalisée sur chaque événement TikTok",
        "Scroll automatique des listes (chat, likes, cadeaux)",
        "Diagnostic audio et fallback automatique sur test.wav",
        "Conversion automatique des sons en PCM 16 bits 44100 Hz mono",
        "Logs d'événements TikTok et sauvegarde JSON",
        "Multiprocessing pour l'isolation TikTokLive/Qt",
    ]
    for item in items:
        ttk.Label(features, text=f"• {item}", style="Muted.TLabel").pack(anchor="w", padx=10, pady=4)

    # Historique des versions
    changelog = ttk.Labelframe(shell, text="Historique des versions (essentiel)", style="Card.TLabelframe", bootstyle=WARNING)
    changelog.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 8))
    versions = [
        "v0.2.0 : Dashboard TikTok complet (chat, likes, cadeaux, favoris, audio, scroll auto, logs, multiprocessing)",
        "v0.1.9 : Conversion automatique des sons, fallback test.wav, fiabilisation audio",
        "v0.1.8 : Ajout gestion multi-utilisateur TikTok (favoris)",
        "v0.1.7 : Scroll automatique, logs d'événements TikTok, sauvegarde JSON",
        "v0.1.6 : Séparation multiprocessing TikTokLive/Qt, robustesse UI",
        "v0.1.5 : Ajout diagnostic audio, options volume, options sons",
        "v0.1.4 : Intégration TikTokLive, gestion chat/likes/cadeaux",
        "v0.1.3 : Ajout onglet TikTok Dashboard, intégration UI",
        "v0.1.2 : Ajout onglet YouTube, AnyDesk, jeux, diagnostic",
        "v0.1.1 : Première version publique SupportX App",
    ]
    for v in versions:
        ttk.Label(changelog, text=f"• {v}", style="Muted.TLabel").pack(anchor="w", padx=10, pady=2)

    # Dépendances principales
    deps = ttk.Labelframe(shell, text="Dépendances principales", style="Card.TLabelframe", bootstyle=INFO)
    deps.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 8))
    dep_list = [
        "PySide6 (UI Qt)",
        "TikTokLive (API TikTok)",
        "yt-dlp (YouTube)",
        "pygame (audio, jeux)",
        "multiprocessing (processus TikTok)",
        "ttkbootstrap (UI Tkinter)",
        "requests, rich, vispy, pytmx, PyCraft...",
    ]
    for d in dep_list:
        ttk.Label(deps, text=f"• {d}", style="Muted.TLabel").pack(anchor="w", padx=10, pady=2)

    footer = ttk.Frame(shell)
    footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(2, 6))
    ttk.Separator(footer, orient="horizontal").pack(fill="x", pady=(0, 8))
    ttk.Label(
        footer,
        text="© 2026 SupportX - Tous droits reserves",
        style="Muted.TLabel",
        bootstyle=SECONDARY,
    ).pack(anchor="e")
