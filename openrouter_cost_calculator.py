import argparse
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load models data
with open('models.json', 'r') as f:
    models_data = json.load(f)['data']

# Create a dictionary for quick model lookup
models_dict = {model['id']: model for model in models_data}

def call_openrouter_api(prompt, model, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "OpenRouter Cost Calculator",
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        usage = data['usage']
        content = data['choices'][0]['message']['content']
        return usage, content
    else:
        return None, f"Error: {response.status_code}"

def calculate_cost(usage, model_id):
    model = models_dict.get(model_id)
    if not model:
        return None, None

    prompt_tokens = usage['prompt_tokens']
    completion_tokens = usage['completion_tokens']
    
    prompt_cost = float(model['pricing']['prompt']) * prompt_tokens
    completion_cost = float(model['pricing']['completion']) * completion_tokens
    
    return prompt_cost, completion_cost

def main():
    parser = argparse.ArgumentParser(description="Calculate OpenRouter API call cost")
    parser.add_argument("prompt", help="The prompt to send to the API")
    parser.add_argument("model", help="The model ID to use")
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Please set the OPENROUTER_API_KEY environment variable")
        return

    usage, content = call_openrouter_api(args.prompt, args.model, api_key)
    
    if usage:
        prompt_cost, completion_cost = calculate_cost(usage, args.model)
        if prompt_cost is not None and completion_cost is not None:
            total_cost = prompt_cost + completion_cost
            
            # Print the response content first
            print(f"{content}\n")
            
            # Print token counts and costs on two lines
            print(f"Tokens: prompt: {usage['prompt_tokens']}, completion: {usage['completion_tokens']}")
            print(f"Cost: total: ${total_cost:.6f}, prompt: ${prompt_cost:.6f}, completion: ${completion_cost:.6f}")
        else:
            print(f"Error: Model {args.model} not found in models.json")
    else:
        print(content)  # This will be the error message

if __name__ == "__main__":
    main()