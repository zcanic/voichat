import customtkinter as ctk
from gui_elements import show_critical_error_dialog 
import gui_elements # Keep for other gui_elements access
from settings_manager import SettingsManager
from llm_services import LLMService
from voicevox_service import VoicevoxService
import threading
import pyperclip 
import os

        self.title("Voice Assistant Chat")
        self.geometry("1000x700")
        
        self.settings_manager = SettingsManager()
        self.settings_panel_window = None
        
        self.primary_llm_service = None
        self.update_primary_llm_service()

        self.translation_llm_service = None 
        self.update_translation_llm_service()

        self.voicevox_service = None 
        self.update_voicevox_service()
        
        self.is_voice_mode_on = self.settings_manager.get_setting("voice_mode_on")
        self.voice_mode_toggle_button = None # Will be assigned by gui_elements

        self.conversation_history = []
        self.message_widgets = [] 
        self.conversation_scroll_frame = None 

        initial_theme = self.settings_manager.get_setting("appearance", "theme")
        if initial_theme and initial_theme.lower() in ["light", "dark", "system"]:
             ctk.set_appearance_mode(initial_theme.lower())
        else:
             ctk.set_appearance_mode("system")

        self.initialize_ui()

    def update_primary_llm_service(self):
        primary_llm_settings = self.settings_manager.get_setting("primary_llm")
        if primary_llm_settings:
            self.primary_llm_service = LLMService(
                api_base_url=primary_llm_settings.get("api_base_url"),
                api_key=primary_llm_settings.get("api_key"),
                model=primary_llm_settings.get("model"),
                temperature=primary_llm_settings.get("temperature"),
                system_prompt=primary_llm_settings.get("system_prompt")
            )
            print("Primary LLM Service Updated/Initialized.")
            if hasattr(self, 'status_label') and self.status_label and not self.primary_llm_service.is_configured():
                self.update_status_bar("Primary LLM not fully configured in Settings.", is_error=True)

    def update_translation_llm_service(self):
        translation_llm_settings = self.settings_manager.get_setting("translation_llm")
        if translation_llm_settings:
            self.translation_llm_service = LLMService(
                api_base_url=translation_llm_settings.get("api_base_url"),
                api_key=translation_llm_settings.get("api_key"),
                model=translation_llm_settings.get("model"),
                temperature=translation_llm_settings.get("temperature"),
                system_prompt=translation_llm_settings.get("system_prompt")
            )
            print("Translation LLM Service Updated/Initialized.")
            if hasattr(self, 'status_label') and self.status_label and not self.translation_llm_service.is_configured():
                self.update_status_bar("Translation LLM not fully configured in Settings.", is_error=True)


    def update_voicevox_service(self):
        voicevox_settings = self.settings_manager.get_setting("voicevox")
        if voicevox_settings:
            engine_url = voicevox_settings.get("engine_address")
            speaker_id = voicevox_settings.get("speaker_id", 1)
            if self.voicevox_service:
                self.voicevox_service.update_config(engine_url, speaker_id)
            else:
                self.voicevox_service = VoicevoxService(engine_url, speaker_id)
            print(f"Voicevox Service Updated/Initialized. URL: {engine_url}, Speaker ID: {speaker_id}")
            if hasattr(self, 'status_label') and self.status_label and not self.voicevox_service.is_configured():
                self.update_status_bar("Voicevox not fully configured in Settings.", is_error=True)
    
    def update_status_bar(self, message: str, is_error: bool = False):
        if not hasattr(self, 'status_label') or not self.status_label:
            # print(f"Status bar not initialized or available. Message: {message}") # Avoid print
            return
        
        prefix = "Error: " if is_error else "Status: "
        full_message = f"{prefix}{str(message)}"
        
        # Use theme colors if possible, otherwise fallback
        label_theme = ctk.ThemeManager.theme.get("CTkLabel", {})
        default_text_color = label_theme.get("text_color", ("black", "white")) # Default if not in theme
        
        text_color_actual = "red" if is_error else default_text_color
        # If default_text_color from theme is a tuple (light_mode, dark_mode)
        if isinstance(text_color_actual, tuple) and len(text_color_actual) == 2:
            current_mode = ctk.get_appearance_mode()
            text_color_actual = text_color_actual[1] if current_mode == "Dark" else text_color_actual[0]

        self.status_label.configure(text=full_message, text_color=text_color_actual)
        # print(full_message) # Avoid redundant print

    def set_input_active(self, is_active: bool):
        if hasattr(self, 'message_input_textbox') and self.message_input_textbox:
            self.message_input_textbox.configure(state="normal" if is_active else "disabled")
        
        if hasattr(self, 'send_button') and self.send_button:
            self.send_button.configure(state="normal" if is_active else "disabled")
            self.send_button.configure(text="Send" if is_active else "Processing...")

    def initialize_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.top_control_bar = gui_elements.create_top_control_bar(self.main_frame, app=self, settings_manager=self.settings_manager)
        self.top_control_bar.pack(side="top", fill="x")

        self.conversation_scroll_frame = gui_elements.create_main_content_area(self.main_frame, app=self)
        # conversation_scroll_frame is already packed in create_main_content_area

        self.input_area = gui_elements.create_input_area(self.main_frame, app=self) # app.send_button and app.message_input_textbox are set here
        self.input_area.pack(side="bottom", fill="x", padx=10, pady=10)
        
        status_bar_frame = gui_elements.create_status_bar(self.main_frame)
        status_bar_frame.pack(side="bottom", fill="x")
        self.status_label = status_bar_frame.winfo_children()[0] 
        
        self.update_voice_mode_toggle_button_text() # Set initial button text/color
        self._apply_voice_mode_theme() # Apply initial theme accents
        self.update_status_bar("Ready.") # Initial status

    def add_message_to_display(self, message_content, role, translated_text_for_replay=None):
        if not self.conversation_scroll_frame:
            print("Error: Conversation scroll frame not initialized.")
            return

        self.conversation_scroll_frame.update_idletasks() 
        max_bubble_width = self.conversation_scroll_frame.winfo_width()
        if max_bubble_width <= 0: max_bubble_width = self.winfo_width() * 0.7 

        is_primary_assistant = (role == "assistant")

        bubble = gui_elements.ConversationBubble(
            parent=self.conversation_scroll_frame, 
            message_text=message_content, 
            role=role, 
            max_width=max_bubble_width,
            is_primary_assistant_response=is_primary_assistant,
            app_instance=self,
            translated_text_for_replay=translated_text_for_replay if is_primary_assistant else None
        )
        # Packing with appropriate side padding is now handled inside ConversationBubble using self.pack_padx_outer
        bubble.pack(anchor="w" if role != "user" else "e", padx=bubble.pack_padx_outer, pady=5, fill="x")
            
        self.message_widgets.append(bubble)
        self.after(100, self._scroll_to_bottom) # Increased delay slightly

    def _scroll_to_bottom(self):
        if self.conversation_scroll_frame:
            self.conversation_scroll_frame._parent_canvas.yview_moveto(1.0)

    def on_send_message_click(self):
        user_message = self.message_input_textbox.get("1.0", "end-1c").strip()
        if not user_message: return

        self.set_input_active(False) # Now uses the new method
        self.message_input_textbox.delete("1.0", "end")
        self.conversation_history.append({"role": "user", "content": user_message})
        self.add_message_to_display(user_message, "user")
        
        self.update_status_bar("Processing message...") # Standardized message
        threading.Thread(target=self._process_message_thread, args=(user_message,), daemon=True).start()

    def _process_message_thread(self, user_message):
        # Use service's is_configured() method
        if not self.primary_llm_service or not self.primary_llm_service.is_configured():
            self.after(0, lambda: gui_elements.show_critical_error_dialog(self, "Primary LLM Error", "Primary LLM not configured. Please check API Key and URL in Settings."))
            self.after(0, lambda: self.update_status_bar("Primary LLM not configured.", is_error=True))
            self.after(0, lambda: self.set_input_active(True)) # Re-enable input
            return

        self.after(0, lambda: self.update_status_bar("Primary LLM: Generating response..."))
        primary_response_text = self.primary_llm_service.generate_response(user_message)
        
        if primary_response_text.startswith("Error:"):
            self.after(0, lambda: self._handle_llm_response(primary_response_text, is_error=True))
            return

        translated_text = None
        voice_status = None

        if self.is_voice_mode_on:
            if not self.translation_llm_service or not self.translation_llm_service.is_configured():
                self.after(0, lambda: gui_elements.show_critical_error_dialog(self, "Translation LLM Error", "Translation LLM not configured for Voice Mode. Please check API Key and URL in Settings."))
                translated_text = "Error: Translation LLM not configured."
            else:
                self.after(0, lambda: self.update_status_bar("Translation LLM: Translating..."))
                translated_text = self.translation_llm_service.generate_response(primary_response_text)

                if not translated_text.startswith("Error:"):
                    if not self.voicevox_service or not self.voicevox_service.is_configured():
                        self.after(0, lambda: gui_elements.show_critical_error_dialog(self, "Voicevox Error", "Voicevox service (engine address) not configured. Please check Settings."))
                        voice_status = "Error: Voicevox service not configured."
                    else:
                        vv_available, vv_msg = VoicevoxService.is_engine_available(self.voicevox_service.base_url)
                        if not vv_available:
                            self.after(0, lambda: gui_elements.show_critical_error_dialog(self, "Voicevox Error", f"Voicevox engine not found or unavailable at {self.voicevox_service.base_url}. Details: {vv_msg}"))
                            voice_status = f"Error: Voicevox engine unavailable. ({vv_msg})"
                        else:
                            self.after(0, lambda: self.update_status_bar("Voicevox: Synthesizing audio..."))
                            query, q_err = self.voicevox_service.generate_audio_query(translated_text)
                            if q_err: voice_status = f"Voicevox Query Error: {q_err}"
                            else:
                                audio_data, s_err = self.voicevox_service.synthesize_speech_data(query)
                                if s_err: voice_status = f"Voicevox Synthesis Error: {s_err}"
                                else:
                                    self.after(0, lambda: self.update_status_bar("Voicevox: Playing audio..."))
                                    threading.Thread(target=self._play_audio_thread, args=(audio_data,), daemon=True).start()
                                    voice_status = "Audio playback initiated."
                else: 
                    voice_status = "Skipping audio due to translation error."
        
        self.after(0, lambda: self._handle_llm_response(primary_response_text, translated_text, voice_status))
        
    def _play_audio_thread(self, audio_data):
        success, play_msg = self.voicevox_service.play_audio_bytes(audio_data) # Use tuple
        self.after(0, lambda: self.update_status_bar(f"Voicevox: {play_msg}", is_error=not success))
        if success:
             self.after(2000, lambda: self.update_status_bar("Ready."))


    def _handle_llm_response(self, primary_response, translated_text=None, voice_status=None, is_error=False):
        final_status = "Ready."
        is_final_status_error = False

        if is_error: # Error from primary LLM service call itself (not just config)
            self.add_message_to_display(primary_response, "assistant") 
            final_status = primary_response
            is_final_status_error = True
        else: # Primary LLM call was successful
            self.conversation_history.append({"role": "assistant", "content": primary_response})
            ttfr = translated_text if (translated_text and not translated_text.startswith("Error:")) else None
            self.add_message_to_display(primary_response, "assistant", translated_text_for_replay=ttfr)

            if translated_text:
                self.conversation_history.append({"role": "translation", "content": translated_text})
                self.add_message_to_display(translated_text, "translation")
                if translated_text.startswith("Error:"):
                    final_status = translated_text # Translation error is the status
                    is_final_status_error = True
            
            if voice_status: 
                if voice_status.startswith("Error:"):
                    # Voice error takes precedence if translation was okay or voice error is more specific
                    final_status = voice_status 
                    is_final_status_error = True
                # "Audio playback initiated" is transient; _play_audio_thread handles final status ("Ready." or error)
                elif not ("initiated" in voice_status or "started" in voice_status):
                    final_status = voice_status

        # Update status bar unless audio playback is just initiated (it will set "Ready." or error later)
        if not (voice_status and ("initiated" in voice_status or "started" in voice_status)):
             self.update_status_bar(final_status, is_error=is_final_status_error)
        
        self.set_input_active(True) # Re-enable input at the end
            
    def clear_conversation(self):
        self.conversation_history.clear()
        for widget in self.message_widgets: widget.destroy()
        self.message_widgets.clear()
        self.update_status_bar("Conversation cleared.") # Standardized

    def copy_last_ai_response(self):
        last_ai_msg = next((m["content"] for m in reversed(self.conversation_history) if m["role"] == "assistant" and not m["content"].startswith("Error:")), None)
        if last_ai_msg:
            try:
                pyperclip.copy(last_ai_msg)
                self.update_status_bar("AI response copied to clipboard.") # Standardized
            except pyperclip.PyperclipException as e:
                self.update_status_bar(f"Error copying to clipboard: {e}", is_error=True) # Standardized
        else:
            self.update_status_bar("No AI response to copy.", is_error=True) # Standardized

    def toggle_voice_mode_globally(self):
        self.is_voice_mode_on = not self.is_voice_mode_on
        self.settings_manager.update_setting("voice_mode_on", self.is_voice_mode_on)
        self.update_voice_mode_toggle_button_text()
        self._apply_voice_mode_theme()
        
        status_msg = f"Voice mode {'On' if self.is_voice_mode_on else 'Off'}."
        is_err = False
        if self.is_voice_mode_on: # Check configurations only if turning voice mode ON
            if not self.translation_llm_service or not self.translation_llm_service.is_configured(): 
                status_msg += " Translation LLM not configured."
                is_err = True
            if not self.voicevox_service or not self.voicevox_service.is_configured(): 
                status_msg += " Voicevox service not configured."
                is_err = True
            elif self.voicevox_service.is_configured(): # Only check engine if service itself is configured
                vv_available, _ = VoicevoxService.is_engine_available(self.voicevox_service.base_url)
                if not vv_available:
                    status_msg += " Voicevox engine unavailable."
                    is_err = True
        self.update_status_bar(status_msg, is_error=is_err)


    def update_voice_mode_toggle_button_text(self):
        if self.voice_mode_toggle_button: 
            if self.is_voice_mode_on:
                self.voice_mode_toggle_button.configure(text="Voice ON (日本語)", fg_color=("green", "darkgreen"))
            else:
                default_fg_color = ctk.ThemeManager.theme.get("CTkButton", {}).get("fg_color", ("#3B8ED0", "#1F6AA5"))
                self.voice_mode_toggle_button.configure(text="Voice OFF", fg_color=default_fg_color)

    def _apply_voice_mode_theme(self): 
        if not hasattr(self, 'conversation_scroll_frame') or not self.conversation_scroll_frame: return
        frame_theme = ctk.ThemeManager.theme.get("CTkFrame", {})
        default_border_color = frame_theme.get("border_color", ("gray50", "gray28"))
        default_border_width = frame_theme.get("border_width", 0)
        if isinstance(default_border_color, str): default_border_color = (default_border_color, default_border_color)

        if self.is_voice_mode_on:
            self.conversation_scroll_frame.configure(border_color=("green", "darkgreen"), border_width=2)
        else:
            self.conversation_scroll_frame.configure(border_color=default_border_color, border_width=default_border_width)

    def replay_audio(self, text_to_speak):
        if not text_to_speak:
            self.update_status_bar("No text to replay.", is_error=True)
            return

        self.set_input_active(False)
        self.update_status_bar("Voicevox: Replaying audio...") 

        if not self.voicevox_service or not self.voicevox_service.is_configured(): # Use is_configured()
            gui_elements.show_critical_error_dialog(self, "Voicevox Error", "Voicevox service (engine address) not configured. Please check Settings.")
            self.update_status_bar("Voicevox not configured for replay.", is_error=True)
            self.set_input_active(True)
            return
        
        is_vv_available, vv_message = VoicevoxService.is_engine_available(self.voicevox_service.base_url)
        if not is_vv_available:
            gui_elements.show_critical_error_dialog(self, "Voicevox Error", f"Voicevox engine not found or unavailable at {self.voicevox_service.base_url}. Details: {vv_message}")
            self.update_status_bar(f"Voicevox engine unavailable for replay. ({vv_message})", is_error=True)
            self.set_input_active(True)
            return
        
        threading.Thread(target=self._replay_audio_thread_worker, args=(text_to_speak,), daemon=True).start()

    def _replay_audio_thread_worker(self, text_to_speak):
        self.after(0, lambda: self.update_status_bar("Voicevox: Synthesizing replay..."))
        audio_query, aq_error = self.voicevox_service.generate_audio_query(text_to_speak)
        if aq_error:
            self.after(0, lambda: self.update_status_bar(f"Replay Query Error: {aq_error[:50]}...", is_error=True))
            self.after(0, lambda: self.set_input_active(True))
            return
        
        audio_data, synth_error = self.voicevox_service.synthesize_speech_data(audio_query)
        if synth_error:
            self.after(0, lambda: self.update_status_bar(f"Replay Synth Error: {synth_error[:50]}...", is_error=True))
            self.after(0, lambda: self.set_input_active(True))
            return
        
        self.after(0, lambda: self.update_status_bar("Voicevox: Playing replay..."))
        success, play_msg = self.voicevox_service.play_audio_bytes(audio_data) # Use tuple
        self.after(0, lambda: self.update_status_bar(f"Voicevox: {play_msg}", is_error=not success))
        if success:
             self.after(2000, lambda: self.update_status_bar("Ready.")) 
        self.after(0, lambda: self.set_input_active(True))

    def open_settings_panel(self):
        if self.settings_panel_window is None or not self.settings_panel_window.winfo_exists():
            self.settings_panel_window = gui_elements.SettingsPanel(parent=self, settings_manager=self.settings_manager, app=self)
            self.update_status_bar("Settings panel opened.") 
            self.settings_panel_window.focus()
        else:
            self.settings_panel_window.deiconify()
            self.settings_panel_window.lift()
            self.settings_panel_window.focus()

if __name__ == "__main__":
    # Ensures that the application is run from the main thread, which is necessary for Tkinter.
    # Also, CustomTkinter theming might need to be initialized before any CTk widgets are created.
    ctk.set_appearance_mode("System") # Default theme
    ctk.set_default_color_theme("blue") 
    
    app = App()
    app.mainloop()

    def cycle_theme(self):
        current_theme_value = self.settings_manager.get_setting("appearance", "theme")
        themes = ["light", "dark", "system"]
        try:
            current_index = themes.index(current_theme_value.lower())
            next_index = (current_index + 1) % len(themes)
            new_theme = themes[next_index]
        except ValueError: # If current theme isn't in our list, default to system
            new_theme = "system"
        
        self.settings_manager.update_setting("appearance", new_theme, "theme") # Save the new theme
        ctk.set_appearance_mode(new_theme) # Apply the new theme
        self.update_status_bar(f"Theme changed to {new_theme.capitalize()}.")
        # Optionally, update cycle theme button text/icon if it's not just a cycle button

    def apply_theme_from_settings_panel(self, theme_name: str):
        if theme_name and theme_name.lower() in ["light", "dark", "system"]:
            theme_to_apply = theme_name.lower()
            # Capitalize for display if needed, but CTk takes lowercase or capitalized "System"
            display_theme_name = theme_name if theme_name == "System" else theme_name.lower()
            
            ctk.set_appearance_mode(display_theme_name) 
            self.settings_manager.update_setting("appearance", theme_to_apply, "theme") # This also saves
            self.update_status_bar(f"Theme set to {theme_name.capitalize()}.")
        else:
            self.update_status_bar(f"Invalid theme name: {theme_name}", is_error=True)

# Add new methods to the App class
App.cycle_theme = cycle_theme
App.apply_theme_from_settings_panel = apply_theme_from_settings_panel
