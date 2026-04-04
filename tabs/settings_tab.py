from tkinter import BooleanVar, StringVar, ttk

from ttkbootstrap.constants import *


def build_settings_tab(self, tab):
    shell = ttk.Frame(tab)
    shell.pack(fill="both", expand=True)
    shell.grid_columnconfigure(0, weight=1)
    shell.grid_columnconfigure(1, weight=1)

    appearance = ttk.Labelframe(shell, text="Apparence", style="Card.TLabelframe", bootstyle=INFO)
    appearance.grid(row=0, column=0, sticky="nsew", padx=(8, 5), pady=(4, 8))

    ttk.Label(appearance, text="Theme global", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(8, 4))
    self.theme_var = StringVar(value=self.theme_manager.config["theme"])
    theme_combo = ttk.Combobox(
        appearance,
        textvariable=self.theme_var,
        values=["system", "darkly", "flatly", "minty", "litera", "morph"],
        state="readonly",
        width=18,
    )
    theme_combo.pack(anchor="w", padx=10, pady=(0, 10))
    theme_combo.bind("<<ComboboxSelected>>", self.change_theme)

    updates = ttk.Labelframe(shell, text="Mises a jour", style="Card.TLabelframe", bootstyle=SUCCESS)
    updates.grid(row=0, column=1, sticky="nsew", padx=(5, 8), pady=(4, 8))

    self.auto_update_var = BooleanVar(value=self.theme_manager.config["auto_update"])
    ttk.Checkbutton(
        updates,
        text="Verifier automatiquement les mises a jour",
        variable=self.auto_update_var,
        bootstyle="round-toggle",
        command=self.save_auto_update_setting,
    ).pack(anchor="w", padx=10, pady=(10, 6))

    self.simulate_var = BooleanVar(value=self.theme_manager.config["simulate_updates"])
    ttk.Checkbutton(
        updates,
        text="Activer le mode simulation",
        variable=self.simulate_var,
        bootstyle="round-toggle",
        command=self.save_simulate_setting,
    ).pack(anchor="w", padx=10, pady=(0, 10))

    advanced = ttk.Labelframe(shell, text="Actions systeme", style="Card.TLabelframe", bootstyle=WARNING)
    advanced.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))

    actions = ttk.Frame(advanced)
    actions.pack(fill="x", padx=10, pady=10)

    ttk.Button(
        actions,
        text="Ouvrir le dossier de l'application",
        bootstyle=(OUTLINE, WARNING),
        command=self.open_app_folder,
    ).pack(side="left", padx=(0, 8))
    ttk.Button(
        actions,
        text="Verifier maintenant",
        bootstyle=WARNING,
        command=lambda: self.check_for_updates(manual=True),
    ).pack(side="left")
