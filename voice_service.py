import requests
import json
import sounddevice as sd # Using sounddevice
import io
import time # For a small delay if needed for sounddevice buffer

class VoicevoxService:
    def __init__(self, base_url="http://localhost:50021", speaker_id=1):
        self.base_url = base_url
        self.speaker_id = int(speaker_id) # Ensure speaker_id is int

    def update_config(self, base_url, speaker_id):
        self.base_url = base_url
        self.speaker_id = int(speaker_id)
        print(f"VoicevoxService config updated: URL={self.base_url}, SpeakerID={self.speaker_id}")

    @classmethod
    def is_engine_available(cls, base_url="http://localhost:50021"):
        if not base_url:
            return False
        try:
            response = requests.get(f"{base_url}/version", timeout=2)
            response.raise_for_status()
            print(f"Voicevox engine found at {base_url}, version: {response.text}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Voicevox engine not available at {base_url}. Error: {e}")
            return False
        except Exception as e: # Catch any other unexpected error
            print(f"An unexpected error occurred while checking Voicevox engine: {e}")
            return False


    def get_speakers(self):
        if not self.base_url:
            print("Error: Voicevox base_url not configured.")
            return None
        try:
            response = requests.get(f"{self.base_url}/speakers", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting Voicevox speakers from {self.base_url}: {e}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON response from Voicevox speakers endpoint. Response: {response.text}")
            return None

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
        except requests.exceptions.Timeout:
            return None, "Error: Voicevox audio_query request timed out."
        except requests.exceptions.ConnectionError:
            return None, f"Error: Could not connect to Voicevox at {self.base_url} for audio_query."
        except requests.exceptions.HTTPError as e:
            return None, f"Error: Voicevox audio_query request failed. Status: {e.response.status_code}. Response: {e.response.text}"
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
            return response.content, None # Return raw audio bytes
        except requests.exceptions.Timeout:
            return None, "Error: Voicevox synthesis request timed out."
        except requests.exceptions.ConnectionError:
            return None, f"Error: Could not connect to Voicevox at {self.base_url} for synthesis."
        except requests.exceptions.HTTPError as e:
            return None, f"Error: Voicevox synthesis request failed. Status: {e.response.status_code}. Response: {e.response.text}"
        except requests.exceptions.RequestException as e:
            return None, f"Error: Voicevox synthesis request failed: {e}"

    def play_audio_bytes(self, audio_bytes):
        if not audio_bytes:
            return "Error: No audio data to play."
        try:
            # Voicevox typically returns WAV data.
            # We need to determine samplerate. Defaulting to 24000 for many Voicevox models.
            # This might need to be dynamic if speakers have different sample rates.
            # For now, assuming a common sample rate.
            # A more robust solution would be to parse WAV header or get it from Voicevox API if possible.
            samplerate = 24000 # Common for Voicevox, but might vary.
            
            # sd.play is non-blocking by default. sd.wait() makes it blocking.
            # For UI responsiveness, we want non-blocking or threaded playback.
            # If sd.play is truly non-blocking in the environment, direct call is fine.
            # Otherwise, threading might be needed if sd.wait() was used.
            
            # Convert bytes to a NumPy array suitable for sounddevice
            # Assuming 16-bit PCM audio, which is common for WAV.
            # This might need adjustment if audio format differs.
            
            # A simple way to play WAV bytes with sounddevice is to load it via something that understands WAV.
            # However, sounddevice itself can play raw numpy arrays.
            # Let's try to play directly if the format is known (e.g. 16-bit int mono)
            # If this causes issues, using a library like `soundfile` to read the BytesIO object is more robust.
            
            # Simple check: if it's typical WAV, it starts with "RIFF"
            if audio_bytes.startswith(b'RIFF'):
                try:
                    import soundfile as sf
                    data, samplerate = sf.read(io.BytesIO(audio_bytes))
                    sd.play(data, samplerate, blocking=False) # Non-blocking play
                    # sd.wait() # This would make it blocking
                    return "Audio playback started."
                except Exception as e: # Fallback or if soundfile not available
                    print(f"Could not use soundfile to play audio, error: {e}. Falling back or erroring.")
                    # Fallback: if you know the exact format (e.g., 16-bit mono at 24kHz)
                    # This part is highly dependent on Voicevox output format and might be fragile.
                    # For now, let's assume soundfile is the primary method for WAV.
                    # If soundfile is not present, this will be an issue.
                    # Consider adding soundfile as a dependency or more robust raw parsing.
                    return f"Error: Could not play audio with soundfile. Is it installed? Error: {e}"
            else:
                return "Error: Audio data does not appear to be standard WAV format (missing RIFF header)."

        except Exception as e:
            print(f"Error playing audio: {e}")
            return f"Error: Failed to play audio. {e}"

if __name__ == '__main__':
    # --- Example Usage ---
    # Make sure a Voicevox engine is running at http://localhost:50021
    
    VOICEVOX_BASE_URL = "http://localhost:50021" # Default for local Voicevox
    
    # 1. Check if engine is available
    print(f"Checking Voicevox engine at {VOICEVOX_BASE_URL}...")
    if not VoicevoxService.is_engine_available(VOICEVOX_BASE_URL):
        print("Voicevox engine is not running or not reachable. Exiting example.")
        exit()
    
    # Initialize service (assuming engine is available)
    vv_service = VoicevoxService(base_url=VOICEVOX_BASE_URL, speaker_id=1) # Use a valid speaker ID

    # 2. Get and print speakers (optional)
    print("\nFetching speakers...")
    speakers = vv_service.get_speakers()
    if speakers:
        print(f"Found {len(speakers)} speakers. First few:")
        for i, speaker in enumerate(speakers[:3]):
            print(f"  ID: {speaker['speaker_uuid']}, Name: {speaker['name']}")
            if speaker.get('styles'):
                 print(f"    Style ID: {speaker['styles'][0]['id']}, Style Name: {speaker['styles'][0]['name']}")
                 if i == 0: # Use first style of first speaker for testing
                    vv_service.update_config(VOICEVOX_BASE_URL, speaker['styles'][0]['id'])
                    print(f"Updated service to use speaker ID: {speaker['styles'][0]['id']}")
    else:
        print("Could not fetch speakers. Using default speaker ID 1.")
        vv_service.update_config(VOICEVOX_BASE_URL, 1)


    # 3. Generate audio for some text
    test_text_japanese = "こんにちは、これはテストです。"
    print(f"\nGenerating audio query for: '{test_text_japanese}' with speaker ID {vv_service.speaker_id}...")
    
    query_json, error = vv_service.generate_audio_query(test_text_japanese)
    if error:
        print(error)
        exit()
    if query_json:
        print("Audio query generated successfully.")
        # print("Query JSON:", json.dumps(query_json, indent=2, ensure_ascii=False))

        # 4. Synthesize speech data from the query
        print("\nSynthesizing speech data...")
        audio_data, error = vv_service.synthesize_speech_data(query_json)
        if error:
            print(error)
            exit()
        
        if audio_data:
            print(f"Speech data synthesized successfully (Size: {len(audio_data)} bytes).")

            # 5. Play the audio
            print("\nPlaying audio...")
            # Create a temporary file to test playback if direct playing is tricky
            # with open("test_audio.wav", "wb") as f:
            #     f.write(audio_data)
            # print("Saved to test_audio.wav")

            playback_status = vv_service.play_audio_bytes(audio_data)
            print(f"Playback status: {playback_status}")
            
            if "started" in playback_status.lower():
                print("Waiting for audio to finish (approx 5 seconds for this example)...")
                # Since play is non-blocking, we might need to wait in the script
                # In the app, this will be handled differently (UI remains responsive)
                time.sleep(5) # Crude wait for playback to finish in this example
                print("Playback likely finished.")
        else:
            print("Failed to synthesize speech data.")
    else:
        print("Failed to generate audio query.")

    # Test with unavailable engine (example)
    print("\nTesting with a non-existent engine (should fail gracefully):")
    vv_service_bad = VoicevoxService(base_url="http://localhost:50000", speaker_id=1)
    query_json_bad, error_bad = vv_service_bad.generate_audio_query("test")
    print(f"Error from bad service: {error_bad}")
    
    available_check = VoicevoxService.is_engine_available("http://localhost:50000")
    print(f"is_engine_available check for bad URL: {available_check}")
