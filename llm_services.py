import requests
import json

class LLMService:
    def __init__(self, api_base_url, api_key, model, temperature, system_prompt):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

    def generate_response(self, user_message):
        if not self.api_base_url or not self.api_key:
            return "Error: LLM service not configured. Missing API Base URL or API Key."

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
            # Construct the full URL if api_base_url doesn't end with /v1/chat/completions or similar
            # This is a common pattern for self-hosted or proxy endpoints.
            # Adjust if your API expects a different endpoint structure.
            endpoint = self.api_base_url
            if not endpoint.endswith(("/v1/chat/completions", "/v1/completions")): # Common OpenAI-like endpoints
                 # Heuristic: if it's just a base, append the typical chat completions path.
                 # This might need to be more flexible depending on actual API structures.
                if endpoint.endswith("/"):
                    endpoint += "v1/chat/completions"
                else:
                    endpoint += "/v1/chat/completions"


            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)

            response_json = response.json()
            
            # Standard OpenAI response structure
            if 'choices' in response_json and response_json['choices']:
                message = response_json['choices'][0].get('message', {})
                content = message.get('content')
                if content:
                    return content
                else:
                    return "Error: No content in LLM response message."
            # Fallback for some non-OpenAI or older completion APIs (less common for chat)
            elif 'text' in response_json: # e.g. some completion endpoints
                 return response_json['text']
            else:
                return f"Error: Unexpected LLM response structure. Response: {json.dumps(response_json, indent=2)}"

        except requests.exceptions.Timeout:
            return "Error: LLM request timed out."
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to LLM service. Check API Base URL and network."
        except requests.exceptions.HTTPError as e:
            return f"Error: LLM API request failed. Status Code: {e.response.status_code}. Response: {e.response.text}"
        except requests.exceptions.RequestException as e:
            return f"Error: An unexpected error occurred with the LLM request: {e}"
        except json.JSONDecodeError:
            return f"Error: Could not decode LLM API response (not valid JSON). Response: {response.text}"
        except KeyError:
            return f"Error: Unexpected structure in LLM response JSON. Could not find 'choices[0].message.content'. Response: {json.dumps(response_json, indent=2)}"
        except Exception as e: # Catch-all for other unexpected errors
            return f"An unexpected error occurred: {str(e)}"

if __name__ == '__main__':
    # Example Usage (requires a running compatible LLM API endpoint)
    # Replace with your actual API details and a running server for testing
    # Ensure the API base URL is correct (e.g., http://localhost:1234/v1 for LM Studio)
    
    # Mock an API key and base URL for local testing if you don't have a live one
    # For a real test, you'd use actual credentials.
    # This example will likely fail without a running server.
    
    api_base_url = "http://localhost:1234/v1" # Common for LM Studio, Ollama (sometimes needs /api/chat)
    # api_base_url = "YOUR_API_BASE_URL" 
    api_key = "sk-your-actual-api-key" # or "ollama" if using ollama without a key
    model = "gpt-3.5-turbo" # or your local model name e.g. "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"
    temperature = 0.7
    system_prompt = "You are a helpful AI assistant."

    llm_service = LLMService(api_base_url, api_key, model, temperature, system_prompt)

    print(f"Attempting to connect to: {api_base_url} with model {model}")
    
    # Test 1: Valid request (will fail if server not running or wrong config)
    user_message_1 = "Hello, how are you?"
    print(f"\nUser: {user_message_1}")
    response_1 = llm_service.generate_response(user_message_1)
    print(f"LLM: {response_1}")

    # Test 2: Service not configured (empty API key)
    llm_service_unconfigured = LLMService(api_base_url, "", model, temperature, system_prompt)
    user_message_2 = "This should fail."
    print(f"\nUser (unconfigured): {user_message_2}")
    response_2 = llm_service_unconfigured.generate_response(user_message_2)
    print(f"LLM (unconfigured): {response_2}")

    # Test 3: Potentially bad endpoint (example)
    llm_service_bad_endpoint = LLMService("http://localhost:1234/bad_endpoint", api_key, model, temperature, system_prompt)
    user_message_3 = "Testing bad endpoint."
    print(f"\nUser (bad endpoint): {user_message_3}")
    response_3 = llm_service_bad_endpoint.generate_response(user_message_3)
    print(f"LLM (bad endpoint): {response_3}")
    
    # Test 4: No base URL
    llm_service_no_url = LLMService("", api_key, model, temperature, system_prompt)
    print(f"\nUser (no URL): {user_message_3}")
    response_4 = llm_service_no_url.generate_response(user_message_3)
    print(f"LLM (no URL): {response_4}")
