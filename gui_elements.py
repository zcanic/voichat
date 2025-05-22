import customtkinter as ctk
from settings_manager import SettingsManager

# --- SettingsPanel Class (collapsed for brevity, no changes here) ---
class SettingsPanel(ctk.CTkToplevel):
    def __init__(self, parent, settings_manager: SettingsManager, app): # Added app parameter
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)
        self.grab_set()
        self.settings_manager = settings_manager
        self.app = app # Store the app instance
        
        self.geometry("700x550") 

        self.tabview = ctk.CTkTabview(self, width=680, height=450) 
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tabview.add("Primary LLM")
        self.tabview.add("Translation LLM")
        self.tabview.add("Voicevox")
        self.tabview.add("Appearance & General")

        self._create_primary_llm_tab(self.tabview.tab("Primary LLM"))
        self._create_translation_llm_tab(self.tabview.tab("Translation LLM"))
        self._create_voicevox_tab(self.tabview.tab("Voicevox"))
        self._create_appearance_tab(self.tabview.tab("Appearance & General"))

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=(0,10))

        save_button = ctk.CTkButton(button_frame, text="Save & Close", command=self._save_and_close)
        save_button.pack(side="right", padx=5, pady=5)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="right", padx=5, pady=5)

    def _create_primary_llm_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab_frame, text="API Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.primary_llm_api_base_url_entry = ctk.CTkEntry(tab_frame)
        self.primary_llm_api_base_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="API Key:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.primary_llm_api_key_entry = ctk.CTkEntry(tab_frame, show="*")
        self.primary_llm_api_key_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="Model:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.primary_llm_model_entry = ctk.CTkEntry(tab_frame)
        self.primary_llm_model_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="Temperature:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        temp_slider_frame = ctk.CTkFrame(tab_frame) 
        temp_slider_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        temp_slider_frame.grid_columnconfigure(0, weight=1)
        self.primary_llm_temp_slider = ctk.CTkSlider(temp_slider_frame, from_=0.0, to=1.0, number_of_steps=100)
        self.primary_llm_temp_slider.grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        self.primary_llm_temp_value_label = ctk.CTkLabel(temp_slider_frame, text="0.7")
        self.primary_llm_temp_value_label.grid(row=0, column=1, padx=(5,0), pady=5, sticky="w")
        self.primary_llm_temp_slider.configure(command=lambda val: self.primary_llm_temp_value_label.configure(text=f"{val:.2f}"))
        ctk.CTkLabel(tab_frame, text="System Prompt:").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.primary_llm_system_prompt_text = ctk.CTkTextbox(tab_frame, height=100)
        self.primary_llm_system_prompt_text.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
        tab_frame.grid_rowconfigure(4, weight=1)
        self._load_primary_llm_settings()

    def _load_primary_llm_settings(self):
        settings = self.settings_manager.get_setting("primary_llm")
        if settings:
            self.primary_llm_api_base_url_entry.insert(0, settings.get("api_base_url", ""))
            self.primary_llm_api_key_entry.insert(0, settings.get("api_key", ""))
            self.primary_llm_model_entry.insert(0, settings.get("model", ""))
            temp = settings.get("temperature", 0.7)
            self.primary_llm_temp_slider.set(float(temp))
            self.primary_llm_temp_value_label.configure(text=f"{float(temp):.2f}")
            self.primary_llm_system_prompt_text.insert("1.0", settings.get("system_prompt", ""))
            
    def _create_translation_llm_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab_frame, text="API Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.translation_llm_api_base_url_entry = ctk.CTkEntry(tab_frame)
        self.translation_llm_api_base_url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="API Key:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.translation_llm_api_key_entry = ctk.CTkEntry(tab_frame, show="*")
        self.translation_llm_api_key_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="Model:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.translation_llm_model_entry = ctk.CTkEntry(tab_frame)
        self.translation_llm_model_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="Temperature:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        temp_slider_frame = ctk.CTkFrame(tab_frame)
        temp_slider_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        temp_slider_frame.grid_columnconfigure(0, weight=1)
        self.translation_llm_temp_slider = ctk.CTkSlider(temp_slider_frame, from_=0.0, to=1.0, number_of_steps=100)
        self.translation_llm_temp_slider.grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        self.translation_llm_temp_value_label = ctk.CTkLabel(temp_slider_frame, text="0.7")
        self.translation_llm_temp_value_label.grid(row=0, column=1, padx=(5,0), pady=5, sticky="w")
        self.translation_llm_temp_slider.configure(command=lambda val: self.translation_llm_temp_value_label.configure(text=f"{val:.2f}"))
        ctk.CTkLabel(tab_frame, text="System Prompt:").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.translation_llm_system_prompt_text = ctk.CTkTextbox(tab_frame, height=100)
        self.translation_llm_system_prompt_text.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
        tab_frame.grid_rowconfigure(4, weight=1)
        self._load_translation_llm_settings()

    def _load_translation_llm_settings(self):
        settings = self.settings_manager.get_setting("translation_llm")
        if settings:
            self.translation_llm_api_base_url_entry.insert(0, settings.get("api_base_url", ""))
            self.translation_llm_api_key_entry.insert(0, settings.get("api_key", ""))
            self.translation_llm_model_entry.insert(0, settings.get("model", ""))
            temp = settings.get("temperature", 0.7)
            self.translation_llm_temp_slider.set(float(temp))
            self.translation_llm_temp_value_label.configure(text=f"{float(temp):.2f}")
            self.translation_llm_system_prompt_text.insert("1.0", settings.get("system_prompt", ""))

    def _create_voicevox_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab_frame, text="Engine Address:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.voicevox_engine_address_entry = ctk.CTkEntry(tab_frame)
        self.voicevox_engine_address_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab_frame, text="Speaker ID:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.voicevox_speaker_id_entry = ctk.CTkEntry(tab_frame)
        self.voicevox_speaker_id_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        button_frame = ctk.CTkFrame(tab_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ctk.CTkButton(button_frame, text="Refresh Speakers (Not Implemented)").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Test Voicevox (Not Implemented)").pack(side="left", padx=5)
        self._load_voicevox_settings()

    def _load_voicevox_settings(self):
        settings = self.settings_manager.get_setting("voicevox")
        if settings:
            self.voicevox_engine_address_entry.insert(0, settings.get("engine_address", ""))
            self.voicevox_speaker_id_entry.insert(0, str(settings.get("speaker_id", "")))

    def _create_appearance_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab_frame, text="Theme:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.appearance_theme_segmented_button = ctk.CTkSegmentedButton(tab_frame, values=["Light", "Dark", "System"])
        self.appearance_theme_segmented_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(tab_frame, text="Font Size:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.appearance_font_size_optionmenu = ctk.CTkOptionMenu(tab_frame, values=["Small", "Medium", "Large"])
        self.appearance_font_size_optionmenu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self._load_appearance_settings()
        
    def _load_appearance_settings(self):
        settings = self.settings_manager.get_setting("appearance")
        if settings:
            self.appearance_theme_segmented_button.set(settings.get("theme", "System").capitalize())
            self.appearance_font_size_optionmenu.set(settings.get("font_size", "Medium").capitalize())
        
        # Load voice mode setting for the switch in general settings
        voice_mode_setting = self.settings_manager.get_setting("voice_mode_on")
        if voice_mode_setting:
            if hasattr(self, 'general_voice_mode_switch'): # Ensure switch exists
                self.general_voice_mode_switch.select()
        else:
            if hasattr(self, 'general_voice_mode_switch'):
                self.general_voice_mode_switch.deselect()


    def _save_and_close(self):
        # Primary LLM
        self.settings_manager.update_setting("primary_llm", self.primary_llm_api_base_url_entry.get(), "api_base_url")
        self.settings_manager.update_setting("primary_llm", self.primary_llm_api_key_entry.get(), "api_key")
        self.settings_manager.update_setting("primary_llm", self.primary_llm_model_entry.get(), "model")
        self.settings_manager.update_setting("primary_llm", float(self.primary_llm_temp_slider.get()), "temperature")
        self.settings_manager.update_setting("primary_llm", self.primary_llm_system_prompt_text.get("1.0", "end-1c"), "system_prompt")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_api_base_url_entry.get(), "api_base_url")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_api_key_entry.get(), "api_key")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_model_entry.get(), "model")
        self.settings_manager.update_setting("translation_llm", float(self.translation_llm_temp_slider.get()), "temperature")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_system_prompt_text.get("1.0", "end-1c"), "system_prompt")
        
        # Voicevox
        self.settings_manager.update_setting("voicevox", self.voicevox_engine_address_entry.get(), "engine_address")
        speaker_id_val = self.voicevox_speaker_id_entry.get()
        try:
            self.settings_manager.update_setting("voicevox", int(speaker_id_val), "speaker_id")
        except ValueError:
            print(f"Warning: Invalid Speaker ID '{speaker_id_val}', not saving.")
            
        # Appearance
        self.settings_manager.update_setting("appearance", self.appearance_theme_segmented_button.get().lower(), "theme")
        self.settings_manager.update_setting("appearance", self.appearance_font_size_optionmenu.get().lower(), "font_size")
        
        # Voice Mode Toggle from general settings
        if hasattr(self, 'general_voice_mode_switch'):
            self.settings_manager.update_setting("voice_mode_on", self.general_voice_mode_switch.get() == 1)
        else: # Should not happen if UI is built correctly
            print("Warning: general_voice_mode_switch not found during save.")

        # Apply theme immediately if changed
        new_theme = self.appearance_theme_segmented_button.get().lower()
        current_mode = ctk.get_appearance_mode()
        if new_theme == "system": 
            if current_mode.lower() != "system": 
                 ctk.set_appearance_mode("System")
        elif new_theme.lower() != current_mode.lower():
             ctk.set_appearance_mode(new_theme)

        # Update services and voice mode in the main app
        if self.app:
            self.app.update_primary_llm_service()
            self.app.update_translation_llm_service() 
            self.app.update_voicevox_service() 
            self.app.is_voice_mode_on = self.settings_manager.get_setting("voice_mode_on") # Update voice mode in app
            if hasattr(self.app, 'update_voice_mode_toggle_button_text'):
                 self.app.update_voice_mode_toggle_button_text() 
            print("SettingsPanel: All services and voice mode in main app signaled for update.")

        self.destroy()

    def _create_general_settings_section(self, tab_frame):
        # This is part of the "Appearance & General" tab
        # Voice Mode Toggle
        ctk.CTkLabel(tab_frame, text="Voice Mode:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.general_voice_mode_switch = ctk.CTkSwitch(tab_frame, text="Enable Voice Output")
        self.general_voice_mode_switch.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # Load existing setting (also called in _load_appearance_settings to ensure it's loaded)
        voice_mode_setting = self.settings_manager.get_setting("voice_mode_on")
        if voice_mode_setting:
            self.general_voice_mode_switch.select()
        else:
            self.general_voice_mode_switch.deselect()

    def _create_appearance_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab_frame, text="Theme:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.appearance_theme_segmented_button = ctk.CTkSegmentedButton(tab_frame, values=["Light", "Dark", "System"])
        self.appearance_theme_segmented_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(tab_frame, text="Font Size:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.appearance_font_size_optionmenu = ctk.CTkOptionMenu(tab_frame, values=["Small", "Medium", "Large"])
        self.appearance_font_size_optionmenu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        self._create_general_settings_section(tab_frame) # Add general settings to this tab

        self._load_appearance_settings() # This loads theme, font size, and ensures voice_mode_switch is set

class ConversationBubble(ctk.CTkFrame):
    def __init__(self, parent, message_text, role, max_width, 
                 is_primary_assistant_response=False, app_instance=None, translated_text_for_replay=None): # Added new params
        super().__init__(parent, corner_radius=10)
        
        self.original_message_text = message_text # Store original for potential future use
        self.role = role
        self.app_instance = app_instance
        self.translated_text_for_replay = translated_text_for_replay
        self.play_audio_button = None # Initialize

        label_anchor = "w"
        bubble_fg_color = "grey30" # Default for assistant
        
        if role == "user":
            bubble_fg_color = "dodgerblue" # Example blue
            label_anchor = "e"
            
        # This inner_frame is used to control the bubble's width based on text length,
        # while the outer ConversationBubble frame is packed to fill and align.
        inner_frame = ctk.CTkFrame(self, fg_color=bubble_fg_color, corner_radius=10)
        
        message_label = ctk.CTkLabel(
            inner_frame, 
            text=message_text, 
            wraplength=max_width * 0.85, 
            justify="left" if (role == "assistant" or role == "translation") else "right", # Adjust justify for translation too
            anchor=label_anchor
        )
        message_label.pack(side="left", padx=10, pady=5, fill="x", expand=True) # Pack label first

        # Add play audio button for primary assistant messages if in voice mode and translated text is available
        if role == "assistant" and is_primary_assistant_response and \
           app_instance and app_instance.is_voice_mode_on:
            
            button_state = "normal" if self.translated_text_for_replay else "disabled"
            button_command = (lambda: app_instance.replay_audio(self.translated_text_for_replay)) \
                             if self.translated_text_for_replay else None

            self.play_audio_button = ctk.CTkButton(
                inner_frame, 
                text="🔊", 
                width=28, height=28, # Make it small
                command=button_command,
                state=button_state
            )
            self.play_audio_button.pack(side="right", padx=(0, 5), pady=5, fill="none", expand=False)


        if role == "user":
            inner_frame.pack(anchor="e", padx=0, pady=0, expand=False) 
        else: # assistant or translation
            inner_frame.pack(anchor="w", padx=0, pady=0, expand=False) 


def create_top_control_bar(parent_frame, app, settings_manager):
    top_bar = ctk.CTkFrame(parent_frame)

    settings_button = ctk.CTkButton(top_bar, text="Settings", command=app.open_settings_panel)
    settings_button.pack(side="left", padx=5, pady=5)
    
    clear_button = ctk.CTkButton(top_bar, text="Clear Conversation", command=app.clear_conversation)
    clear_button.pack(side="left", padx=5, pady=5)

    app_name_label = ctk.CTkLabel(top_bar, text="Chat Application")
    app_name_label.pack(side="left", expand=True, fill="x", padx=5, pady=5)

    # Voice Mode Toggle Button in Top Bar
    # Storing on app instance to allow App class to update its text
    app.voice_mode_toggle_button = ctk.CTkButton(
        top_bar, 
        text="Voice: Off", # Initial text, will be updated by app
        command=app.toggle_voice_mode_globally # Method to be created in App class
    )
    app.voice_mode_toggle_button.pack(side="right", padx=5, pady=5)
    # app.update_voice_mode_toggle_button_text() # App should call this after UI init

    copy_last_ai_button = ctk.CTkButton(top_bar, text="Copy Last AI", command=app.copy_last_ai_response)
    copy_last_ai_button.pack(side="right", padx=5, pady=5)

    return top_bar

def create_main_content_area(parent_frame, app):
    # Instead of a placeholder label, create a CTkScrollableFrame
    app.conversation_scroll_frame = ctk.CTkScrollableFrame(parent_frame)
    app.conversation_scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)
    
    # Configure the scrollable frame to update scrollbar when content changes
    app.conversation_scroll_frame._scrollbar.configure(command=app.conversation_scroll_frame._parent_canvas.yview)

    return app.conversation_scroll_frame


def create_input_area(parent_frame, app):
    input_frame = ctk.CTkFrame(parent_frame)

    message_input = ctk.CTkTextbox(input_frame, height=100) 
    message_input.pack(side="left", expand=True, fill="x", padx=5, pady=5)

    send_button = ctk.CTkButton(input_frame, text="Send")
    send_button.pack(side="right", padx=5, pady=5)

    return input_frame

def create_status_bar(parent_frame):
    status_bar = ctk.CTkFrame(parent_frame)
    
    status_label = ctk.CTkLabel(status_bar, text="Status: Ready")
    status_label.pack(side="left", padx=5, pady=5)
    
    return status_bar