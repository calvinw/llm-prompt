import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("OPENROUTER_API_KEY")

# If API key is not set, prompt the user
if not api_key:
    api_key = input("Please enter your OpenRouter API key: ")

# API endpoint
url = "https://openrouter.ai/api/v1/chat/completions"

# Headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:8000",  # Replace with your actual URL
    "X-Title": "OpenRouter API Test Script",
}

# Get number of choices from user
num_choices = int(input("Enter the number of choices you want (1-5): "))
num_choices = max(1, min(num_choices, 5))  # Ensure the number is between 1 and 5

# Sample payload
payload = {
    "model": "openai/gpt-3.5-turbo",  # You can change this to any supported model
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a short joke."}
    ],
    "n": num_choices,  # Request multiple choices
    "temperature": 0.7  # Add some randomness to get varied responses
}

def print_formatted_json(obj):
    print(json.dumps(obj, indent=2))

# Make the API call
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an exception for bad status codes
    
    print("Full Response Body:")
    print_formatted_json(response.json())
    
    # Print individual choices
    choices = response.json().get('choices', [])
    for i, choice in enumerate(choices, 1):
        print(f"\nChoice {i}:")
        print_formatted_json(choice)
    
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print("Error Response Body:")
        print_formatted_json(e.response.json())
