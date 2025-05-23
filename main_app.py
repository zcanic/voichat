import customtkinter as ctk
import tkinter as tk 
import threading
import json 
import os 

import gui_elements
from settings_manager import SettingsManager
from llm_services import LLMService
from voicevox_service import VoicevoxService
import pyperclip 

class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Advanced AI LLM Chatbox - Bento UI")
        self.geometry("1200x800")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Cell attributes
        self.chat_history_cell = None
        self.message_input_cell = None
        self.voice_mode_cell = None
        self.primary_llm_quick_adjust_cell = None
        self.translation_llm_status_cell = None
        self.voicevox_status_cell = None
        self.settings_info_cell = None
        self.status_bar_cell = None 
        
        # UI Element attributes
        self.conversation_scroll_frame = None 
        self.message_input_textbox = None
        self.send_button = None
        self.status_label = None 
        self.voice_mode_toggle_button = None
        self.settings_button = None
        self.dimmer_frame = None # For settings panel dimming

        # Attributes for Primary LLM Quick Adjust Cell (B2)
        self.primary_llm_model_label = None
        self.primary_llm_temp_value_label = None
        self.primary_llm_temp_slider = None
        self.primary_llm_prompt_status_label = None

        # Attributes for Translation LLM Status Cell (B3)
        self.translation_llm_model_label = None
        self.translation_llm_prompt_status_label = None

        # Attributes for Voicevox Engine Status Cell (C1)
        self.voicevox_engine_status_display_label = None


        self.settings_manager = SettingsManager()

        self.primary_llm_service = None
        self.translation_llm_service = None
        self.voicevox_service = None
        
        self.initialize_ui() 

        self.update_primary_llm_service() 
        self.update_translation_llm_service()
        self.update_voicevox_service() 
        
        self._load_primary_llm_quick_adjust_values()
        self._load_translation_llm_status_values() 
        self.update_voicevox_engine_status_display() 


        self.conversation_history = []
        self.message_widgets = [] 

        self.sent_message_history = []
        self.sent_message_history_index = -1

        self.is_voice_mode_on = self.settings_manager.get_setting("voice_mode_on")
        self.settings_panel_window = None


        initial_theme = self.settings_manager.get_setting("appearance", "theme")
        if initial_theme:
            theme_to_apply = initial_theme.lower()
            if theme_to_apply not in ["light", "dark", "system"]:
                theme_to_apply = "system"
            ctk.set_appearance_mode(theme_to_apply.capitalize() if theme_to_apply == "system" else theme_to_apply)
        
        if self.conversation_scroll_frame: 
            self._apply_voice_mode_theme() 

    def initialize_ui(self):
        self.bento_container = ctk.CTkFrame(self, fg_color="transparent")
        self.bento_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.bento_container.grid_columnconfigure(0, weight=3) 
        self.bento_container.grid_columnconfigure(1, weight=3) 
        self.bento_container.grid_columnconfigure(2, weight=2) 
        self.bento_container.grid_columnconfigure(3, weight=2) 
        self.bento_container.grid_rowconfigure(0, weight=2) 
        self.bento_container.grid_rowconfigure(1, weight=2) 
        self.bento_container.grid_rowconfigure(2, weight=1) 

        self.cell_definitions = [
            {"name": "Chat History", "row":0, "col":0, "rowspan":2, "colspan":2, "attr": "chat_history_cell"},
            {"name": "Message Input", "row":2, "col":0, "rowspan":1, "colspan":2, "attr": "message_input_cell"},
            {"name": "Voice Mode", "row":0, "col":2, "attr": "voice_mode_cell"},
            {"name": "Primary LLM Quick Adjust", "row":1, "col":2, "attr": "primary_llm_quick_adjust_cell"},
            {"name": "Translation LLM Status", "row":2, "col":2, "attr": "translation_llm_status_cell"},
            {"name": "Voicevox Engine Status", "row":0, "col":3, "attr": "voicevox_status_cell"},
            {"name": "Settings & Info", "row":1, "col":3, "attr": "settings_info_cell"},
            {"name": "Status Bar", "row":2, "col":3, "attr": "status_bar_cell"}
        ]
        
        self._reveal_cells_sequentially()


    def _reveal_cells_sequentially(self, cell_index=0):
        if cell_index >= len(self.cell_definitions):
            self._populate_critical_cells_after_reveal()
            
            self.update_primary_llm_service() 
            self.update_translation_llm_service()
            self.update_voicevox_service()

            if hasattr(self, '_load_primary_llm_quick_adjust_values'): self._load_primary_llm_quick_adjust_values()
            if hasattr(self, '_load_translation_llm_status_values'): self._load_translation_llm_status_values()
            if hasattr(self, 'update_voicevox_engine_status_display'): self.update_voicevox_engine_status_display()
            
            if self.conversation_scroll_frame: 
               self._apply_voice_mode_theme()
            
            self.update_status_bar("All UI cells revealed and initialized.")
            return

        cell_def = self.cell_definitions[cell_index]
        created_cell = gui_elements.create_bento_cell(
            self.bento_container, cell_def["name"], cell_def["row"], cell_def["col"],
            rowspan=cell_def.get("rowspan", 1), colspan=cell_def.get("colspan", 1)
        )
        setattr(self, cell_def["attr"], created_cell) 
        
        delay_ms = 50 
        self.after(delay_ms, lambda: self._reveal_cells_sequentially(cell_index + 1))

    def _populate_critical_cells_after_reveal(self):
        # A1: Chat History
        if self.chat_history_cell:
            for widget in self.chat_history_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Chat History": widget.destroy(); break
            self.conversation_scroll_frame = ctk.CTkScrollableFrame(self.chat_history_cell, fg_color="transparent")
            self.conversation_scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # A2: Message Input
        if self.message_input_cell:
            for widget in self.message_input_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Message Input": widget.destroy(); break
            self.message_input_cell.grid_columnconfigure(0, weight=1); self.message_input_cell.grid_columnconfigure(1, weight=0) 
            self.message_input_cell.grid_rowconfigure(0, weight=1)    
            self.message_input_textbox = ctk.CTkTextbox(self.message_input_cell, height=70, border_width=1, corner_radius=8)
            self.message_input_textbox.grid(row=0, column=0, sticky="nsew", padx=(5,5), pady=5)
            self.send_button = ctk.CTkButton(self.message_input_cell, text="Send", width=70, command=self.on_send_message_click)
            self.send_button.grid(row=0, column=1, sticky="nse", padx=(0,5), pady=5)
            if self.message_input_textbox: 
                self.message_input_textbox.bind("<Up>", self.on_input_arrow_up)
                self.message_input_textbox.bind("<Down>", self.on_input_arrow_down)
        
        # B1: Voice Mode Toggle
        if self.voice_mode_cell:
            for widget in self.voice_mode_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Voice Mode": widget.destroy(); break 
            self.voice_mode_cell.grid_rowconfigure(0, weight=1); self.voice_mode_cell.grid_columnconfigure(0, weight=1) 
            self.voice_mode_toggle_button = ctk.CTkSwitch(self.voice_mode_cell, text="Voice Output", command=self.toggle_voice_mode_globally, onvalue=True, offvalue=False)
            self.voice_mode_toggle_button.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
            self.update_voice_mode_toggle_button_text()

        # B2: Primary LLM Quick Adjust
        if self.primary_llm_quick_adjust_cell:
            for widget in self.primary_llm_quick_adjust_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Primary LLM Quick Adjust": widget.destroy(); break
            self.primary_llm_quick_adjust_cell.grid_columnconfigure(0, weight=1); self.primary_llm_quick_adjust_cell.grid_columnconfigure(1, weight=2)
            for i in range(4): self.primary_llm_quick_adjust_cell.grid_rowconfigure(i, weight=0)
            ctk.CTkLabel(self.primary_llm_quick_adjust_cell, text="Model:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            self.primary_llm_model_label = ctk.CTkLabel(self.primary_llm_quick_adjust_cell, text="N/A", anchor="w", wraplength=160)
            self.primary_llm_model_label.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(self.primary_llm_quick_adjust_cell, text="Temp:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            self.primary_llm_temp_value_label = ctk.CTkLabel(self.primary_llm_quick_adjust_cell, text="0.0", anchor="w")
            self.primary_llm_temp_value_label.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
            self.primary_llm_temp_slider = ctk.CTkSlider(self.primary_llm_quick_adjust_cell, from_=0.0, to=1.0, number_of_steps=100, command=self._on_primary_llm_temp_slider_change)
            self.primary_llm_temp_slider.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0,5))
            ctk.CTkLabel(self.primary_llm_quick_adjust_cell, text="Prompt:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
            self.primary_llm_prompt_status_label = ctk.CTkLabel(self.primary_llm_quick_adjust_cell, text="N/A", anchor="w", wraplength=160)
            self.primary_llm_prompt_status_label.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        # B3: Translation LLM Status
        if self.translation_llm_status_cell:
            for widget in self.translation_llm_status_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Translation LLM Status": widget.destroy(); break
            self.translation_llm_status_cell.grid_columnconfigure(0, weight=1); self.translation_llm_status_cell.grid_columnconfigure(1, weight=2)
            self.translation_llm_status_cell.grid_rowconfigure(0, weight=0); self.translation_llm_status_cell.grid_rowconfigure(1, weight=0)
            ctk.CTkLabel(self.translation_llm_status_cell, text="Model:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            self.translation_llm_model_label = ctk.CTkLabel(self.translation_llm_status_cell, text="N/A", anchor="w", wraplength=160)
            self.translation_llm_model_label.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(self.translation_llm_status_cell, text="Prompt:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            self.translation_llm_prompt_status_label = ctk.CTkLabel(self.translation_llm_status_cell, text="N/A", anchor="w", wraplength=160)
            self.translation_llm_prompt_status_label.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # C1: Voicevox Engine Status
        if self.voicevox_status_cell:
            for widget in self.voicevox_status_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Voicevox Engine Status": widget.destroy(); break
            self.voicevox_status_cell.grid_columnconfigure(0, weight=1)
            self.voicevox_status_cell.grid_rowconfigure(0, weight=0); self.voicevox_status_cell.grid_rowconfigure(1, weight=0)
            ctk.CTkLabel(self.voicevox_status_cell, text="Voicevox Engine:").grid(row=0, column=0, sticky="nw", padx=5, pady=(5,2))
            self.voicevox_engine_status_display_label = ctk.CTkLabel(self.voicevox_status_cell, text="N/A", anchor="w", wraplength=180)
            self.voicevox_engine_status_display_label.grid(row=1, column=0, sticky="new", padx=5, pady=(0,5))
        
        # C2: Settings & Info
        if self.settings_info_cell:
            for widget in self.settings_info_cell.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Settings & Info": widget.destroy(); break
            self.settings_info_cell.grid_rowconfigure(0, weight=1); self.settings_info_cell.grid_columnconfigure(0, weight=1) 
            self.settings_button = ctk.CTkButton(self.settings_info_cell, text="Settings", command=self.open_settings_panel)
            self.settings_button.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        # C3: Status Bar
        if self.status_bar_cell:
            for widget in self.status_bar_cell.winfo_children(): 
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Status Bar": widget.destroy(); break
            self.status_bar_cell.grid_rowconfigure(0, weight=1); self.status_bar_cell.grid_columnconfigure(0, weight=1)
            self.status_label = ctk.CTkLabel(self.status_bar_cell, text="", anchor="w") 
            self.status_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=2)


    def _load_primary_llm_quick_adjust_values(self):
        if not all(hasattr(self, attr) and getattr(self, attr) is not None and getattr(self, attr).winfo_exists()
                   for attr in ['primary_llm_model_label', 'primary_llm_temp_slider', 
                                'primary_llm_temp_value_label', 'primary_llm_prompt_status_label']):
            return 
        config = self.settings_manager.get_setting("primary_llm")
        if config:
            self.primary_llm_model_label.configure(text=str(config.get("model", "N/A")))
            temp_value = config.get("temperature", 0.0); temp = float(temp_value) if isinstance(temp_value, (int, float, str)) and str(temp_value).replace('.', '', 1).isdigit() else 0.0
            self.primary_llm_temp_slider.set(temp); self.primary_llm_temp_value_label.configure(text=f"{temp:.2f}")
            prompt = config.get("system_prompt", ""); prompt_snippet = (prompt[:25] + "...") if len(prompt) > 28 else prompt 
            self.primary_llm_prompt_status_label.configure(text=prompt_snippet if prompt else "Default")
        else: 
            self.primary_llm_model_label.configure(text="N/A"); self.primary_llm_temp_value_label.configure(text="0.0")
            self.primary_llm_temp_slider.set(0.0); self.primary_llm_prompt_status_label.configure(text="N/A")

    def _on_primary_llm_temp_slider_change(self, value):
        if not all(hasattr(self, attr) and getattr(self, attr) is not None and getattr(self,attr).winfo_exists()
                   for attr in ['primary_llm_temp_value_label', 'settings_manager']): return
        temp = round(float(value), 2)
        self.primary_llm_temp_value_label.configure(text=f"{temp:.2f}")
        self.settings_manager.update_setting("primary_llm", temp, sub_key="temperature")
        self.update_primary_llm_service() 

    def _load_translation_llm_status_values(self):
        if not all(hasattr(self, attr) and getattr(self, attr) is not None and getattr(self, attr).winfo_exists()
                   for attr in ['translation_llm_model_label', 'translation_llm_prompt_status_label']): return
        config = self.settings_manager.get_setting("translation_llm")
        if config and self.translation_llm_service and self.translation_llm_service.is_configured():
            self.translation_llm_model_label.configure(text=str(config.get("model", "N/A")))
            prompt = config.get("system_prompt", "")
            if "translate" in prompt.lower() and "japanese" in prompt.lower(): self.translation_llm_prompt_status_label.configure(text="Translates to Japanese")
            elif prompt: self.translation_llm_prompt_status_label.configure(text=(prompt[:30] + "...") if len(prompt) > 33 else prompt)
            else: self.translation_llm_prompt_status_label.configure(text="Default")
        else: 
            self.translation_llm_model_label.configure(text="N/A"); self.translation_llm_prompt_status_label.configure(text="Not Configured")

    def update_primary_llm_service(self):
        config = self.settings_manager.get_setting("primary_llm")
        if config and config.get("api_base_url") and config.get("api_key"):
            self.primary_llm_service = LLMService(api_base_url=config.get("api_base_url"), api_key=config.get("api_key"), model=config.get("model"), temperature=config.get("temperature"), system_prompt=config.get("system_prompt"))
        else: self.primary_llm_service = None
        if hasattr(self, 'primary_llm_model_label') and self.primary_llm_model_label and self.primary_llm_model_label.winfo_exists(): self._load_primary_llm_quick_adjust_values()
        elif hasattr(self, 'status_label') and self.status_label and self.status_label.winfo_exists():
            if self.primary_llm_service and self.primary_llm_service.is_configured(): self.update_status_bar("Primary LLM service configured.")
            else: self.update_status_bar("Primary LLM not fully configured.", is_error=True)

    def update_translation_llm_service(self):
        config = self.settings_manager.get_setting("translation_llm")
        if config and config.get("api_base_url") and config.get("api_key"):
            self.translation_llm_service = LLMService(api_base_url=config.get("api_base_url"), api_key=config.get("api_key"), model=config.get("model"), temperature=config.get("temperature"), system_prompt=config.get("system_prompt"))
        else: self.translation_llm_service = None
        if hasattr(self, 'translation_llm_model_label') and self.translation_llm_model_label and self.translation_llm_model_label.winfo_exists(): self._load_translation_llm_status_values()

    def update_voicevox_service(self):
        config = self.settings_manager.get_setting("voicevox")
        if config and config.get("engine_address"):
            self.voicevox_service = VoicevoxService(base_url=config.get("engine_address"), speaker_id=int(config.get("speaker_id", 1)))
        else: self.voicevox_service = None
        if hasattr(self, 'voicevox_engine_status_display_label') and self.voicevox_engine_status_display_label: self.update_voicevox_engine_status_display()

    def update_voicevox_engine_status_display(self):
        if not hasattr(self, 'voicevox_engine_status_display_label') or not self.voicevox_engine_status_display_label or not self.voicevox_engine_status_display_label.winfo_exists(): return 
        default_text_color = ("black", "white") 
        try:
            text_color_tuple = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
            default_text_color = text_color_tuple[1] if ctk.get_appearance_mode() == "Dark" else text_color_tuple[0]
        except Exception: pass 
        if self.voicevox_service and self.voicevox_service.is_configured(): self.voicevox_engine_status_display_label.configure(text="Configured", text_color=default_text_color)
        else: self.voicevox_engine_status_display_label.configure(text="Not Configured", text_color="orange")

    def add_dimmer(self):
        if not hasattr(self, 'dimmer_frame') or self.dimmer_frame is None or not self.dimmer_frame.winfo_exists():
            # Dimmer should be on top of bento_container, but below the settings panel.
            # Create it on `self` (the main app window) to ensure it can overlay everything effectively.
            self.dimmer_frame = ctk.CTkFrame(self, fg_color=("black", "black"), corner_radius=0) # Solid black
            self.dimmer_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            # Attempt to set window attribute for transparency. This is platform-dependent.
            # For a more reliable cross-platform "dim" effect without true alpha on child frames,
            # a very dark color is used. Actual transparency might not be achieved on all systems for a frame.
            try:
                 self.attributes("-alpha", 0.75) # This makes the *entire app window* transparent
                 # So, this is not what we want for a dimmer frame within the app.
                 # The best we can do with a CTkFrame is a dark color.
                 # True alpha blending for a child frame is complex.
                 # Revert to a dark color for the frame.
                 self.dimmer_frame.configure(fg_color=("gray10", "gray10")) # Dark semi-opaque color
            except tk.TclError: # If -alpha is not supported (e.g. wayland without proper compositor)
                 print("Alpha transparency for dimmer not supported, using solid dark color.")
                 self.dimmer_frame.configure(fg_color=("gray10", "gray10")) # Fallback to dark solid color
        self.dimmer_frame.lift()


    def remove_dimmer(self):
        if hasattr(self, 'dimmer_frame') and self.dimmer_frame is not None and self.dimmer_frame.winfo_exists():
            self.dimmer_frame.destroy()
            self.dimmer_frame = None
            # If we made the main window transparent, revert it.
            # However, the current dimmer logic uses a Frame, not main window transparency.
            # So, this line might not be needed unless the strategy for add_dimmer changes.
            # try: self.attributes("-alpha", 1.0) # Fully opaque
            # except tk.TclError: pass 
    
    def open_settings_panel(self):
        if self.settings_panel_window is None or not self.settings_panel_window.winfo_exists():
            self.add_dimmer() 
            self.settings_panel_window = gui_elements.SettingsPanel(self, settings_manager=self.settings_manager, app=self)
            if self.dimmer_frame: 
                 self.settings_panel_window.lift(aboveThis=self.dimmer_frame)
            else: 
                 self.settings_panel_window.lift()
            self.settings_panel_window.animate_open() 
            self.update_status_bar("Settings panel opened.")
        else:
            self.settings_panel_window.deiconify()
            self.add_dimmer() 
            self.settings_panel_window.lift(aboveThis=self.dimmer_frame if self.dimmer_frame else None)
            if hasattr(self.settings_panel_window, 'animate_open'):
                 self.settings_panel_window.animate_open() 
            else:
                 self.settings_panel_window.grab_set() 
            
    def on_send_message_click(self):
        if not self.message_input_textbox: 
            self.update_status_bar("Error: Message input UI not ready.", is_error=True)
            return
        user_message = self.message_input_textbox.get("1.0", "end-1c").strip()
        if not user_message: return
        self.set_input_active(False)
        self.update_status_bar("Processing message...")
        if not self.sent_message_history or (self.sent_message_history and user_message != self.sent_message_history[-1]):
            self.sent_message_history.append(user_message)
        self.sent_message_history_index = len(self.sent_message_history)
        self.message_input_textbox.delete("1.0", "end")
        self.conversation_history.append({"role": "user", "content": user_message})
        self.add_message_to_display(user_message, "user")
        threading.Thread(target=self._process_message_thread, args=(user_message,), daemon=True).start()

    def _process_message_thread(self, user_message):
        primary_response_text, translated_text_for_response, voice_status_for_response, has_critical_error = None, None, None, False
        if not self.primary_llm_service or not self.primary_llm_service.is_configured():
            self.after(0, lambda: gui_elements.show_critical_error_dialog(self, "Primary LLM Error", "Primary LLM not configured."))
            primary_response_text, has_critical_error = "Error: Primary LLM not configured.", True
        else:
            self.after(0, lambda: self.update_status_bar("Primary LLM: Generating response..."))
            primary_response_text = self.primary_llm_service.generate_response(user_message)

        if not has_critical_error and self.is_voice_mode_on and not primary_response_text.startswith("Error:"):
            if not self.translation_llm_service or not self.translation_llm_service.is_configured():
                translated_text_for_response = "Info: Translation LLM not configured. Skipping translation."
                self.after(0, lambda: self.update_status_bar(translated_text_for_response, is_error=True))
            else:
                self.after(0, lambda: self.update_status_bar("Translation LLM: Translating..."))
                translated_text_for_response = self.translation_llm_service.generate_response(primary_response_text)

            if translated_text_for_response and not (translated_text_for_response.startswith("Error:") or translated_text_for_response.startswith("Info:")):
                if not self.voicevox_service or not self.voicevox_service.is_configured():
                    voice_status_for_response, _ = "Info: Voicevox service not configured. Skipping audio.", self.after(0, lambda: self.update_status_bar(voice_status_for_response, is_error=True))
                else:
                    available, status_msg = VoicevoxService.is_engine_available(self.voicevox_service.base_url)
                    if not available:
                        self.after(0, lambda: gui_elements.show_critical_error_dialog(self, "Voicevox Error", status_msg))
                        voice_status_for_response = f"Error: Voicevox engine unavailable. {status_msg}"
                    else:
                        self.after(0, lambda: self.update_status_bar("Voicevox: Synthesizing audio..."))
                        audio_query, error_msg_aq = self.voicevox_service.generate_audio_query(translated_text_for_response)
                        if error_msg_aq: voice_status_for_response = f"Error (Audio Query): {error_msg_aq}"
                        else:
                            audio_data, error_msg_synth = self.voicevox_service.synthesize_speech_data(audio_query)
                            if error_msg_synth: voice_status_for_response = f"Error (Synthesis): {error_msg_synth}"
                            else:
                                threading.Thread(target=self._play_audio_thread, args=(audio_data, "main"), daemon=True).start()
                                voice_status_for_response = "Audio playing..."
            elif translated_text_for_response and (translated_text_for_response.startswith("Error:") or translated_text_for_response.startswith("Info:")):
                 voice_status_for_response = "Skipping audio due to translation issue."
        self.after(0, lambda: self._handle_llm_response(primary_response_text, translated_text_for_response, voice_status_for_response, has_critical_error))

    def _play_audio_thread(self, audio_data, context="main"): 
        self.after(0, lambda: self.update_status_bar(f"Voicevox: Playing audio ({context})..."))
        success, msg = self.voicevox_service.play_audio_bytes(audio_data)
        self.after(0, lambda: self.update_status_bar(f"Voicevox: {msg}", is_error=not success))
        if context == "main" or context == "replay": self.after(0, lambda: self.set_input_active(True))
        if success and context == "main": self.after(100, lambda: self.update_status_bar("Ready."))

    def _handle_llm_response(self, primary_response_text, translated_text, voice_status_message, is_critical_error):
        if not is_critical_error: 
            self.conversation_history.append({"role": "assistant", "content": primary_response_text})
            ttfr = translated_text if self.is_voice_mode_on and translated_text and not (translated_text.startswith("Error:") or translated_text.startswith("Info:")) else None
            self.add_message_to_display(primary_response_text, "assistant", translated_text_for_replay=ttfr)
        if translated_text: 
            self.conversation_history.append({"role": "translation", "content": translated_text})
            self.add_message_to_display(translated_text, "translation")
        final_status, is_final_status_error = "Ready.", False
        if is_critical_error: final_status, is_final_status_error = primary_response_text, True
        elif primary_response_text.startswith("Error:"): final_status, is_final_status_error = primary_response_text, True
        elif translated_text and (translated_text.startswith("Error:") or translated_text.startswith("Info:")): final_status, is_final_status_error = translated_text, True
        elif voice_status_message and (voice_status_message.startswith("Error:") or voice_status_message.startswith("Info:")): final_status, is_final_status_error = voice_status_message, True
        elif voice_status_message and not (voice_status_message == "Audio playing..." or "initiated" in voice_status_message): final_status = voice_status_message
        if not (self.is_voice_mode_on and voice_status_message == "Audio playing..." and not is_critical_error):
            self.set_input_active(True); self.update_status_bar(final_status, is_error=is_final_status_error)

    def add_message_to_display(self, message_content, role, translated_text_for_replay=None):
        if not self.conversation_scroll_frame or not self.conversation_scroll_frame.winfo_exists(): 
            print(f"Debug: Conv. area not ready. ({role}) {message_content}"); return
        try:
            self.conversation_scroll_frame.update_idletasks(); max_bubble_width = self.conversation_scroll_frame.winfo_width()*0.8
            if max_bubble_width <= 0: max_bubble_width = self.winfo_width()*0.6 
        except Exception as e: print(f"Error getting scroll frame width: {e}"); max_bubble_width = 500 
        bubble = gui_elements.ConversationBubble(self.conversation_scroll_frame, message_text=message_content, role=role, max_width=max_bubble_width, is_primary_assistant_response=(role=="assistant"), app_instance=self, translated_text_for_replay=translated_text_for_replay)
        bubble.pack(anchor="e" if role == "user" else "w", padx=bubble.pack_padx_outer, pady=5, fill="x")
        self.message_widgets.append(bubble); self.after(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        if self.conversation_scroll_frame and self.conversation_scroll_frame.winfo_exists(): self.conversation_scroll_frame._parent_canvas.yview_moveto(1.0)

    def clear_conversation(self):
        self.conversation_history.clear(); [w.destroy() for w in self.message_widgets]; self.message_widgets.clear()
        self.update_status_bar("Conversation cleared.")

    def copy_last_ai_response(self):
        last_ai_message = next((m["content"] for m in reversed(self.conversation_history) if m["role"] == "assistant" and not m["content"].startswith("Error:")), None)
        if last_ai_message:
            try: pyperclip.copy(last_ai_message); self.update_status_bar("Copied to clipboard.")
            except Exception as e: self.update_status_bar(f"Error copying: {e}", is_error=True)
        else: self.update_status_bar("No AI response to copy.", is_error=True)

    def toggle_voice_mode_globally(self):
        self.is_voice_mode_on = not self.is_voice_mode_on
        self.settings_manager.update_setting("voice_mode_on", self.is_voice_mode_on)
        if hasattr(self, 'voice_mode_toggle_button') and self.voice_mode_toggle_button: self.update_voice_mode_toggle_button_text()
        if hasattr(self, 'conversation_scroll_frame') and self.conversation_scroll_frame: self._apply_voice_mode_theme()
        status_msg, is_err_status = f"Voice Mode {'ON' if self.is_voice_mode_on else 'OFF'}.", False
        if self.is_voice_mode_on:
            if not self.translation_llm_service or not self.translation_llm_service.is_configured(): status_msg += " Translation LLM not configured."; is_err_status = True
            if not self.voicevox_service or not self.voicevox_service.is_configured(): status_msg += " Voicevox service not configured."; is_err_status = True
            elif self.voicevox_service.is_configured():
                available, engine_msg = VoicevoxService.is_engine_available(self.voicevox_service.base_url)
                if not available: status_msg += f" Voicevox engine unavailable: {engine_msg}"; is_err_status = True
        self.update_status_bar(status_msg, is_error=is_err_status)

    def update_voice_mode_toggle_button_text(self):
        if not self.voice_mode_toggle_button or not self.voice_mode_toggle_button.winfo_exists(): return 
        if self.is_voice_mode_on: self.voice_mode_toggle_button.select(); self.voice_mode_toggle_button.configure(text="Voice ON (日本語)")
        else: self.voice_mode_toggle_button.deselect(); self.voice_mode_toggle_button.configure(text="Voice OFF")

    def _apply_voice_mode_theme(self):
        if not self.conversation_scroll_frame or not self.conversation_scroll_frame.winfo_exists(): return 
        try:
            frame_theme = ctk.ThemeManager.theme["CTkScrollableFrame"]
            default_border_color, default_border_width = frame_theme["border_color"], frame_theme["border_width"]
        except KeyError: default_border_color, default_border_width = ("gray70", "gray30"), 0
        current_mode = ctk.get_appearance_mode()
        actual_default_border_color = default_border_color[1] if isinstance(default_border_color, tuple) and current_mode == "Dark" else default_border_color[0] if isinstance(default_border_color, tuple) else default_border_color
        if self.is_voice_mode_on: self.conversation_scroll_frame.configure(border_color="green", border_width=2)
        else: self.conversation_scroll_frame.configure(border_color=actual_default_border_color, border_width=default_border_width)
            
    def replay_audio(self, text_to_speak):
        self.update_status_bar("Replaying audio...")
        if not text_to_speak: self.update_status_bar("Error: No text for replay.", is_error=True); return
        if not self.voicevox_service or not self.voicevox_service.is_configured():
            gui_elements.show_critical_error_dialog(self, "Voicevox Error", "Voicevox not configured."); self.update_status_bar("Error: Voicevox not configured for replay.", is_error=True); return
        available, status_msg = VoicevoxService.is_engine_available(self.voicevox_service.base_url)
        if not available:
            gui_elements.show_critical_error_dialog(self, "Voicevox Error", f"Voicevox engine unavailable: {status_msg}"); self.update_status_bar(f"Error: Voicevox engine unavailable for replay. {status_msg}", is_error=True); return
        self.set_input_active(False); self.update_status_bar("Voicevox: Synthesizing replay...")
        threading.Thread(target=self._replay_audio_thread_worker, args=(text_to_speak,), daemon=True).start()

    def _replay_audio_thread_worker(self, text_to_speak):
        audio_query, error_msg_aq = self.voicevox_service.generate_audio_query(text_to_speak)
        if error_msg_aq: self.after(0, lambda: [self.update_status_bar(f"Replay Error (Query): {error_msg_aq}", is_error=True), self.set_input_active(True)]); return
        audio_data, error_msg_synth = self.voicevox_service.synthesize_speech_data(audio_query)
        if error_msg_synth: self.after(0, lambda: [self.update_status_bar(f"Replay Error (Synth): {error_msg_synth}", is_error=True), self.set_input_active(True)]); return
        self._play_audio_thread(audio_data, "replay")

    def cycle_theme(self):
        current_theme_name = ctk.get_appearance_mode(); themes = ["Light", "Dark", "System"] 
        try: current_index = themes.index(current_theme_name)
        except ValueError: current_index = themes.index("System") 
        self.apply_theme_from_settings_panel(themes[(current_index + 1) % len(themes)])

    def apply_theme_from_settings_panel(self, theme_name: str): 
        if theme_name in ["Light", "Dark", "System"]:
            ctk.set_appearance_mode(theme_name); self.settings_manager.update_setting("appearance", "theme", theme_name.lower())
            self.update_status_bar(f"Theme changed to {theme_name}.")
        else: self.update_status_bar(f"Invalid theme name: {theme_name}", is_error=True)

    def update_status_bar(self, message: str, is_error: bool = False): 
        if self.status_label and self.status_label.winfo_exists(): 
            prefix = "Error: " if is_error else "Status: "; default_text_color = ("black", "white")
            try: 
                text_color_tuple = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
                default_text_color = text_color_tuple[1] if ctk.get_appearance_mode() == "Dark" else text_color_tuple[0]
            except Exception: pass
            self.status_label.configure(text=prefix + message, text_color="red" if is_error else default_text_color)
        else: print(f"Status Update (Label N/A): {message}") 

    def set_input_active(self, is_active: bool): 
        try:
            if self.message_input_textbox and self.message_input_textbox.winfo_exists(): self.message_input_textbox.configure(state="normal" if is_active else "disabled")
            if self.send_button and self.send_button.winfo_exists(): self.send_button.configure(state="normal" if is_active else "disabled", text="Send" if is_active else "Processing...")
        except tk.TclError as e: print(f"Error configuring input widgets: {e}")
                
    def on_input_arrow_up(self, event=None): 
        if not self.message_input_textbox or not self.sent_message_history: return "break"
        if self.sent_message_history_index == len(self.sent_message_history): self.sent_message_history_index = len(self.sent_message_history) - 1
        elif self.sent_message_history_index > 0: self.sent_message_history_index -= 1
        else: self.sent_message_history_index = 0
        if 0 <= self.sent_message_history_index < len(self.sent_message_history):
            self.message_input_textbox.delete("1.0", "end"); self.message_input_textbox.insert("1.0", self.sent_message_history[self.sent_message_history_index]); self.message_input_textbox.mark_set("insert", "end")
        return "break"

    def on_input_arrow_down(self, event=None):
        if not self.message_input_textbox or not self.sent_message_history: return "break"
        if self.sent_message_history_index < len(self.sent_message_history) - 1:
            self.sent_message_history_index += 1
            self.message_input_textbox.delete("1.0", "end"); self.message_input_textbox.insert("1.0", self.sent_message_history[self.sent_message_history_index]); self.message_input_textbox.mark_set("insert", "end")
        elif self.sent_message_history_index == len(self.sent_message_history) - 1:
            self.sent_message_history_index += 1; self.message_input_textbox.delete("1.0", "end")
        return "break"

if __name__ == "__main__":
    app = App()
    app.mainloop()

```
