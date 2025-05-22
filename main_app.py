import customtkinter as ctk
import gui_elements
from settings_manager import SettingsManager
from llm_services import LLMService
from voicevox_service import VoicevoxService # Import VoicevoxService
import threading
import pyperclip 

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chat Application")
        self.geometry("1000x700")
        
        self.settings_manager = SettingsManager()
        self.settings_panel_window = None
        
        self.primary_llm_service = None
        self.update_primary_llm_service()

        self.translation_llm_service = None # Initialize translation LLM service
        self.update_translation_llm_service()

        self.voicevox_service = None # Initialize Voicevox service
        self.update_voicevox_service()
        
        self.is_voice_mode_on = self.settings_manager.get_setting("voice_mode_on")
        self.voice_mode_toggle_button = None # Will be assigned by gui_elements

        self.conversation_history = []
        self.message_widgets = [] 
        self.conversation_scroll_frame = None 

        initial_theme = self.settings_manager.get_setting("appearance", "theme")
        if initial_theme in ["light", "dark", "system"]:
             ctk.set_appearance_mode(initial_theme)
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
            if self.primary_llm_service and (not self.primary_llm_service.api_base_url or not self.primary_llm_service.api_key):
                print("Warning: Primary LLM Service is missing API Base URL or API Key after update.")
                if hasattr(self, 'status_label'): 
                    self.status_label.configure(text="Status: Primary LLM not configured.")
    
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
            if self.translation_llm_service and (not self.translation_llm_service.api_base_url or not self.translation_llm_service.api_key):
                print("Warning: Translation LLM Service is missing API Base URL or API Key.")
                if hasattr(self, 'status_label') and self.status_label.cget("text") == "Status: Ready": # Avoid overwriting other statuses
                     self.status_label.configure(text="Status: Translation LLM not configured.")

    def update_voicevox_service(self):
        voicevox_settings = self.settings_manager.get_setting("voicevox")
        if voicevox_settings:
            engine_url = voicevox_settings.get("engine_address")
            speaker_id = voicevox_settings.get("speaker_id")
            if self.voicevox_service:
                self.voicevox_service.update_config(engine_url, speaker_id)
            else:
                self.voicevox_service = VoicevoxService(engine_url, speaker_id)
            print(f"Voicevox Service Updated/Initialized. URL: {engine_url}, Speaker ID: {speaker_id}")
            if not engine_url:
                 print("Warning: Voicevox engine address is not configured.")
                 if hasattr(self, 'status_label') and self.status_label.cget("text") == "Status: Ready":
                    self.status_label.configure(text="Status: Voicevox not configured.")


    def initialize_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.top_control_bar = gui_elements.create_top_control_bar(
            self.main_frame, 
            app=self, 
            settings_manager=self.settings_manager
        )
        self.top_control_bar.pack(side="top", fill="x")

        # Initialize the voice mode toggle button's text
        if hasattr(self, 'update_voice_mode_toggle_button_text'):
            self.update_voice_mode_toggle_button_text()

        gui_elements.create_main_content_area(self.main_frame, app=self) 

        self.input_area = gui_elements.create_input_area(self.main_frame, app=self)
        self.input_area.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.message_input_textbox = self.input_area.winfo_children()[0] 
        self.send_button = self.input_area.winfo_children()[1] 
        self.send_button.configure(command=self.on_send_message_click)

        status_bar_frame = gui_elements.create_status_bar(self.main_frame)
        status_bar_frame.pack(side="bottom", fill="x")
        self.status_label = status_bar_frame.winfo_children()[0] 
        
        # Initial status check
        status_messages = []
        if self.primary_llm_service and (not self.primary_llm_service.api_base_url or not self.primary_llm_service.api_key):
            status_messages.append("PrimaryLLM N/C")
        if self.translation_llm_service and (not self.translation_llm_service.api_base_url or not self.translation_llm_service.api_key):
            status_messages.append("TranslateLLM N/C")
        if self.voicevox_service and not self.voicevox_service.base_url: # Check if engine_address is set
            status_messages.append("Voicevox N/C")
        
        if status_messages:
            self.status_label.configure(text="Status: " + ", ".join(status_messages))
        else:
            self.status_label.configure(text="Status: Ready")
        
        # Apply initial voice mode theme to conversation frame
        self._apply_voice_mode_theme()


    def add_message_to_display(self, message_content, role, translated_text_for_replay=None): # Added translated_text_for_replay
        if not self.conversation_scroll_frame:
            print("Error: Conversation scroll frame not initialized.")
            return

        self.conversation_scroll_frame.update_idletasks() 
        max_bubble_width = self.conversation_scroll_frame.winfo_width() * 0.8
        if max_bubble_width <= 0: 
            max_bubble_width = self.winfo_width() * 0.5 

        is_primary_assistant = (role == "assistant") # Determine if it's the primary assistant message

        bubble = gui_elements.ConversationBubble(
            parent=self.conversation_scroll_frame, 
            message_text=message_content, 
            role=role, 
            max_width=max_bubble_width,
            is_primary_assistant_response=is_primary_assistant, # Pass this flag
            app_instance=self, # Pass app instance
            translated_text_for_replay=translated_text_for_replay if is_primary_assistant else None # Pass translated text only for primary assistant
        )

        if role == "user":
            bubble.pack(anchor="e", padx=(max_bubble_width * 0.15 , 10), pady=5, fill="x")
        elif role == "translation":
             bubble.pack(anchor="w", padx=(20, max_bubble_width * 0.10), pady=3, fill="x") # Indented
        else: 
            bubble.pack(anchor="w", padx=(10, max_bubble_width * 0.15), pady=5, fill="x")
            
        self.message_widgets.append(bubble)
        self.after(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        if self.conversation_scroll_frame:
            self.conversation_scroll_frame._parent_canvas.yview_moveto(1.0)

    def on_send_message_click(self):
        user_message = self.message_input_textbox.get("1.0", "end-1c").strip()
        if not user_message:
            return

        self.message_input_textbox.delete("1.0", "end")
        self.conversation_history.append({"role": "user", "content": user_message})
        self.add_message_to_display(user_message, "user")

        self.send_button.configure(state="disabled")
        self.message_input_textbox.configure(state="disabled")
        self.status_label.configure(text="Status: Primary LLM: Generating...")

        threading.Thread(target=self._process_message_thread, args=(user_message,), daemon=True).start()

    def _process_message_thread(self, user_message):
        if not self.primary_llm_service or not self.primary_llm_service.api_base_url or not self.primary_llm_service.api_key:
            primary_response_text = "Error: Primary LLM service not configured. Please check API settings."
            self.after(0, lambda: self._handle_llm_response(primary_response_text, is_error=True))
            return

        primary_response_text = self.primary_llm_service.generate_response(user_message)
        
        # Early exit if primary LLM failed
        if primary_response_text.startswith("Error:"):
            self.after(0, lambda: self._handle_llm_response(primary_response_text, is_error=True))
            return

        translated_text_for_response = None
        voice_status_for_response = None

        if self.is_voice_mode_on:
            self.after(0, lambda: self.status_label.configure(text="Status: Translating..."))
            
            if not self.translation_llm_service or not self.translation_llm_service.api_base_url or not self.translation_llm_service.api_key:
                translated_text_for_response = "Error: Translation LLM not configured."
            else:
                translated_text_for_response = self.translation_llm_service.generate_response(primary_response_text)

                if not translated_text_for_response.startswith("Error:"):
                    self.after(0, lambda: self.status_label.configure(text="Status: Synthesizing audio..."))
                    if not self.voicevox_service or not self.voicevox_service.base_url:
                        voice_status_for_response = "Error: Voicevox service not configured."
                    elif not VoicevoxService.is_engine_available(self.voicevox_service.base_url):
                        voice_status_for_response = f"Error: Voicevox engine not available at {self.voicevox_service.base_url}."
                    else:
                        audio_query, aq_error = self.voicevox_service.generate_audio_query(translated_text_for_response)
                        if aq_error:
                            voice_status_for_response = f"Voicevox Query Error: {aq_error}"
                        else:
                            audio_data, synth_error = self.voicevox_service.synthesize_speech_data(audio_query)
                            if synth_error:
                                voice_status_for_response = f"Voicevox Synthesis Error: {synth_error}"
                            else:
                                # Play audio in a separate thread to avoid blocking UI
                                threading.Thread(target=self._play_audio_thread, args=(audio_data,), daemon=True).start()
                                voice_status_for_response = "Audio playback initiated." # Will be updated by thread
                else: # Translation itself resulted in an error message
                    voice_status_for_response = "Skipping audio due to translation error."


        self.after(0, lambda: self._handle_llm_response(
            primary_response_text, 
            translated_text=translated_text_for_response,
            voice_status_message=voice_status_for_response
        ))
        
    def _play_audio_thread(self, audio_data):
        play_status = self.voicevox_service.play_audio_bytes(audio_data)
        self.after(0, lambda: self.status_label.configure(text=f"Status: Voicevox: {play_status}"))


    def _handle_llm_response(self, primary_response_text, translated_text=None, voice_status_message=None, is_error=False):
        successful_translated_text_for_replay = None
        if translated_text and not translated_text.startswith("Error:") and self.is_voice_mode_on:
            successful_translated_text_for_replay = translated_text

        if not is_error: 
            self.conversation_history.append({"role": "assistant", "content": primary_response_text})
            # Pass successful translated text to the primary assistant bubble for replay
            self.add_message_to_display(primary_response_text, "assistant", translated_text_for_replay=successful_translated_text_for_replay)
        else: 
            self.add_message_to_display(primary_response_text, "assistant") 

        current_status = "Status: Ready"

        if translated_text: # This is the actual display of the translation bubble
            self.conversation_history.append({"role": "translation", "content": translated_text})
            self.add_message_to_display(translated_text, "translation") # No replay text for the translation bubble itself
            if translated_text.startswith("Error:"):
                current_status = f"Status: Translation Error - {translated_text[:50]}..."
        
        if voice_status_message:
            print(f"Voice Status: {voice_status_message}") 
            if voice_status_message.startswith("Error:") and (not translated_text or not translated_text.startswith("Error:")):
                current_status = f"Status: Voicevox Error - {voice_status_message[:50]}..."
            elif "initiated" in voice_status_message or "started" in voice_status_message:
                pass 
            else: 
                 current_status = f"Status: {voice_status_message}"


        self.send_button.configure(state="normal")
        self.message_input_textbox.configure(state="normal")
        
        if is_error: # Error from primary LLM config
            self.status_label.configure(text=f"Status: Error - {primary_response_text[:50]}...")
        elif primary_response_text.startswith("Error:"): # Error from primary LLM generation
             self.status_label.configure(text=f"Status: LLM Error - {primary_response_text[:50]}...")
        else: # No error from primary LLM
            self.status_label.configure(text=current_status) # Use the aggregated status
            
            
    def clear_conversation(self):
        self.conversation_history.clear()
        for widget in self.message_widgets:
            widget.destroy()
        self.message_widgets.clear()
        self.status_label.configure(text="Status: Conversation cleared.")
        print("Conversation cleared.")

    def copy_last_ai_response(self):
        last_ai_response = None
        for message in reversed(self.conversation_history):
            if message["role"] == "assistant":
                if not message["content"].startswith("Error:"):
                    last_ai_response = message["content"]
                    break
        
        if last_ai_response:
            try:
                pyperclip.copy(last_ai_response)
                self.status_label.configure(text="Status: AI response copied to clipboard.")
            except pyperclip.PyperclipException as e:
                self.status_label.configure(text="Status: Error copying (Pyperclip issue).")
                print(f"Pyperclip error: {e}")
        else:
            self.status_label.configure(text="Status: No AI response to copy.")

    def toggle_voice_mode_globally(self):
        self.is_voice_mode_on = not self.is_voice_mode_on
        self.settings_manager.update_setting("voice_mode_on", self.is_voice_mode_on)
        if hasattr(self, 'update_voice_mode_toggle_button_text'):
            self.update_voice_mode_toggle_button_text()
        # Update status bar or provide some feedback
        current_status = f"Status: Voice mode {'On' if self.is_voice_mode_on else 'Off'}."
        # Check other service statuses to append if necessary
        if self.primary_llm_service and (not self.primary_llm_service.api_base_url or not self.primary_llm_service.api_key):
            current_status += " PrimaryLLM N/C."
        if self.is_voice_mode_on: # Only check these if voice mode is relevant
            if self.translation_llm_service and (not self.translation_llm_service.api_base_url or not self.translation_llm_service.api_key):
                current_status += " TranslateLLM N/C."
            if self.voicevox_service and not self.voicevox_service.base_url:
                current_status += " Voicevox N/C."
        self.status_label.configure(text=current_status)


    def update_voice_mode_toggle_button_text(self):
        if self.voice_mode_toggle_button: # Check if button is initialized
            self.voice_mode_toggle_button.configure(text=f"Voice: {'On' if self.is_voice_mode_on else 'Off'}")
        elif hasattr(self, 'top_control_bar'): # Attempt to find it if not directly assigned, though direct assignment in gui_elements is better
            # This is a fallback, direct assignment `app.voice_mode_toggle_button` in `create_top_control_bar` is preferred
            for widget in self.top_control_bar.winfo_children():
                if isinstance(widget, ctk.CTkButton) and "Voice:" in widget.cget("text"):
                    self.voice_mode_toggle_button = widget
                    widget.configure(text=f"Voice: {'On' if self.is_voice_mode_on else 'Off'}")
                    break


    def open_settings_panel(self):
        if self.settings_panel_window is None or not self.settings_panel_window.winfo_exists():
            self.settings_panel_window = gui_elements.SettingsPanel(parent=self, settings_manager=self.settings_manager, app=self)
            self.settings_panel_window.focus()
        else:
            self.settings_panel_window.deiconify()
            self.settings_panel_window.lift()
            self.settings_panel_window.focus()

if __name__ == "__main__":
    app = App()
    app.mainloop()
