import json
import os

class ThemeManager:
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "theme": "system",
                "auto_update": True,
                "simulate_updates": False,
                "app_name": "SuperApp Launcher",
                "app_version": "1.0.0",
                "supportx_url": "https://supportx.com"
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
