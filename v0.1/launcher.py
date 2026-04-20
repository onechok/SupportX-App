import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import os
import platform
import sys
from tkinterweb import HtmlFrame
from PIL import Image, ImageTk
import webbrowser
import time
import darkdetect  # Added missing import
from theme_manager import ThemeManager  # Import the new ThemeManager
from update_manager import UpdateManager  # Import du gestionnaire de mises à jour

class SuperAppLauncher:
    def __init__(self, root):
        self.root = root
        self.theme_manager = ThemeManager()
        config = self.theme_manager.config

        self.root.title(f"{config['app_name']} o- Version {config['app_version']}")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # Initialiser le style
        self.style = ttk.Style()
        self.apply_theme()

        # Configuration de l'icône
        icon_path = self.resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Erreur lors du chargement de l'icône : {e}")

        # Variables d'interface
        self.update_status = None
        self.progress = None
        self.web_frame = None
        self.web_tab = None
        self.current_version = config['app_version']
        self.supportx_url = config['supportx_url']

        # Créer l'interface
        self.setup_main_ui()

        # Initialiser le gestionnaire de mises à jour
        self.update_manager = UpdateManager(self, config)

        # Vérifier les mises à jour SEULEMENT si auto_update est activé
        if config['auto_update']:
            self.check_for_updates(manual=False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def resource_path(self, relative_path):
        """Récupère le chemin absolu pour les ressources"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def apply_theme(self):
        """Applique le thème à l'application"""
        if self.theme_manager.config["theme"] == "system":
            self.style.theme_use("darkly" if darkdetect.isDark() else "flatly")
        else:
            self.style.theme_use(self.theme_manager.config["theme"])

    def setup_main_ui(self):
        # Création du notebook pour les onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        # Onglets
        main_tab = ttk.Frame(self.notebook)
        self.web_tab = ttk.Frame(self.notebook)
        about_tab = ttk.Frame(self.notebook)
        settings_tab = ttk.Frame(self.notebook)

        self.notebook.add(main_tab, text="Accueil")
        self.notebook.add(self.web_tab, text="SupportX")
        self.notebook.add(about_tab, text="À propos")
        self.notebook.add(settings_tab, text="Paramètres")

        # Construire chaque onglet
        self.build_main_tab(main_tab)
        self.build_web_tab()
        self.build_about_tab(about_tab)
        self.build_settings_tab(settings_tab)

        # Barre de statut
        self.status_bar = ttk.Label(
            self.root,
            text=f"Version {self.current_version} | © 2023 SupportX",
            bootstyle=SECONDARY,
            anchor="center",
            font=("Arial", 9)
        )
        self.status_bar.pack(fill="x", side="bottom", padx=5, pady=5)

    def build_main_tab(self, tab):
        """Construit l'onglet principal avec un design épuré"""
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(expand=True)

        try:
            img = Image.open(self.resource_path("logo.png"))
            img = img.resize((100, 100), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            logo_label = ttk.Label(content_frame, image=self.logo)
            logo_label.pack(pady=(0, 20))
        except Exception as e:
            print(f"Erreur lors du chargement du logo : {e}")
            logo_label = ttk.Label(
                content_frame,
                text="🚀",
                font=("Arial", 48),
                bootstyle=PRIMARY
            )
            logo_label.pack(pady=(0, 20))

        title = ttk.Label(
            content_frame,
            text="SuperApp Launcher",
            font=("Arial", 20, "bold"),
            bootstyle=PRIMARY
        )
        title.pack(pady=(0, 5))

        version_frame = ttk.Frame(content_frame)
        version_frame.pack(pady=5)

        ttk.Label(version_frame, text="Version:", font=("Arial", 10)).pack(side="left")
        self.version_label = ttk.Label(
            version_frame,
            text=self.current_version,
            font=("Arial", 10, "bold"),
            bootstyle=INFO
        )
        self.version_label.pack(side="left", padx=5)

        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(pady=20)

        buttons = [
            ("Vérifier les mises à jour", SUCCESS, lambda: self.check_for_updates(manual=True)),
            ("Ouvrir SupportX", PRIMARY, self.open_web_tab),
            ("Ouvrir dans navigateur", (OUTLINE, PRIMARY), self.open_in_browser)
        ]

        for text, style, command in buttons:
            btn = ttk.Button(
                btn_frame,
                text=text,
                command=command,
                bootstyle=style,
                width=20
            )
            btn.pack(pady=8)

        update_frame = ttk.Labelframe(
            content_frame,
            text="Mise à jour",
            bootstyle=INFO
        )
        update_frame.pack(fill="x", pady=20)

        self.update_status = ttk.Label(
            update_frame,
            text="Dernière vérification: jamais",
            bootstyle=INFO,
            font=("Arial", 9)
        )
        self.update_status.pack(pady=5, padx=15, anchor="w")

        self.progress = ttk.Progressbar(
            update_frame,
            bootstyle="info-striped",
            mode="determinate"
        )
        self.progress.pack(fill="x", padx=15, pady=(0, 15))

    def build_web_tab(self):
        """Construit l'onglet avec le site Next.js dans un design minimaliste"""
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

    def build_about_tab(self, tab):
        """Onglet À propos avec design minimal"""
        about_frame = ttk.Frame(tab, padding=30)
        about_frame.pack(fill="both", expand=True)

        ttk.Label(
            about_frame,
            text="SuperApp Launcher",
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

        ttk.Label(
            about_frame,
            text="© 2023 SupportX - Tous droits réservés",
            font=("Arial", 9),
            bootstyle=SECONDARY
        ).pack(side="bottom", pady=10)

    def build_settings_tab(self, tab):
        """Onglet Paramètres avec options de personnalisation"""
        settings_frame = ttk.Frame(tab, padding=20)
        settings_frame.pack(fill="both", expand=True)

        theme_frame = ttk.Labelframe(
            settings_frame,
            text="Personnalisation de l'interface",
            bootstyle=INFO
        )
        theme_frame.pack(fill="x", pady=10, padx=5)

        ttk.Label(
            theme_frame,
            text="Thème de l'application:",
            font=("Arial", 10)
        ).pack(padx=10, pady=(10, 5), anchor="w")

        self.theme_var = tk.StringVar(value=self.theme_manager.config["theme"])
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["system", "darkly", "flatly", "vapor", "minty"],
            state="readonly",
            width=15
        )
        theme_combo.pack(padx=10, pady=(0, 10), anchor="w")
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)

        update_frame = ttk.Labelframe(
            settings_frame,
            text="Mises à jour automatiques",
            bootstyle=INFO
        )
        update_frame.pack(fill="x", pady=10, padx=5)

        self.auto_update_var = tk.BooleanVar(value=self.theme_manager.config["auto_update"])
        auto_update_check = ttk.Checkbutton(
            update_frame,
            text="Vérifier automatiquement les mises à jour",
            variable=self.auto_update_var,
            bootstyle="round-toggle",
            command=self.save_auto_update_setting
        )
        auto_update_check.pack(padx=10, pady=10, anchor="w")

        # Nouveau cadre pour la simulation des mises à jour
        simulation_frame = ttk.Labelframe(
            settings_frame,
            text="Mode Développeur",
            bootstyle=INFO
        )
        simulation_frame.pack(fill="x", pady=10, padx=5)

        self.simulate_var = tk.BooleanVar(value=self.theme_manager.config["simulate_updates"])
        simulate_check = ttk.Checkbutton(
            simulation_frame,
            text="Activer la simulation des mises à jour",
            variable=self.simulate_var,
            bootstyle="round-toggle",
            command=self.save_simulate_setting
        )
        simulate_check.pack(padx=10, pady=10, anchor="w")

        advanced_frame = ttk.Labelframe(
            settings_frame,
            text="Paramètres avancés",
            bootstyle=WARNING
        )
        advanced_frame.pack(fill="x", pady=10, padx=5)

        ttk.Button(
            advanced_frame,
            text="Ouvrir le dossier de l'application",
            command=self.open_app_folder,
            bootstyle=(OUTLINE, WARNING)
        ).pack(padx=10, pady=10, anchor="w")

        ttk.Button(
            advanced_frame,
            text="Forcer la vérification des mises à jour",
            command=lambda: self.check_for_updates(manual=True),
            bootstyle=(OUTLINE, WARNING)
        ).pack(padx=10, pady=(0, 10), anchor="w")

    def save_auto_update_setting(self):
        """Sauvegarde le paramètre de mise à jour automatique"""
        self.theme_manager.config["auto_update"] = self.auto_update_var.get()
        self.theme_manager.save_config()

    def save_simulate_setting(self):
        """Sauvegarde le paramètre de simulation des mises à jour"""
        self.theme_manager.config["simulate_updates"] = self.simulate_var.get()
        self.theme_manager.save_config()
        self.status_bar.config(text="Paramètre de simulation sauvegardé")

    def change_theme(self, event):
        """Change le thème de l'application"""
        self.theme_manager.config["theme"] = self.theme_var.get()
        self.theme_manager.save_config()
        self.apply_theme()
        self.status_bar.config(text="Thème modifié - Redémarrez l'application pour appliquer complètement")

    def refresh_webview(self):
        """Rafraîchit la page web"""
        if self.web_frame:
            self.web_frame.reload()

    def load_webview(self, url):
        """Charge une URL spécifique dans la webview"""
        if self.web_frame:
            self.web_frame.load_url(url)

    def open_web_tab(self):
        """Ouvre l'onglet SupportX"""
        self.notebook.select(self.web_tab)

    def open_in_browser(self):
        """Ouvre le site dans le navigateur par défaut"""
        webbrowser.open(self.supportx_url)

    def open_app_folder(self):
        """Ouvre le dossier de l'application"""
        app_path = os.path.dirname(os.path.abspath(__file__))
        try:
            if platform.system() == "Windows":
                os.startfile(app_path)
            elif platform.system() == "Darwin":
                os.system(f"open '{app_path}'")
            else:
                os.system(f"xdg-open '{app_path}'")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier: {str(e)}")

    def check_for_updates(self, manual=False):
        """Vérifie les mises à jour seulement si autorisé"""
        # Toujours autoriser les vérifications manuelles
        # Pour les automatiques, vérifier si auto_update est activé
        if manual or self.theme_manager.config["auto_update"]:
            self.update_manager.check_for_updates(manual)

    def on_closing(self):
        """Gestion de la fermeture de l'application"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'application?"):
            self.root.destroy()

def main():
    root = ttk.Window()
    app = SuperAppLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()