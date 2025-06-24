import requests
import json

# Replace with your actual OpenAI API key
OPENAI_API_KEY = ''
# Or, even better, load from environment variable:
# import os
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}',
}

data = {
    'model': 'gpt-3.5-turbo',  # Or 'gpt-4o', 'gpt-4', etc.
    'messages': [
        {'role': 'user', 'content': 'Hello, how are you today?'}
    ]
}

try:
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    print(response.json()['choices'][0]['message']['content'])
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response content: {e.response.text}")
