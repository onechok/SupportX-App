from tkinter import ttk

from tkinterweb import HtmlFrame
from ttkbootstrap.constants import *


def build_web_tab(self):
    shell = ttk.Frame(self.web_tab)
    shell.pack(fill="both", expand=True, padx=0, pady=0)

    self.web_frame = HtmlFrame(shell, messages_enabled=False)
    self.web_frame.pack(fill="both", expand=True)
    self.web_frame.load_website(self.supportx_url)
