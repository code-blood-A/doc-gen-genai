import requests
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class OllamaClient:
    def __init__(self):
        self.api_url = config.OLLAMA_URL
        self.model = config.OLLAMA_MODEL

    def generate(self, prompt, max_new_tokens=500, temperature=0.7):
        """
        Sends a prompt to the local Ollama instance and returns the generated text.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_new_tokens,
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to Ollama at {self.api_url}. Is the Ollama server running?")
            return None
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            return None

if __name__ == "__main__":
    # Simple test
    client = OllamaClient()
    test_prompt = "Hello, tell me a short joke about Java."
    print("Testing Ollama Client...")
    print(client.generate(test_prompt))
