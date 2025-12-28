import yaml
import os

class ConfigManager:
    def __init__(self, config_path="level_maze/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            # Fallback path if running from different context
            abs_path = os.path.join(os.path.dirname(__file__), "config.yaml")
            if os.path.exists(abs_path):
                self.config_path = abs_path
            else:
                raise FileNotFoundError(f"Config file not found at {self.config_path}")

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_window_config(self):
        return self.config.get("window", {})

    def get_ability_config(self, ability_name):
        return self.config.get("abilities", {}).get(ability_name, {})
