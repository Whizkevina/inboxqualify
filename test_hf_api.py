import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"API Key present: {bool(api_key)}")
print(f"API Key prefix: {api_key[:10] if api_key else 'None'}...")

# Test different models
models = [
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "distilbert-base-uncased-finetuned-sst-2-english",
    "nlptown/bert-base-multilingual-uncased-sentiment"
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

for model in models:
    print(f"\n--- Testing {model} ---")
    try:
        url = f"https://api-inference.huggingface.co/models/{model}"
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": "This is a test message"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text[:200]}")
        else:
            print("Success!")
            result = response.json()
            print(f"Result: {result}")
            break
    except Exception as e:
        print(f"Exception: {e}")
