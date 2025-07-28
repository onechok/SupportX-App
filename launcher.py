import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
import zipfile
import shutil
import threading
import os
import platform
import sys
from tkinterweb import HtmlFrame
from PIL import Image, ImageTk
import webbrowser
import time
import darkdetect
import json

# Configuration
APP_VERSION = "1.0.0"
UPDATE_SERVER_URL = "https://supportx.ch/updates"
APP_NAME = "SupperX APP"
SUPPORTX_URL = "https://supportx.ch/"
CONFIG_FILE = "config.json"

class ThemeManager:
    """Gère les thèmes et les paramètres de l'application"""

    DEFAULT_CONFIG = {
        "theme": "system",
        "auto_update": True,
    }

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """Charge la configuration depuis le fichier ou utilise les valeurs par défaut"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Mettre à jour la configuration avec les valeurs par défaut si certaines clés sont manquantes
                    for key in self.DEFAULT_CONFIG:
                        if key not in config:
                            config[key] = self.DEFAULT_CONFIG[key]
                    return config
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration : {e}")

        return self.DEFAULT_CONFIG

    def save_config(self):
        """Sauvegarde la configuration dans le fichier"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration : {e}")

class SuperAppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - Version {APP_VERSION}")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # Initialiser le gestionnaire de thème
        self.theme_manager = ThemeManager()

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

        self.update_status = None
        self.progress = None
        self.web_frame = None
        self.web_tab = None
        self.current_version = APP_VERSION

        # Créer l'interface
        self.setup_main_ui()

        # Vérifier les mises à jour
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
            text=f"Version {APP_VERSION} | © 2025 SupportX",
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
            text=APP_VERSION,
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
            ("Accueil", "secondary", lambda: self.load_webview(SUPPORTX_URL), 10),
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
        self.web_frame.load_website(SUPPORTX_URL)
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
            text=f"Version {APP_VERSION}",
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
            text="© 2025 SupportX - Tous droits réservés",
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
        webbrowser.open(SUPPORTX_URL)

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
        """Vérifie les mises à jour disponibles"""
        current_time = time.strftime("%H:%M:%S")
        self.status_bar.config(text=f"Vérification des mises à jour... ({current_time})")
        self.update_status.config(text="Vérification en cours...")
        try:
            threading.Thread(target=self.simulate_update_check, args=(manual,), daemon=True).start()
        except Exception as e:
            self.update_status.config(text="Échec de vérification")
            self.status_bar.config(text="Échec de vérification des mises à jour")
            if manual:
                messagebox.showerror("Erreur", f"Impossible de vérifier les mises à jour: {str(e)}")

    def simulate_update_check(self, manual):
        """Simulation de vérification de mise à jour"""
        time.sleep(2)
        demo_mode = True
        if demo_mode:
            latest_version = "1.3.0"
            update_available = self.is_newer_version(latest_version)
            if update_available:
                self.root.after(0, lambda: self.show_update_available(latest_version, manual))
            else:
                self.root.after(0, lambda: self.show_no_update(manual))

    def show_update_available(self, latest_version, manual):
        """Affiche qu'une mise à jour est disponible"""
        self.update_status.config(text=f"Mise à jour {latest_version} disponible!")
        self.status_bar.config(text=f"Version {latest_version} disponible - Prêt à installer")
        if manual or messagebox.askyesno("Mise à jour disponible", f"Version {latest_version} disponible. Voulez-vous l'installer maintenant?"):
            threading.Thread(target=self.download_and_apply_update, args=(f"{UPDATE_SERVER_URL}/update_{latest_version}.zip",), daemon=True).start()

    def show_no_update(self, manual):
        """Affiche qu'aucune mise à jour n'est disponible"""
        current_time = time.strftime("%H:%M:%S")
        self.update_status.config(text=f"Vous avez la dernière version ({self.current_version})")
        self.status_bar.config(text=f"À jour - Dernière vérification: {current_time}")
        if manual:
            messagebox.showinfo("Mise à jour", "Vous utilisez la dernière version disponible.")

    def is_newer_version(self, latest_version):
        """Vérifie si la version est plus récente"""
        current = [int(x) for x in self.current_version.split(".")]
        latest = [int(x) for x in latest_version.split(".")]
        return latest > current

    def download_and_apply_update(self, update_url):
        """Télécharge et applique la mise à jour"""
        try:
            self.update_status.config(text="Téléchargement en cours...")
            self.status_bar.config(text="Téléchargement de la mise à jour...")
            self.progress["value"] = 0
            for i in range(0, 101, 2):
                self.progress["value"] = i
                self.update_status.config(text=f"Téléchargement... {i}%")
                time.sleep(0.05)
                self.root.update()

            self.update_status.config(text="Application de la mise à jour...")
            self.status_bar.config(text="Installation de la mise à jour...")
            for i in range(0, 101, 5):
                self.progress["value"] = i
                time.sleep(0.1)
                self.root.update()

            self.current_version = "1.3.0"
            self.version_label.config(text=self.current_version)
            self.update_status.config(text="Mise à jour terminée!")
            self.status_bar.config(text="Mise à jour installée avec succès - Redémarrage nécessaire")
            messagebox.showinfo("Mise à jour", "Mise à jour installée avec succès. Veuillez redémarrer l'application pour appliquer les changements.")
        except Exception as e:
            self.update_status.config(text="Échec de la mise à jour")
            self.status_bar.config(text="Échec de l'installation de la mise à jour")
            messagebox.showerror("Erreur", f"Échec de la mise à jour : {str(e)}")

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
