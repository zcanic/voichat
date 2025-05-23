import customtkinter as ctk
import tkinter as tk
from settings_manager import SettingsManager

# --- Bento Cell Creation ---
def create_bento_cell(parent_container, cell_name, row, col, rowspan=1, colspan=1, 
                      fg_color=("gray75", "gray25"), text_color=None, 
                      border_width=1, border_color=("gray60", "gray40")):
    """
    Creates a standardized styled frame (a "bento cell") within a parent container.
    The cell includes a placeholder label with its name, which should ideally be
    removed or replaced by actual content later.
    """
    cell_frame = ctk.CTkFrame(
        parent_container, 
        fg_color=fg_color,
        border_width=border_width,
        border_color=border_color,
        corner_radius=8 
    )
    cell_frame.grid(row=row, column=col, rowspan=rowspan, colspan=colspan, sticky="nsew", padx=5, pady=5)
    
    label = ctk.CTkLabel(cell_frame, text=cell_name, text_color=text_color)
    label.place(relx=0.5, rely=0.5, anchor="center") 
    
    return cell_frame

# --- Conversation Bubble ---
class ConversationBubble(ctk.CTkFrame):
    def __init__(self, parent, message_text, role, max_width=400, 
                 is_primary_assistant_response=False, app_instance=None, 
                 translated_text_for_replay=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.app_instance = app_instance
        self.translated_text_for_replay = translated_text_for_replay
        self.role = role

        if role == "user":
            self.configure(fg_color=("#3b82f6", "#2563eb")) # Tailwind blue-500 / blue-600
            self.pack_padx_outer = (50, 10) 
            text_anchor = "e"
        elif role == "assistant":
            self.configure(fg_color=("#e5e7eb", "#374151")) # Tailwind gray-200 / gray-700
            self.pack_padx_outer = (10, 50)
            text_anchor = "w"
        elif role == "translation":
            self.configure(fg_color=("#a855f7", "#7e22ce")) # Tailwind purple-500 / purple-700
            self.pack_padx_outer = (20, 60) 
            text_anchor = "w"
        else: 
            self.configure(fg_color="red")
            self.pack_padx_outer = (10, 10)
            text_anchor = "c"

        self.columnconfigure(0, weight=1) 
        if role == "assistant" and self.app_instance and self.translated_text_for_replay:
            self.columnconfigure(1, weight=0) 

        self.message_label = ctk.CTkLabel(
            self, text=message_text, wraplength=max_width - 40,
            justify="left" if text_anchor == "w" else "right", anchor=text_anchor
        )
        self.message_label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        if role == "assistant" and self.app_instance and self.translated_text_for_replay:
            self.replay_button = ctk.CTkButton(
                self, text="🗣️", width=20, height=20,
                command=self._replay_audio_action,
                fg_color="transparent", hover_color=("gray70", "gray30")
            )
            self.replay_button.grid(row=0, column=1, sticky="e", padx=(0,5), pady=5)

    def _replay_audio_action(self):
        if self.app_instance and self.translated_text_for_replay:
            self.app_instance.replay_audio(self.translated_text_for_replay)


# --- Settings Panel ---
class SettingsPanel(ctk.CTkToplevel):
    def __init__(self, parent, settings_manager: SettingsManager, app=None, **kwargs): 
        super().__init__(parent, **kwargs)
        self.app_instance = app 
        self.settings_manager = settings_manager
        
        self.title("Settings")
        
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        self.target_width = int(parent_width * 0.7)
        self.target_height = int(parent_height * 0.8)
        
        self.initial_x = parent.winfo_x() + (parent_width - self.target_width) // 2
        self.initial_y = parent.winfo_y() + (parent_height - self.target_height) // 2
        
        self.current_height = 10 
        y_start_pos = self.initial_y + (self.target_height // 2) - (self.current_height // 2)
        self.geometry(f"{self.target_width}x{self.current_height}+{self.initial_x}+{y_start_pos}")

        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.start_close_animation)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(expand=True, fill="both", padx=5, pady=5)

        self._create_llm_settings_tab(self.tab_view.add("Primary LLM"))
        self._create_llm_settings_tab(self.tab_view.add("Translation LLM"), llm_type="translation_llm")
        self._create_voicevox_settings_tab(self.tab_view.add("Voicevox TTS"))
        self._create_appearance_settings_tab(self.tab_view.add("Appearance"))
        self._create_data_management_tab(self.tab_view.add("Data"))

        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=5, pady=(5,10))
        
        self.save_button = ctk.CTkButton(self.buttons_frame, text="Save & Close", command=self._save_and_close)
        self.save_button.pack(side="right", padx=(10,0))
        
        self.cancel_button = ctk.CTkButton(self.buttons_frame, text="Cancel", command=self.start_close_animation, fg_color=("gray60", "gray25"))
        self.cancel_button.pack(side="right")

    def animate_open(self, current_height=None):
        if current_height is None:
            current_height = self.current_height
        
        animation_steps = 20 
        step_height_increment = int((self.target_height - self.current_height) / animation_steps) if animation_steps > 0 else (self.target_height - self.current_height)
        if step_height_increment < 1 and self.target_height > current_height : step_height_increment = 1
        
        new_height = min(current_height + step_height_increment, self.target_height)
        
        new_y = self.initial_y + (self.target_height - new_height) // 2
        
        self.geometry(f"{self.target_width}x{int(new_height)}+{self.initial_x}+{new_y}")
        self.current_height = new_height

        if new_height < self.target_height:
            self.after(15, lambda: self.animate_open(new_height)) 
        else:
            self.geometry(f"{self.target_width}x{int(self.target_height)}+{self.initial_x}+{self.initial_y}") 
            self.grab_set() 
            self.lift()     

    def start_close_animation(self):
        if self.app_instance:
            self.app_instance.remove_dimmer() 
        self.grab_release() 
        self.animate_close()

    def animate_close(self, current_height=None):
        if current_height is None:
            current_height = self.winfo_height()
        
        animation_steps = 20
        step_height_decrement = int(self.target_height / animation_steps) 
        if step_height_decrement < 1: step_height_decrement = 1
        animation_delay_ms = 10
        
        new_height = max(current_height - step_height_decrement, 0)
        new_y = self.initial_y + (self.target_height - new_height) // 2

        self.geometry(f"{self.target_width}x{int(new_height)}+{self.initial_x}+{new_y}")

        if new_height > 0:
            self.after(animation_delay_ms, lambda: self.animate_close(new_height))
        else:
            self.destroy()

    def _create_llm_settings_tab(self, tab, llm_type="primary_llm"):
        settings = self.settings_manager.get_setting(llm_type)
        
        ctk.CTkLabel(tab, text="API Base URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        api_base_entry = ctk.CTkEntry(tab, width=350)
        api_base_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        api_base_entry.insert(0, settings.get("api_base_url", ""))
        
        ctk.CTkLabel(tab, text="API Key:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        api_key_entry = ctk.CTkEntry(tab, width=350, show="*")
        api_key_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        api_key_entry.insert(0, settings.get("api_key", ""))
        
        ctk.CTkLabel(tab, text="Model:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        model_entry = ctk.CTkEntry(tab, width=350)
        model_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        model_entry.insert(0, settings.get("model", ""))
        
        ctk.CTkLabel(tab, text="Temperature:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        temp_entry = ctk.CTkEntry(tab, width=100)
        temp_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        temp_entry.insert(0, str(settings.get("temperature", "0.2")))

        ctk.CTkLabel(tab, text="System Prompt:").grid(row=4, column=0, padx=5, pady=(5,0), sticky="nw")
        system_prompt_textbox = ctk.CTkTextbox(tab, height=100, wrap="word")
        system_prompt_textbox.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        system_prompt_textbox.insert("1.0", settings.get("system_prompt", ""))
        
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(5, weight=1)

        setattr(self, f"{llm_type}_api_base_entry", api_base_entry)
        setattr(self, f"{llm_type}_api_key_entry", api_key_entry)
        setattr(self, f"{llm_type}_model_entry", model_entry)
        setattr(self, f"{llm_type}_temp_entry", temp_entry)
        setattr(self, f"{llm_type}_system_prompt_textbox", system_prompt_textbox)

    def _create_voicevox_settings_tab(self, tab):
        settings = self.settings_manager.get_setting("voicevox")
        
        ctk.CTkLabel(tab, text="Voicevox Engine Address:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.voicevox_engine_entry = ctk.CTkEntry(tab, width=300)
        self.voicevox_engine_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.voicevox_engine_entry.insert(0, settings.get("engine_address", "http://localhost:50021"))

        ctk.CTkLabel(tab, text="Speaker ID:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.voicevox_speaker_id_entry = ctk.CTkEntry(tab, width=100)
        self.voicevox_speaker_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.voicevox_speaker_id_entry.insert(0, str(settings.get("speaker_id", "1")))
        
        self.voicevox_test_button = ctk.CTkButton(tab, text="Test Voicevox", command=self._test_voicevox)
        self.voicevox_test_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        tab.grid_columnconfigure(1, weight=1)

    def _create_appearance_settings_tab(self, tab):
        settings = self.settings_manager.get_setting("appearance")
        
        ctk.CTkLabel(tab, text="Theme:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.theme_menu = ctk.CTkOptionMenu(tab, values=["Light", "Dark", "System"],
                                            command=self._on_theme_change)
        self.theme_menu.set(settings.get("theme", "system").capitalize())
        self.theme_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def _create_data_management_tab(self, tab):
        ctk.CTkLabel(tab, text="Conversation History:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.clear_conv_button = ctk.CTkButton(tab, text="Clear Conversation History", command=self._confirm_clear_conversation)
        self.clear_conv_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(tab, text="Settings File:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.reset_settings_button = ctk.CTkButton(tab, text="Reset All Settings to Default", command=self._confirm_reset_settings)
        self.reset_settings_button.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def _on_theme_change(self, new_theme: str):
        if self.app_instance:
            self.app_instance.apply_theme_from_settings_panel(new_theme)

    def _save_settings(self):
        self.settings_manager.update_setting("primary_llm", self.primary_llm_api_base_entry.get(), "api_base_url")
        self.settings_manager.update_setting("primary_llm", self.primary_llm_api_key_entry.get(), "api_key")
        self.settings_manager.update_setting("primary_llm", self.primary_llm_model_entry.get(), "model")
        self.settings_manager.update_setting("primary_llm", float(self.primary_llm_temp_entry.get()), "temperature")
        self.settings_manager.update_setting("primary_llm", self.primary_llm_system_prompt_textbox.get("1.0", "end-1c"), "system_prompt")

        self.settings_manager.update_setting("translation_llm", self.translation_llm_api_base_entry.get(), "api_base_url")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_api_key_entry.get(), "api_key")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_model_entry.get(), "model")
        self.settings_manager.update_setting("translation_llm", float(self.translation_llm_temp_entry.get()), "temperature")
        self.settings_manager.update_setting("translation_llm", self.translation_llm_system_prompt_textbox.get("1.0", "end-1c"), "system_prompt")
        
        self.settings_manager.update_setting("voicevox", self.voicevox_engine_entry.get(), "engine_address")
        self.settings_manager.update_setting("voicevox", int(self.voicevox_speaker_id_entry.get()), "speaker_id")
        
        self.settings_manager.save_settings()

        if self.app_instance:
            self.app_instance.update_primary_llm_service()
            self.app_instance.update_translation_llm_service()
            self.app_instance.update_voicevox_service()
            self.app_instance.update_status_bar("Settings saved and services updated.")

    def _save_and_close(self):
        self._save_settings()
        self.start_close_animation()

    def _test_voicevox(self):
        if self.app_instance and self.app_instance.voicevox_service:
            base_url = self.voicevox_engine_entry.get()
            speaker_id = int(self.voicevox_speaker_id_entry.get())
            test_service = VoicevoxService(base_url=base_url, speaker_id=speaker_id)
            available, message = test_service.is_engine_available(base_url)
            
            if available:
                success, audio_data, error_msg = test_service.generate_and_get_audio_data("テスト。")
                if success:
                    threading.Thread(target=test_service.play_audio_bytes, args=(audio_data,), daemon=True).start()
                    show_info_dialog(self, "Voicevox Test", "Test audio should be playing.")
                else:
                    show_critical_error_dialog(self, "Voicevox Test Error", f"Failed to generate test audio: {error_msg}")
            else:
                show_critical_error_dialog(self, "Voicevox Test Error", f"Engine not available: {message}")
        else:
            show_critical_error_dialog(self, "Voicevox Test Error", "Voicevox service not initialized in main app.")

    def _confirm_clear_conversation(self):
        ConfirmationDialog(self, "Clear Conversation?", 
                           "Are you sure you want to clear the conversation history? This cannot be undone.",
                           lambda: self.app_instance.clear_conversation() if self.app_instance else None)

    def _confirm_reset_settings(self):
        ConfirmationDialog(self, "Reset Settings?", 
                           "Are you sure you want to reset ALL settings to their defaults? The application will close.",
                           self._execute_reset_settings)
    
    def _execute_reset_settings(self):
        self.settings_manager.reset_to_defaults()
        self.settings_manager.save_settings()
        if self.app_instance:
            show_info_dialog(self.app_instance, "Settings Reset", "Settings have been reset to default. Please restart the application.")
            self.app_instance.destroy() 
        else:
            self.destroy()

# --- Utility Dialogs ---
def show_critical_error_dialog(parent, title, message):
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x150")
    dialog.transient(parent)
    dialog.attributes("-topmost", True)
    dialog.grab_set()
    label = ctk.CTkLabel(dialog, text=message, wraplength=380)
    label.pack(padx=20, pady=20, expand=True, fill="both")
    ok_button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
    ok_button.pack(pady=10)
    dialog.wait_window()

def show_info_dialog(parent, title, message):
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("300x150")
    dialog.transient(parent)
    dialog.attributes("-topmost", True)
    dialog.grab_set()
    label = ctk.CTkLabel(dialog, text=message, wraplength=280)
    label.pack(padx=20, pady=20, expand=True, fill="both")
    ok_button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
    ok_button.pack(pady=10)
    dialog.wait_window()

class ConfirmationDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, command_on_yes):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.attributes("-topmost", True)
        self.grab_set()

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        label = ctk.CTkLabel(self.main_frame, text=message, wraplength=300)
        label.pack(pady=(0,20), expand=True, fill="x")

        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        buttons_frame.columnconfigure((0,1), weight=1)

        self.yes_button = ctk.CTkButton(buttons_frame, text="Yes", command=lambda: self._action_and_close(command_on_yes), width=100)
        self.yes_button.grid(row=0, column=0, padx=(0,5), sticky="e")

        self.no_button = ctk.CTkButton(buttons_frame, text="No", command=self.destroy, width=100, fg_color=("gray60", "gray25"))
        self.no_button.grid(row=0, column=1, padx=(5,0), sticky="w")
        
        self.after(100, self._center_window) 
        self.wait_window()

    def _center_window(self):
        try:
            self.update_idletasks()
            parent_x = self.master.winfo_x()
            parent_y = self.master.winfo_y()
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()
            
            dialog_width = self.winfo_width()
            dialog_height = self.winfo_height()
            
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            self.geometry(f"+{x}+{y}")
        except Exception as e:
            print(f"Error centering confirmation dialog: {e}")

    def _action_and_close(self, command):
        if command:
            command()
        self.destroy()
```
