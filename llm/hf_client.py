from huggingface_hub import InferenceClient
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class HFClient:
    def __init__(self):
        # The InferenceClient handles the URL and headers automatically
        self.client = InferenceClient(
            model=config.HF_INFERENCE_URL.split("/models/")[-1],
            token=config.HF_TOKEN
        )

    def generate(self, prompt, max_new_tokens=2048, temperature=0.7):
        """
        Sends a prompt to the HF Inference API using the Chat interface.
        """
        try:
            # Using chat_completion because most modern providers prefer the 'conversational' task
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_new_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling HF API via chat_completion: {e}")
            return None

if __name__ == "__main__":
    # Simple test
    client = HFClient()
    test_prompt = "Generate a Javadoc for a Java method named 'calculateSum' that takes two integers and returns their sum."
    print("Testing HF Client...")
    print(client.generate(test_prompt))
