from tkinter import ttk, StringVar, BooleanVar
from ttkbootstrap.constants import *

def build_settings_tab(self, tab):
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

    self.theme_var = StringVar(value=self.theme_manager.config["theme"])
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

    self.auto_update_var = BooleanVar(value=self.theme_manager.config["auto_update"])
    auto_update_check = ttk.Checkbutton(
        update_frame,
        text="Vérifier automatiquement les mises à jour",
        variable=self.auto_update_var,
        bootstyle="round-toggle",
        command=self.save_auto_update_setting
    )
    auto_update_check.pack(padx=10, pady=10, anchor="w")

    simulation_frame = ttk.Labelframe(
        settings_frame,
        text="Mode Développeur",
        bootstyle=INFO
    )
    simulation_frame.pack(fill="x", pady=10, padx=5)

    self.simulate_var = BooleanVar(value=self.theme_manager.config["simulate_updates"])
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
