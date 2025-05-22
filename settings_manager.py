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
                "speaker_id": 1
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
                # Get node or create one
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
                with open(self.settings_file_path, "r") as f:
                    loaded_settings = json.load(f)
                # Merge loaded settings with defaults to ensure all keys are present
                # and to add new default settings if the file is from an older version.
                # Default settings are the base, loaded settings override them.
                merged_settings = self.default_settings.copy() # Start with a copy of defaults
                return self._deep_merge_dicts(loaded_settings, merged_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings file '{self.settings_file_path}'. Error: {e}. Using default settings.")
                return self.default_settings.copy()
        else:
            # If the file doesn't exist, return a copy of the default settings.
            return self.default_settings.copy()

    def save_settings(self):
        """
        Saves the current settings to the settings file.
        """
        try:
            with open(self.settings_file_path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error: Could not save settings to '{self.settings_file_path}'. Error: {e}")

    def get_setting(self, key, sub_key=None):
        """
        Retrieves a setting value.

        Args:
            key (str): The main setting key.
            sub_key (str, optional): The sub-key for nested settings. Defaults to None.

        Returns:
            The value of the setting, or None if not found.
        """
        if sub_key:
            return self.settings.get(key, {}).get(sub_key)
        else:
            return self.settings.get(key)

    def update_setting(self, key, value, sub_key=None):
        """
        Updates a setting and saves all settings to the file.

        Args:
            key (str): The main setting key.
            value: The new value for the setting.
            sub_key (str, optional): The sub-key for nested settings. Defaults to None.
        """
        if sub_key:
            if key not in self.settings or not isinstance(self.settings[key], dict):
                self.settings[key] = {}  # Initialize if key doesn't exist or is not a dict
            self.settings[key][sub_key] = value
        else:
            self.settings[key] = value
        self.save_settings()

if __name__ == '__main__':
    # Example Usage
    settings_manager = SettingsManager(settings_file_path="test_app_settings.json")
    
    print("Initial settings:", settings_manager.settings)
    
    # Test getting settings
    print("\nGetting 'appearance' theme:", settings_manager.get_setting("appearance", "theme"))
    print("Getting 'voice_mode_on':", settings_manager.get_setting("voice_mode_on"))
    print("Getting non-existent key:", settings_manager.get_setting("non_existent_key"))

    # Test updating settings
    settings_manager.update_setting("voice_mode_on", True)
    print("\nUpdated 'voice_mode_on':", settings_manager.get_setting("voice_mode_on"))
    
    settings_manager.update_setting("primary_llm", "gpt-4", "model")
    print("Updated 'primary_llm' model:", settings_manager.get_setting("primary_llm", "model"))

    settings_manager.update_setting("appearance", "large", "font_size")
    print("Updated 'appearance' font_size:", settings_manager.get_setting("appearance", "font_size"))

    # Test saving (implicitly tested by update_setting, but can be called directly)
    # settings_manager.save_settings() 
    
    # Test loading with a pre-existing file (run script again after first run)
    print("\nReloading settings from file (if it exists from a previous run):")
    settings_manager_reloaded = SettingsManager(settings_file_path="test_app_settings.json")
    print("Reloaded settings:", settings_manager_reloaded.settings)
    
    # Clean up the test file
    if os.path.exists("test_app_settings.json"):
        os.remove("test_app_settings.json")
        print("\nCleaned up test_app_settings.json")
