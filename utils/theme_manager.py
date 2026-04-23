import json
import os

class ThemeManager:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), '../config/config.json')
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
                "app_name": "Supportx APP Launcher",
                "app_version": "0.2.0",
                "supportx_url": "https://supportx.ch"
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
