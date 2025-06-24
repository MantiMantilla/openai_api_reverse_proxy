# openai_api_reverse_proxy
An AWS Lambda based OpenAI API reverse proxy that supports response streaming with accompanying test scripts.

To run the tests:
```bash
export LAMBDA_FUNCTION_URL="https://xxxxxxxxxx.lambda-url.eu-west-1.on.aws/"
export REVERSE_PROXY_API_KEY="your_secret_api_key_for_proxy"
python test_proxy.py
```

```
$env:LAMBDA_FUNCTION_URL="https://xxxxxxxxxx.lambda-url.eu-west-1.on.aws/"
$env:REVERSE_PROXY_API_KEY="your_secret_api_key_for_proxy"
python test_proxy.py
```
