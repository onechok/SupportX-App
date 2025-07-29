import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinterweb import HtmlFrame
from PIL import Image, ImageTk
import webbrowser
import os
import platform
import sys
import darkdetect
from theme_manager import ThemeManager
from update_manager import UpdateManager
from tabs.main_tab import build_main_tab
from tabs.web_tab import build_web_tab
from tabs.about_tab import build_about_tab
from tabs.settings_tab import build_settings_tab
from tabs.history_tab import build_history_tab  # Nouvelle importation pour l'onglet Historique

class SuperAppLauncher:
    def __init__(self, root):
        self.root = root
        self.theme_manager = ThemeManager()
        config = self.theme_manager.config
        self.root.title(f"{config['app_name']} - Version {config['app_version']}")
        self.root.geometry("1100x650")
        self.root.minsize(900, 600)
        self.style = ttk.Style()
        self.apply_theme()
        icon_path = self.resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Erreur lors du chargement de l'icône : {e}")
        self.current_version = config['app_version']
        self.supportx_url = config['supportx_url']
        self.setup_main_ui()
        self.update_manager = UpdateManager(self, config)
        if config['auto_update']:
            self.check_for_updates(manual=False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def apply_theme(self):
        if self.theme_manager.config["theme"] == "system":
            self.style.theme_use("darkly" if darkdetect.isDark() else "flatly")
        else:
            self.style.theme_use(self.theme_manager.config["theme"])

    def setup_main_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)
        main_tab = ttk.Frame(self.notebook)
        self.web_tab = ttk.Frame(self.notebook)
        about_tab = ttk.Frame(self.notebook)
        settings_tab = ttk.Frame(self.notebook)
        history_tab = ttk.Frame(self.notebook)  # Nouvelle frame pour l'onglet Historique
        self.notebook.add(main_tab, text="Accueil")
        self.notebook.add(self.web_tab, text="SupportX")
        self.notebook.add(about_tab, text="À propos")
        self.notebook.add(settings_tab, text="Paramètres")
        self.notebook.add(history_tab, text="Historique")  # Ajout de l'onglet Historique
        build_main_tab(self, main_tab)
        build_web_tab(self)
        build_about_tab(self, about_tab)
        build_settings_tab(self, settings_tab)
        build_history_tab(self, history_tab)  # Construction du contenu de l'onglet Historique
        self.status_bar = ttk.Label(
            self.root,
            text=f"Version {self.current_version} | © 2025 SupportX",
            bootstyle=SECONDARY,
            anchor="center",
            font=("Arial", 9)
        )
        self.status_bar.pack(fill="x", side="bottom", padx=5, pady=5)

    def check_for_updates(self, manual=False):
        if manual or self.theme_manager.config["auto_update"]:
            self.update_manager.check_for_updates(manual)

    def open_web_tab(self):
        self.notebook.select(self.web_tab)

    def open_in_browser(self):
        webbrowser.open(self.supportx_url)

    def refresh_webview(self):
        if hasattr(self, 'web_frame') and self.web_frame:
            self.web_frame.reload()

    def load_webview(self, url):
        if hasattr(self, 'web_frame') and self.web_frame:
            self.web_frame.load_url(url)

    def open_app_folder(self):
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

    def save_auto_update_setting(self):
        self.theme_manager.config["auto_update"] = self.auto_update_var.get()
        self.theme_manager.save_config()

    def save_simulate_setting(self):
        self.theme_manager.config["simulate_updates"] = self.simulate_var.get()
        self.theme_manager.save_config()
        self.status_bar.config(text="Paramètre de simulation sauvegardé")

    def change_theme(self, event):
        self.theme_manager.config["theme"] = self.theme_var.get()
        self.theme_manager.save_config()
        self.apply_theme()
        self.status_bar.config(text="Thème modifié - Redémarrez l'application pour appliquer complètement")

    def on_closing(self):
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'application?"):
            self.root.destroy()

def main():
    root = ttk.Window()
    app = SuperAppLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()