import json
import os

class SettingsManager:
    """
    Manages application settings, loading them from and saving them to a JSON file.
    """
    def __init__(self, settings_file_path="app_settings.json"):
        """
        Initializes the SettingsManager.

        Args:
            settings_file_path (str): The path to the settings file.
        """
        self.settings_file_path = settings_file_path
        self.default_settings = {
            "primary_llm": {
                "api_base_url": "",
                "api_key": "",
                "model": "default_model",
                "temperature": 0.7,
                "system_prompt": "You are a helpful assistant."
            },
            "translation_llm": {
                "api_base_url": "",
                "api_key": "",
                "model": "default_translator_model",
                "temperature": 0.7,
                "system_prompt": "Translate the following text to Japanese."
            },
            "voicevox": {
                "engine_address": "http://localhost:50021",
                "speaker_id": 1 # As per Step 9, this is an entry field, so just an ID.
            },
            "appearance": {
                "theme": "system",  # Options: "system", "light", "dark"
                "font_size": "medium"  # Options: "small", "medium", "large"
            },
            "voice_mode_on": False
        }
        self.settings = self.load_settings()

    def _deep_merge_dicts(self, source, destination):
        """
        Recursively merges source dictionary into destination dictionary.
        Nested dictionaries are merged as well.
        """
        for key, value in source.items():
            if isinstance(value, dict):
                node = destination.setdefault(key, {})
                self._deep_merge_dicts(value, node)
            else:
                destination[key] = value
        return destination

    def load_settings(self):
        """
        Loads settings from the settings file.
        If the file doesn't exist or is corrupted, returns default settings.
        Merges loaded settings with default settings to ensure all keys are present.
        """
        if os.path.exists(self.settings_file_path):
            try:
                with open(self.settings_file_path, "r", encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Merge loaded settings with defaults to ensure all keys are present
                merged_settings = self.default_settings.copy() 
                return self._deep_merge_dicts(loaded_settings, merged_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings file '{self.settings_file_path}'. Error: {e}. Using default settings.")
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()

    def save_settings(self):
        """
        Saves the current settings to the settings file.
        """
        try:
            with open(self.settings_file_path, "w", encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save settings to '{self.settings_file_path}'. Error: {e}")

    def get_setting(self, key, sub_key=None):
        """
        Retrieves a setting value.
        """
        if sub_key:
            return self.settings.get(key, {}).get(sub_key)
        else:
            return self.settings.get(key)

    def update_setting(self, key, value, sub_key=None):
        """
        Updates a setting and saves all settings to the file.
        """
        if sub_key:
            if key not in self.settings or not isinstance(self.settings[key], dict):
                self.settings[key] = {}
            self.settings[key][sub_key] = value
        else:
            self.settings[key] = value
        self.save_settings()

if __name__ == '__main__':
    # Example Usage
    manager = SettingsManager(settings_file_path="test_settings.json")
    print("Initial settings:", manager.settings)
    manager.update_setting("primary_llm", "test_value", "api_key")
    print("Updated settings:", manager.settings)
    if os.path.exists("test_settings.json"):
        os.remove("test_settings.json")
        print("Cleaned up test_settings.json")
