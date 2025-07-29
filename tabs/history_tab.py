import tkinter as tk
from tkinter import ttk
from ttkbootstrap.constants import *
import webview

class BrowserFrame:
    """Simule un composant navigateur en ouvrant une fenêtre PyWebView."""
    def __init__(self, url, title="Navigateur intégré"):
        self.url = url
        self.title = title

    def open(self):
        # PyWebView doit être appelé dans le thread principal
        webview.create_window(self.title, self.url)
        webview.start()

def build_history_tab(app, tab):
    """Ajoute un bouton dans l'onglet Historique pour afficher le site dans PyWebView."""
    history_frame = ttk.Frame(tab, padding=20)
    history_frame.pack(fill="both", expand=True)

    ttk.Label(
        history_frame,
        text="Historique SupportX",
        font=("Arial", 14, "bold"),
        bootstyle=PRIMARY
    ).pack(pady=10)

    ttk.Label(
        history_frame,
        text="Cliquez sur le bouton ci-dessous pour afficher l'historique en ligne dans une fenêtre intégrée.",
        font=("Arial", 11),
        wraplength=700,
        justify="center"
    ).pack(pady=10)

    browser = BrowserFrame(url="https://supportx.ch", title="SupportX - Historique")

    ttk.Button(
        history_frame,
        text="Ouvrir l'historique Web",
        bootstyle=SUCCESS,
        command=browser.open
    ).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("SupportX App")
    root.geometry("800x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    history_tab = ttk.Frame(notebook)
    notebook.add(history_tab, text="Historique")

    build_history_tab(root, history_tab)

    root.mainloop()
