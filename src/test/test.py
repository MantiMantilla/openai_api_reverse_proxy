import requests
import json
import os

# --- Configuration ---
# Get your Lambda Function URL from AWS Console (e.g., https://xxxxxxxxxx.lambda-url.eu-west-1.on.aws/)
LAMBDA_FUNCTION_URL = os.environ.get("LAMBDA_FUNCTION_URL", "YOUR_LAMBDA_FUNCTION_URL_HERE") + "/chat/completions"
# Get your reverse proxy API key (the one you set as REVERSE_PROXY_API_KEY in Lambda environment variables)
REVERSE_PROXY_API_KEY = os.environ.get("REVERSE_PROXY_API_KEY", "YOUR_REVERSE_PROXY_API_KEY_HERE")
OPENAI_API_KEY = REVERSE_PROXY_API_KEY

# --- OpenAI Chat Completions Request Body (adjust as needed) ---
# This mimics a request to OpenAI's chat completions endpoint.
# The 'stream: true' is crucial for testing the streaming behavior of your proxy.
OPENAI_REQUEST_BODY = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a short story about a brave knight and a wise dragon."},
    ],
    # "max_tokens": 150,
    "temperature": 0.7,
    "stream": True  # This is the key for streaming responses
}

# --- Headers for your reverse proxy ---
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "X-API-Key": REVERSE_PROXY_API_KEY,
    "Accept": "text/event-stream" # Important for SSE streams
}

def test_reverse_proxy_streaming():
    print(f"Sending request to Lambda Function URL: {LAMBDA_FUNCTION_URL}")
    print(f"Using API Key: {'*' * (len(REVERSE_PROXY_API_KEY) - 4) + REVERSE_PROXY_API_KEY[-4:] if REVERSE_PROXY_API_KEY else 'N/A'}")
    print(f"Request body: {json.dumps(OPENAI_REQUEST_BODY, indent=2)}")

    try:
        # Use stream=True to tell requests to not download the entire response at once
        with requests.post(LAMBDA_FUNCTION_URL, headers=HEADERS, json=OPENAI_REQUEST_BODY, stream=True) as response:
            print(f"\nReceived status code: {response.status_code}")
            print("Received headers:")
            for header, value in response.headers.items():
                print(f"  {header}: {value}")

            # Check for non-200 status codes first
            if response.status_code != 200:
                try:
                    error_content = response.text
                    print(f"\nError response content:\n{error_content}")
                except Exception as e:
                    print(f"\nCould not read error response content: {e}")
                response.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)

            print("\n--- Streaming Response ---")
            # Iterate over the response content in chunks
            # response.iter_content(chunk_size=None) will iterate over raw bytes as they arrive
            # For SSE (Server-Sent Events) from OpenAI, iter_lines() is often more suitable
            # as it handles line-by-line parsing.
            total_output_text = ""
            for line in response.iter_lines():
                if line:  # Filter out keep-alive new lines
                    decoded_line = line.decode('utf-8')
                    # print(f"Chunk received: {decoded_line}")
                    # If the response is truly SSE, you might parse it like this:
                    if decoded_line.startswith('data:'):
                        try:
                            json_data = json.loads(decoded_line[5:].strip())
                            # Process the JSON data here
                            print(f"Parsed JSON: {json.dumps(json_data, indent=2)}")
                            total_output_text += json_data["choices"][0]["delta"].get("content", "")
                        except json.JSONDecodeError:
                            print(f"Non-JSON data line: {decoded_line}")

            print("\n--- Streaming Complete ---")
            
            print("\n--- Total Output ---")
            print(total_output_text)

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during the request: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    # You can set these environment variables before running the script, e.g.:
    # export LAMBDA_FUNCTION_URL="https://xxxxxxxxxx.lambda-url.eu-west-1.on.aws/"
    # export REVERSE_PROXY_API_KEY="your_secret_api_key_for_proxy"
    # python your_script_name.py

    # Or uncomment and set them directly here for quick testing (NOT recommended for production secrets)
    # LAMBDA_FUNCTION_URL = "https://xxxxxxxxxx.lambda-url.eu-west-1.on.aws/"
    # REVERSE_PROXY_API_KEY = "your_secret_api_key_for_proxy"

    if "YOUR_LAMBDA_FUNCTION_URL_HERE" in LAMBDA_FUNCTION_URL or "YOUR_REVERSE_PROXY_API_KEY_HERE" in REVERSE_PROXY_API_KEY:
        print("WARNING: Please update LAMBDA_FUNCTION_URL and REVERSE_PROXY_API_KEY in the script or via environment variables.")
        print("Exiting.")
    else:
        test_reverse_proxy_streaming()
