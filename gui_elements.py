import customtkinter as ctk # Renamed from customtkinter
import threading
import re # For parsing speaker ID from combobox if needed later, not strictly for Step 9

# Assuming VoicevoxService is in voicevox_service.py for static method calls
from voicevox_service import VoicevoxService


class SettingsPanel(ctk.CTkToplevel):
    def __init__(self, parent, settings_manager, app): # app instance for callbacks
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)
        self.grab_set()
        self.settings_manager = settings_manager
        self.app = app # Store the app instance (main_app.App)
        
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

    def _create_llm_tab_content(self, tab_frame, llm_type_key):
        # Helper to create common LLM settings widgets
        tab_frame.grid_columnconfigure(1, weight=1)

        widgets = {}

        ctk.CTkLabel(tab_frame, text="API Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        widgets["api_base_url_entry"] = ctk.CTkEntry(tab_frame)
        widgets["api_base_url_entry"].grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(tab_frame, text="API Key:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        widgets["api_key_entry"] = ctk.CTkEntry(tab_frame, show="*")
        widgets["api_key_entry"].grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(tab_frame, text="Model:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        widgets["model_entry"] = ctk.CTkEntry(tab_frame)
        widgets["model_entry"].grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(tab_frame, text="Temperature:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        temp_slider_frame = ctk.CTkFrame(tab_frame)
        temp_slider_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        temp_slider_frame.grid_columnconfigure(0, weight=1)
        
        widgets["temp_slider"] = ctk.CTkSlider(temp_slider_frame, from_=0.0, to=1.0, number_of_steps=100)
        widgets["temp_slider"].grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        widgets["temp_value_label"] = ctk.CTkLabel(temp_slider_frame, text="0.7") # Default text
        widgets["temp_value_label"].grid(row=0, column=1, padx=(5,0), pady=5, sticky="w")
        widgets["temp_slider"].configure(command=lambda val, label=widgets["temp_value_label"]: label.configure(text=f"{val:.2f}"))
        
        ctk.CTkLabel(tab_frame, text="System Prompt:").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        widgets["system_prompt_text"] = ctk.CTkTextbox(tab_frame, height=100)
        widgets["system_prompt_text"].grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
        tab_frame.grid_rowconfigure(4, weight=1)
        
        return widgets

    def _load_llm_settings(self, widgets, llm_type_key):
        settings = self.settings_manager.get_setting(llm_type_key)
        if settings:
            widgets["api_base_url_entry"].insert(0, settings.get("api_base_url", ""))
            widgets["api_key_entry"].insert(0, settings.get("api_key", ""))
            widgets["model_entry"].insert(0, settings.get("model", ""))
            temp = settings.get("temperature", 0.7)
            widgets["temp_slider"].set(float(temp))
            widgets["temp_value_label"].configure(text=f"{float(temp):.2f}")
            widgets["system_prompt_text"].insert("1.0", settings.get("system_prompt", ""))

    def _save_llm_settings(self, widgets, llm_type_key):
        self.settings_manager.update_setting(llm_type_key, widgets["api_base_url_entry"].get(), "api_base_url")
        self.settings_manager.update_setting(llm_type_key, widgets["api_key_entry"].get(), "api_key")
        self.settings_manager.update_setting(llm_type_key, widgets["model_entry"].get(), "model")
        self.settings_manager.update_setting(llm_type_key, float(widgets["temp_slider"].get()), "temperature")
        self.settings_manager.update_setting(llm_type_key, widgets["system_prompt_text"].get("1.0", "end-1c"), "system_prompt")

    def _create_primary_llm_tab(self, tab_frame):
        self.primary_llm_widgets = self._create_llm_tab_content(tab_frame, "primary_llm")
        self._load_llm_settings(self.primary_llm_widgets, "primary_llm")

    def _create_translation_llm_tab(self, tab_frame):
        self.translation_llm_widgets = self._create_llm_tab_content(tab_frame, "translation_llm")
        self._load_llm_settings(self.translation_llm_widgets, "translation_llm")

    def _create_voicevox_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab_frame, text="Engine Address:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.voicevox_engine_address_entry = ctk.CTkEntry(tab_frame)
        self.voicevox_engine_address_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(tab_frame, text="Speaker ID:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.voicevox_speaker_id_combobox = ctk.CTkComboBox(tab_frame, values=[], state="normal", command=None) # Allow manual entry
        self.voicevox_speaker_id_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.voicevox_speaker_id_combobox.set("") 

        self.speaker_name_to_id_map = {} # Initialize map

        button_frame = ctk.CTkFrame(tab_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.voicevox_refresh_button = ctk.CTkButton(button_frame, text="Refresh Speakers", command=self._refresh_voicevox_speakers)
        self.voicevox_refresh_button.pack(side="left", padx=5)
        
        self.voicevox_test_button = ctk.CTkButton(button_frame, text="Test Voicevox", command=self._test_voicevox_connection)
        self.voicevox_test_button.pack(side="left", padx=5)

        self.voicevox_status_label = ctk.CTkLabel(tab_frame, text="", height=1, wraplength=tab_frame.winfo_width()-20)
        self.voicevox_status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=(0,5), sticky="ew")
        
        self._load_voicevox_settings()

    def _load_voicevox_settings(self):
        settings = self.settings_manager.get_setting("voicevox")
        engine_address = ""
        if settings:
            engine_address = settings.get("engine_address", "")
            self.voicevox_engine_address_entry.insert(0, engine_address)
            self.current_saved_speaker_id = settings.get("speaker_id") # Store as int
            # Set the raw ID into combobox text field initially. 
            # _refresh_voicevox_speakers will attempt to map it to display name.
            if self.current_saved_speaker_id is not None:
                 self.voicevox_speaker_id_combobox.set(str(self.current_saved_speaker_id))
            else:
                self.voicevox_speaker_id_combobox.set("")


        if engine_address:
            self._refresh_voicevox_speakers() # This will populate and try to select
        else:
            self.voicevox_speaker_id_combobox.configure(values=[]) # No address, no speakers
            self.voicevox_speaker_id_combobox.set("")
            self.voicevox_status_label.configure(text="Engine address not set.")


    def _refresh_voicevox_speakers(self):
        self.voicevox_refresh_button.configure(state="disabled")
        self.voicevox_speaker_id_combobox.configure(state="disabled")
        self.voicevox_status_label.configure(text="Refreshing speakers...", text_color=None)

        engine_address = self.voicevox_engine_address_entry.get().strip()
        if not engine_address:
            self.voicevox_status_label.configure(text="Error: Engine address is required.", text_color="orange")
            self.voicevox_refresh_button.configure(state="normal")
            # Keep combobox disabled as there's no valid address
            return

        is_available, message = VoicevoxService.is_engine_available(engine_address)
        if not is_available:
            self.voicevox_status_label.configure(text=f"Engine not reachable: {message}", text_color="orange")
            self.voicevox_refresh_button.configure(state="normal")
            self.voicevox_speaker_id_combobox.configure(state="normal") 
            return
        
        self.voicevox_status_label.configure(text="Fetching speakers from engine...")
        threading.Thread(target=self._fetch_speakers_thread_worker, args=(engine_address,), daemon=True).start()

    def _fetch_speakers_thread_worker(self, engine_address):
        speakers_data, error_msg = VoicevoxService.get_speakers(engine_address)
        self.after(0, lambda: self._update_speaker_list_ui(speakers_data, error_msg))

    def _update_speaker_list_ui(self, speakers_data, error_msg):
        self.voicevox_refresh_button.configure(state="normal")
        self.voicevox_speaker_id_combobox.configure(state="normal")
        self.speaker_name_to_id_map.clear()
        
        if error_msg:
            self.voicevox_status_label.configure(text=f"Error: {error_msg}", text_color="orange")
            self.voicevox_speaker_id_combobox.configure(values=[])
            self.voicevox_speaker_id_combobox.set("")
            return

        if not speakers_data:
            self.voicevox_status_label.configure(text="Failed to load speakers or no speakers found.", text_color="orange")
            self.voicevox_speaker_id_combobox.configure(values=[])
            self.voicevox_speaker_id_combobox.set("")
            return

        speaker_display_values = []
        value_to_set_display_name = ""

        for speaker_group in speakers_data:
            group_name = speaker_group.get("name", "Unknown Speaker")
            for style in speaker_group.get("styles", []):
                style_name = style.get("name", "Default Style")
                style_id = style.get("id")
                display_name = f"{group_name} - {style_name} (ID: {style_id})"
                speaker_display_values.append(display_name)
                self.speaker_name_to_id_map[display_name] = style_id
                
                if hasattr(self, 'current_saved_speaker_id') and style_id == self.current_saved_speaker_id:
                    value_to_set_display_name = display_name
        
        current_combobox_text = self.voicevox_speaker_id_combobox.get()

        self.voicevox_speaker_id_combobox.configure(values=speaker_display_values)

        if value_to_set_display_name:
            self.voicevox_speaker_id_combobox.set(value_to_set_display_name)
        elif speaker_display_values: # If saved ID not found, try to keep current text if it's a valid ID, else first
            try: # Check if current text is a raw ID that exists
                raw_id_check = int(current_combobox_text)
                if raw_id_check in self.speaker_name_to_id_map.values():
                    # Find the display name for this raw ID
                    for dn, i_d in self.speaker_name_to_id_map.items():
                        if i_d == raw_id_check:
                            self.voicevox_speaker_id_combobox.set(dn)
                            break
                else: # Raw ID not in list, set to first
                    self.voicevox_speaker_id_combobox.set(speaker_display_values[0])
            except ValueError: # Not a raw ID, set to first
                 self.voicevox_speaker_id_combobox.set(speaker_display_values[0])
        else:
            self.voicevox_speaker_id_combobox.set("")
            
        self.voicevox_status_label.configure(text="Speakers refreshed.", text_color=None) 

    def _test_voicevox_connection(self):
        self.voicevox_test_button.configure(state="disabled")
        self.voicevox_status_label.configure(text="Testing Voicevox...", text_color=None)

        engine_address = self.voicevox_engine_address_entry.get().strip()
        selected_value = self.voicevox_speaker_id_combobox.get()
        
        parsed_speaker_id = None
        if not selected_value:
            self.voicevox_status_label.configure(text="Error: Speaker ID not selected.", text_color="orange")
            self.voicevox_test_button.configure(state="normal")
            return

        if selected_value in self.speaker_name_to_id_map:
            parsed_speaker_id = self.speaker_name_to_id_map[selected_value]
        else:
            try:
                parsed_speaker_id = int(selected_value)
            except ValueError:
                self.voicevox_status_label.configure(text="Error: Invalid Speaker ID format.", text_color="orange")
                self.voicevox_test_button.configure(state="normal")
                return

        if not engine_address:
            self.voicevox_status_label.configure(text="Error: Engine address required.", text_color="orange")
            self.voicevox_test_button.configure(state="normal")
            return

        threading.Thread(target=self._test_voicevox_thread_worker, args=(engine_address, parsed_speaker_id), daemon=True).start()

    def _test_voicevox_thread_worker(self, engine_address, speaker_id):
        temp_service = VoicevoxService(engine_address, speaker_id)
        
        available, status_msg = VoicevoxService.is_engine_available(engine_address)
        if not available:
            self.after(0, lambda: self._update_test_status(f"Test failed: Engine - {status_msg}", True))
            return

        test_phrase = "こんにちは、これはテストです。"
        audio_query, error_msg = temp_service.generate_audio_query(test_phrase)
        if error_msg:
            self.after(0, lambda: self._update_test_status(f"Test failed: Query - {error_msg}", True))
            return

        audio_data, error_msg = temp_service.synthesize_speech_data(audio_query)
        if error_msg:
            self.after(0, lambda: self._update_test_status(f"Test failed: Synth - {error_msg}", True))
            return
        
        success, playback_msg = temp_service.play_audio_bytes(audio_data)
        if success:
            self.after(0, lambda: self._update_test_status("Test sound played successfully.", False))
        else:
            self.after(0, lambda: self._update_test_status(f"Test: Playback - {playback_msg}", True))
            
    def _update_test_status(self, message, is_error):
        self.voicevox_status_label.configure(text=message, text_color="orange" if is_error else None)
        self.voicevox_test_button.configure(state="normal")

    def _create_appearance_tab(self, tab_frame):
        tab_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab_frame, text="Theme:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.appearance_theme_segmented_button = ctk.CTkSegmentedButton(tab_frame, values=["Light", "Dark", "System"])
        self.appearance_theme_segmented_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(tab_frame, text="Font Size:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.appearance_font_size_optionmenu = ctk.CTkOptionMenu(tab_frame, values=["Small", "Medium", "Large"])
        self.appearance_font_size_optionmenu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Voice Mode Toggle (Part of Step 9)
        ctk.CTkLabel(tab_frame, text="Voice Mode:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.general_voice_mode_switch = ctk.CTkSwitch(tab_frame, text="Enable Voice Output")
        self.general_voice_mode_switch.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self._load_appearance_settings()
        
    def _load_appearance_settings(self):
        settings = self.settings_manager.get_setting("appearance")
        if settings:
            self.appearance_theme_segmented_button.set(settings.get("theme", "System").capitalize())
            self.appearance_font_size_optionmenu.set(settings.get("font_size", "Medium").capitalize())
        
        voice_mode_on = self.settings_manager.get_setting("voice_mode_on")
        if voice_mode_on:
            self.general_voice_mode_switch.select()
        else:
            self.general_voice_mode_switch.deselect()

    def _save_and_close(self):
        self._save_llm_settings(self.primary_llm_widgets, "primary_llm")
        self._save_llm_settings(self.translation_llm_widgets, "translation_llm")

        # Voicevox
        self.settings_manager.update_setting("voicevox", self.voicevox_engine_address_entry.get().strip(), "engine_address")
        
        selected_speaker_value = self.voicevox_speaker_id_combobox.get()
        speaker_id_to_save = None
        if selected_speaker_value in self.speaker_name_to_id_map: # Check if it's a display name
            speaker_id_to_save = self.speaker_name_to_id_map[selected_speaker_value]
        else: # Assume it's a manually entered ID
            try:
                speaker_id_to_save = int(selected_speaker_value)
            except ValueError:
                # This case should ideally be handled with validation before saving,
                # or by not saving if the value is invalid and not in the map.
                # For now, if it's not in map and not int, it might not save or save incorrectly.
                # The `SettingsManager` expects an int for speaker_id.
                print(f"Warning: Speaker ID '{selected_speaker_value}' is not a recognized format or valid ID. May not save correctly.")
                # Attempt to use current_saved_speaker_id if available and valid, otherwise skip update
                if hasattr(self, 'current_saved_speaker_id') and isinstance(self.current_saved_speaker_id, int):
                    speaker_id_to_save = self.current_saved_speaker_id # Fallback to last known good ID
                else:
                    speaker_id_to_save = 1 # Default fallback
        
        if speaker_id_to_save is not None: # Ensure we have a value
             self.settings_manager.update_setting("voicevox", int(speaker_id_to_save), "speaker_id")
            
        # Appearance
        self.settings_manager.update_setting("appearance", self.appearance_theme_segmented_button.get().lower(), "theme")
        self.settings_manager.update_setting("appearance", self.appearance_font_size_optionmenu.get().lower(), "font_size")
        
        # Voice Mode
        voice_mode_on = self.general_voice_mode_switch.get() == 1
        self.settings_manager.update_setting("voice_mode_on", voice_mode_on)
        
        # Apply theme immediately
        new_theme = self.appearance_theme_segmented_button.get().lower()
        current_mode = ctk.get_appearance_mode().lower()
        if new_theme == "system":
            if current_mode != "system": ctk.set_appearance_mode("System")
        elif new_theme != current_mode:
             ctk.set_appearance_mode(new_theme)

        # Update app services and state
        if self.app:
            self.app.update_primary_llm_service()
            self.app.update_translation_llm_service() 
            self.app.update_voicevox_service() 
            self.app.is_voice_mode_on = voice_mode_on # Update app's flag
            if hasattr(self.app, 'update_voice_mode_toggle_button_text'):
                 self.app.update_voice_mode_toggle_button_text() 
            if hasattr(self.app, '_apply_voice_mode_theme'):
                self.app._apply_voice_mode_theme()

        self.destroy()

class ConversationBubble(ctk.CTkFrame):
    def __init__(self, parent, message_text, role, max_width, 
                 is_primary_assistant_response=False, app_instance=None, translated_text_for_replay=None):
        super().__init__(parent, corner_radius=10, fg_color="transparent") # Outer bubble transparent
        
        self.role = role
        self.app_instance = app_instance # For calling replay_audio
        self.translated_text_for_replay = translated_text_for_replay

        # Determine bubble color and text alignment based on role
        if role == "user":
            bubble_fg_color = ("#3B8ED0", "#1F6AA5") # Default CTk blue
            text_anchor = "e"
            pack_anchor = "e"
            padx_outer = (50, 10) # Left padding to push to right
        elif role == "assistant":
            bubble_fg_color = ("#707070", "#505050") # Greyish
            text_anchor = "w"
            pack_anchor = "w"
            padx_outer = (10, 50) # Right padding to push to left
        elif role == "translation":
            bubble_fg_color = ("#606060", "#404040") # Darker Greyish for translation
            text_anchor = "w"
            pack_anchor = "w"
            padx_outer = (25, 65) # Indent more than assistant, less than user
        else: # Error or other
            bubble_fg_color = ("#C00000", "#800000") # Reddish for errors
            text_anchor = "w"
            pack_anchor = "w"
            padx_outer = (10,50)

        # Inner frame for actual bubble appearance and content
        inner_frame = ctk.CTkFrame(self, fg_color=bubble_fg_color, corner_radius=10)
        
        # Configure inner_frame to align left or right within the transparent outer bubble
        # The outer bubble will fill 'x', inner_frame will not expand to fill outer.
        if pack_anchor == "e":
            inner_frame.pack(anchor="e", padx=0, pady=0) # No internal padding for inner frame relative to outer
        else:
            inner_frame.pack(anchor="w", padx=0, pady=0)

        content_frame = ctk.CTkFrame(inner_frame, fg_color="transparent") # Holds label and button
        content_frame.pack(padx=10, pady=5, fill="x", expand=True)

        message_label = ctk.CTkLabel(
            content_frame, 
            text=message_text, 
            wraplength=max_width * 0.75, # Adjust wraplength
            justify="left" if text_anchor == "w" else "right",
            anchor=text_anchor
        )
        message_label.pack(side="left", fill="x", expand=True)

        if role == "assistant" and is_primary_assistant_response and app_instance and app_instance.is_voice_mode_on:
            button_state = "normal" if self.translated_text_for_replay else "disabled"
            button_command = (lambda: app_instance.replay_audio(self.translated_text_for_replay)) \
                             if self.translated_text_for_replay else None
            play_audio_button = ctk.CTkButton(
                content_frame, text="🔊", width=28, height=28, command=button_command, state=button_state
            )
            play_audio_button.pack(side="right", padx=(5,0), fill="none", expand=False)
        
        # The outer frame uses padx_outer to control its own alignment on the scrollable frame.
        self.pack_padx_outer = padx_outer


def create_top_control_bar(parent_frame, app, settings_manager):
    top_bar = ctk.CTkFrame(parent_frame)

    settings_button = ctk.CTkButton(top_bar, text="Settings", command=app.open_settings_panel)
    settings_button.pack(side="left", padx=5, pady=5)
    
    clear_button = ctk.CTkButton(top_bar, text="Clear Conversation", command=app.clear_conversation)
    clear_button.pack(side="left", padx=5, pady=5)

    app_name_label = ctk.CTkLabel(top_bar, text="Chat Application")
    app_name_label.pack(side="left", expand=True, fill="x", padx=5, pady=5)
    
    app.voice_mode_toggle_button = ctk.CTkButton(
        top_bar, text="Voice: Off", command=app.toggle_voice_mode_globally
    )
    app.voice_mode_toggle_button.pack(side="right", padx=5, pady=5)

    theme_cycle_button = ctk.CTkButton(top_bar, text="Cycle Theme", command=app.cycle_theme)
    theme_cycle_button.pack(side="right", padx=5, pady=5)

    copy_last_ai_button = ctk.CTkButton(top_bar, text="Copy Last AI", command=app.copy_last_ai_response)
    copy_last_ai_button.pack(side="right", padx=5, pady=5)
    return top_bar

def _create_appearance_tab(self, tab_frame): # In SettingsPanel Class
    tab_frame.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(tab_frame, text="Theme:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    self.appearance_theme_segmented_button = ctk.CTkSegmentedButton(
        tab_frame, 
        values=["Light", "Dark", "System"],
        command=lambda value: self.app.apply_theme_from_settings_panel(value) # Pass the selected value
    )
    self.appearance_theme_segmented_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(tab_frame, text="Font Size:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    self.appearance_font_size_optionmenu = ctk.CTkOptionMenu(tab_frame, values=["Small", "Medium", "Large"])
    self.appearance_font_size_optionmenu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    
    # This part should already exist from previous steps, ensure it's called
    if hasattr(self, '_create_general_settings_section'):
        self._create_general_settings_section(tab_frame) 
    else: # Should ideally not happen if class is correctly structured
        print("Warning: _create_general_settings_section method missing in SettingsPanel")

    if hasattr(self, '_load_appearance_settings'):
        self._load_appearance_settings()
    else:
        print("Warning: _load_appearance_settings method missing in SettingsPanel")

# Replace the existing _create_appearance_tab method in SettingsPanel
SettingsPanel._create_appearance_tab = _create_appearance_tab


def create_main_content_area(parent_frame, app):
    app.conversation_scroll_frame = ctk.CTkScrollableFrame(parent_frame)
    app.conversation_scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)
    if hasattr(app.conversation_scroll_frame, '_parent_canvas'): # Ensure canvas exists
        app.conversation_scroll_frame._scrollbar.configure(command=app.conversation_scroll_frame._parent_canvas.yview)
    return app.conversation_scroll_frame

def create_input_area(parent_frame, app):
    input_frame = ctk.CTkFrame(parent_frame)
    input_frame.grid_columnconfigure(0, weight=1) # Make textbox expand

    app.message_input_textbox = ctk.CTkTextbox(input_frame, height=100) 
    app.message_input_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    app.send_button = ctk.CTkButton(input_frame, text="Send", command=app.on_send_message_click)
    app.send_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")
    return input_frame

def create_status_bar(parent_frame):
    status_bar = ctk.CTkFrame(parent_frame, height=30) # Give it a bit of height
    status_bar.pack_propagate(False) # Prevent label from shrinking it
    
    status_label = ctk.CTkLabel(status_bar, text="Status: Ready")
    status_label.pack(side="left", padx=10, pady=5) # Add some padding
    return status_bar

# This function should be part of gui_elements.py as per current subtask.
def show_critical_error_dialog(parent_window, title: str, message: str):
    dialog = ctk.CTkToplevel(parent_window)
    dialog.title(title)
    dialog.transient(parent_window) 
    dialog.grab_set() 

    dialog_width = 400
    dialog_height = 170 # Increased height for better text display
    
    # Center on parent
    parent_x = parent_window.winfo_x()
    parent_y = parent_window.winfo_y()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()
    x = parent_x + (parent_width // 2) - (dialog_width // 2)
    y = parent_y + (parent_height // 2) - (dialog_height // 2)
    
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    dialog.resizable(False, False)

    message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    message_frame.pack(padx=20, pady=20, expand=True, fill="both")
    
    icon_label = ctk.CTkLabel(message_frame, text="⚠️", font=("Segoe UI Emoji", 24)) # Example with emoji
    icon_label.pack(side="left", padx=(0,10), anchor="center")

    message_label = ctk.CTkLabel(message_frame, text=message, wraplength=dialog_width - 80, justify="left")
    message_label.pack(side="left", expand=True, fill="both", anchor="center")

    ok_button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=100)
    ok_button.pack(pady=(0, 20))
    
    dialog.attributes("-topmost", True) 
    dialog.lift() 
    dialog.focus_force() 
    
    parent_window.wait_window(dialog) # Make it modal
