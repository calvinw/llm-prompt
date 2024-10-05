import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('OPENROUTER_API_KEY')

# OpenRouter API endpoint
url = "https://openrouter.ai/api/v1/chat/completions"

# Headers for the API request
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Request body
data = {
    "model": "openai/gpt-3.5-turbo",  # You can change this to any supported model
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

# Make the API call
response = requests.post(url, headers=headers, json=data)

# Check if the request was successful
if response.status_code == 200:
    # Get the response content
    content = response.json()
    print("Response:", content['choices'][0]['message']['content'])

    # Get the cost info from the header
    cost_info_str = response.headers.get('x-openrouter-cost-info')

    if cost_info_str:
        # Parse the JSON string
        cost_info = json.loads(cost_info_str)
        
        # Access and print the cost details
        prompt_tokens = cost_info.get('prompt_tokens')
        completion_tokens = cost_info.get('completion_tokens')
        total_cost = cost_info.get('total_cost')
        
        print(f"\nCost Information:")
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Completion tokens: {completion_tokens}")
        print(f"Total cost: ${total_cost}")
    else:
        print("\nCost information not available in the response headers.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
