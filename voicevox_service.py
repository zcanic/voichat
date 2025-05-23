import requests
import json
import sounddevice as sd
import soundfile as sf # For robust WAV parsing
import io
import time # For example usage delay

class VoicevoxService:
    def __init__(self, base_url="http://localhost:50021", speaker_id=1):
        self.base_url = base_url
        try:
            self.speaker_id = int(speaker_id)
        except ValueError:
            print(f"Warning: Invalid speaker_id '{speaker_id}', defaulting to 1.")
            self.speaker_id = 1


    def update_config(self, base_url, speaker_id):
        self.base_url = base_url
        try:
            self.speaker_id = int(speaker_id)
        except ValueError:
            print(f"Warning: Invalid speaker_id '{speaker_id}' during update, defaulting to 1.")
            self.speaker_id = 1
        print(f"VoicevoxService config updated: URL={self.base_url}, SpeakerID={self.speaker_id}")

    def is_configured(self):
        """Checks if the essential base URL is configured."""
        return bool(self.base_url)

    @staticmethod
    def is_engine_available(base_url):
        if not base_url:
            return False, "Error: Base URL not provided."
        try:
            response = requests.get(f"{base_url}/version", timeout=2)
            response.raise_for_status()
            return True, f"Engine available, version: {response.text}"
        except requests.exceptions.Timeout:
            return False, "Error: Connection timed out."
        except requests.exceptions.ConnectionError:
            return False, "Error: Connection failed."
        except requests.exceptions.HTTPError as e:
            return False, f"Error: HTTP {e.response.status_code} - {e.response.reason}."
        except requests.exceptions.RequestException as e:
            return False, f"Error: Request failed ({e.__class__.__name__})."
        except Exception as e:
            return False, f"Error: An unexpected error occurred ({e.__class__.__name__})."

    @staticmethod
    def get_speakers(base_url):
        if not base_url:
            return None, "Error: Voicevox base_url not configured."
        try:
            response = requests.get(f"{base_url}/speakers", timeout=5)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.Timeout:
            return None, "Error: Request for speakers timed out."
        except requests.exceptions.ConnectionError:
            return None, f"Error: Could not connect to Voicevox at {base_url} for speakers."
        except requests.exceptions.HTTPError as e:
            return None, f"Error: Speaker request failed. Status: {e.response.status_code}. Response: {e.response.text}"
        except requests.exceptions.RequestException as e:
            return None, f"Error getting Voicevox speakers: {e}"
        except json.JSONDecodeError as e:
            return None, f"Error: Could not decode JSON from speakers. Response: {response.text}. Details: {e}"


    def generate_audio_query(self, text):
        if not self.base_url:
            return None, "Error: Voicevox base_url not configured."
        if not text:
            return None, "Error: Text for audio query cannot be empty."
        
        params = {"text": text, "speaker": self.speaker_id}
        try:
            response = requests.post(f"{self.base_url}/audio_query", params=params, timeout=10)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            return None, f"Error: Voicevox audio_query request failed: {e}"
        except json.JSONDecodeError:
            return None, f"Error: Could not decode JSON from audio_query. Response: {response.text}"

    def synthesize_speech_data(self, audio_query_json):
        if not self.base_url:
            return None, "Error: Voicevox base_url not configured."
        if not audio_query_json:
            return None, "Error: Audio query JSON cannot be empty for synthesis."

        headers = {"Content-Type": "application/json"}
        params = {"speaker": self.speaker_id}
        
        try:
            response = requests.post(
                f"{self.base_url}/synthesis", 
                params=params, 
                json=audio_query_json, 
                headers=headers, 
                timeout=20
            )
            response.raise_for_status()
            return response.content, None
        except requests.exceptions.RequestException as e:
            return None, f"Error: Voicevox synthesis request failed: {e}"

    def play_audio_bytes(self, audio_bytes):
        if not audio_bytes:
            return False, "Error: No audio data to play."
        try:
            data, samplerate = sf.read(io.BytesIO(audio_bytes))
            sd.play(data, samplerate, blocking=False)
            return True, "Audio playback started successfully."
        except sf.LibsndfileError as e:
            print(f"Soundfile error playing audio: {e}")
            return False, f"Error: Failed to process audio data (Soundfile: {e}). Ensure ffmpeg is installed if needed."
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False, f"Error: Failed to play audio ({e.__class__.__name__})."

if __name__ == '__main__':
    # Example Usage (requires a running Voicevox engine)
    # test_url = "http://localhost:50021"
    # available, msg = VoicevoxService.is_engine_available(test_url)
    # print(f"Engine at {test_url} available: {available}, Message: {msg}")

    # if available:
    #     speakers, err = VoicevoxService.get_speakers(test_url)
    #     if err:
    #         print(err)
    #     elif speakers:
    #         print(f"Found {len(speakers)} speaker groups.")
    #         if speakers and speakers[0]['styles']:
    #             test_speaker_id = speakers[0]['styles'][0]['id']
    #             print(f"Using speaker ID: {test_speaker_id}")
                
    #             service = VoicevoxService(base_url=test_url, speaker_id=test_speaker_id)
    #             test_text = "こんにちは、これはテスト音声です。"
    #             query, q_err = service.generate_audio_query(test_text)
    #             if q_err: print(q_err)
    #             elif query:
    #                 print("Audio query generated.")
    #                 audio_data, s_err = service.synthesize_speech_data(query)
    #                 if s_err: print(s_err)
    #                 elif audio_data:
    #                     print("Audio synthesized.")
    #                     success, play_msg = service.play_audio_bytes(audio_data)
    #                     print(f"Playback success: {success}, Message: {play_msg}")
    #                     if success:
    #                         time.sleep(3) 
    #                         print("Playback likely finished.")
    #         else: print("No styles found for the first speaker or no speakers array.")
    #     else: print("No speakers found or error in speaker data format.")
    pass
