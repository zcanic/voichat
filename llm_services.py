import requests
import json

class LLMService:
    def __init__(self, api_base_url, api_key, model, temperature, system_prompt):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

    def is_configured(self):
        """Checks if the essential API base URL and API key are configured."""
        return bool(self.api_base_url and self.api_key)

    def generate_response(self, user_message):
        if not self.is_configured(): # Use the helper method
            return "Error: LLM service not configured. Missing API Base URL or API Key."

        # Common path for OpenAI-compatible APIs
        # Users might provide "http://localhost:1234/v1" or just "http://localhost:1234"
        # This attempts to standardize to .../v1/chat/completions
        endpoint = self.api_base_url
        if not endpoint.endswith("/"):
            endpoint += "/"
        if not endpoint.endswith("v1/"):
            # If it's a base URL like http://host:port/, append v1/
            # If it's http://host:port/custom_path/, this might be an issue,
            # but OpenAI standard is /v1/
            if "v1" not in endpoint.split('/')[-2]: # check if "v1" is not in the last path segment
                 endpoint += "v1/"
        
        if not endpoint.endswith("chat/completions"):
             endpoint += "chat/completions"


        payload = {
            "model": self.model,
            "temperature": float(self.temperature), # Ensure temperature is float
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
            response_json = response.json()
            
            if 'choices' in response_json and response_json['choices']:
                message = response_json['choices'][0].get('message', {})
                content = message.get('content')
                if content:
                    return content.strip()
                else:
                    return "Error: No content in LLM response message."
            else: # Fallback for non-OpenAI or older completion APIs
                return f"Error: Unexpected LLM response structure. Full response: {json.dumps(response_json, indent=2)}"

        except requests.exceptions.Timeout:
            return "Error: LLM request timed out."
        except requests.exceptions.ConnectionError:
            return f"Error: Could not connect to LLM service at {endpoint}. Check API Base URL and network."
        except requests.exceptions.HTTPError as e:
            return f"Error: LLM API request failed. Status: {e.response.status_code}. Response: {e.response.text}"
        except requests.exceptions.RequestException as e:
            return f"Error: An unexpected error occurred with the LLM request: {e}"
        except json.JSONDecodeError:
            return f"Error: Could not decode LLM API response (not valid JSON). Response: {response.text}"
        except KeyError: # If expected keys like 'choices' are missing
            return f"Error: Unexpected structure in LLM response JSON. Response: {json.dumps(response_json, indent=2)}"
        except Exception as e: # Catch-all for other unexpected errors
            return f"An unexpected error occurred: {str(e)}"

if __name__ == '__main__':
    # Example Usage - replace with your actual API details if you have a local server
    # Ensure your local server (e.g., LM Studio, Ollama with OpenAI compatibility) is running
    # api_base_url_test = "http://localhost:1234/v1" # Common for LM Studio
    # api_key_test = "test" # Or your actual key, or "ollama" for Ollama if no key needed
    # model_test = "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF" # Example model name
    
    # print(f"Testing LLMService with base URL: {api_base_url_test}, model: {model_test}")
    # service = LLMService(api_base_url_test, api_key_test, model_test, 0.7, "You are a test assistant.")
    # response_text = service.generate_response("Hello, world!")
    # print(f"LLM Response: {response_text}")

    # Test missing config
    # service_unconfigured = LLMService("", "", "test", 0.7, "test")
    # print(service_unconfigured.generate_response("This should fail."))
    pass # Keep __main__ minimal for restoration
