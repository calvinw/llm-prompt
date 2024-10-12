import streamlit as st
import os
from dotenv import load_dotenv
import re
import requests

# Load environment variables
load_dotenv()

def replace_custom_latex_delimiters(text):
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    return text

SPECIFIED_MODELS = [
    "openai/gpt-4o-mini",  # Default model
    "openai/gpt-4o",
    "openai/gpt-3.5-turbo",
    "openai/gpt-4-turbo",
    "anthropic/claude-3-haiku",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    "mistralai/mistral-large",
    "mistralai/mistral-medium",
    "meta-llama/llama-3-70b-instruct",
    "meta-llama/llama-3-8b-instruct:free",
    "microsoft/wizardlm-2-8x22b",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]

def get_model_pricing(model_info):
    pricing = model_info.get('pricing', {})
    prompt_price = float(pricing.get('prompt', 0)) * 1000  # Convert to price per 1000 tokens
    completion_price = float(pricing.get('completion', 0)) * 1000  # Convert to price per 1000 tokens
    return prompt_price, completion_price

@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def get_models_data(api_key):
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",  # Replace with your actual URL
        "X-Title": "Streamlit OpenRouter App",
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch models data: {response.status_code}")
        return None

st.set_page_config(page_title="Chat with AI", page_icon="💬", layout="wide")

with st.sidebar:
    st.title("Chat Settings")
    openrouter_api_key = st.text_input("Enter your OPENROUTER_API_KEY:", type="password")
    st.caption("If left empty, the app will use the API key from the .env file.")

# Use the API key from user input or environment variable
api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.warning("Please enter your OPENROUTER API key in the sidebar or set it in your .env file.", icon="⚠️")
    st.stop()

# Use the function to get models data
models_data = get_models_data(api_key)

if models_data:
    models_dict = {model['id']: model for model in models_data['data']}
    all_model_options = [model['id'] for model in models_data['data']]
    model_options = [model for model in SPECIFIED_MODELS if model in all_model_options] + [model for model in all_model_options if model not in SPECIFIED_MODELS]
    model_options.append("Custom (type your own)")
else:
    models_dict = {}
    model_options = ["Custom (type your own)"]

with st.sidebar:
    model_selection = st.selectbox("Select a model:", model_options, index=0)
    
    if model_selection == "Custom (type your own)":
        model_name = st.text_input("Enter custom model name:")
    else:
        model_name = model_selection
    
    # Temperature slider
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    
    if model_name in models_dict:
        prompt_price, completion_price = get_model_pricing(models_dict[model_name])
        st.markdown(f"""
        <div style='font-size: 18px; font-weight: bold;'>
        Pricing: ${prompt_price:.4f}/${completion_price:.4f} per 1k tokens
        </div>
        """, unsafe_allow_html=True)
    
    if model_name in models_dict:
        st.markdown("### Model Description")
        model_description = models_dict[model_name].get('description', 'No description available.')
        st.write(model_description)

st.title(f"Chat with {model_name}")

# System prompt input
system_prompt = st.text_area("System Prompt (optional):", height=30)

# Add message display toggle
display_mode = st.radio("Messages Display", ["Markdown", "Text"], horizontal=True)

def call_openrouter_api(messages, model, temperature, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",  # Replace with your actual URL
        "X-Title": "Streamlit OpenRouter App",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {})
        return content, usage
    else:
        return f"Error: {response.status_code}", None

def calculate_cost(usage, model_id):
    model = models_dict.get(model_id)
    if not model:
        return None, None

    prompt_tokens = usage['prompt_tokens']
    completion_tokens = usage['completion_tokens']
    
    prompt_cost = float(model['pricing']['prompt']) * prompt_tokens
    completion_cost = float(model['pricing']['completion']) * completion_tokens
    
    return prompt_cost, completion_cost

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if display_mode == "Markdown":
            st.markdown(replace_custom_latex_delimiters(message["content"]))
        else:
            st.text(message["content"])

# Accept user input
if prompt := st.chat_input("What is your message?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        if display_mode == "Markdown":
            st.markdown(prompt)
        else:
            st.text(prompt)
    
    # Prepare messages for API call
    api_messages = []
    if system_prompt:
        api_messages.append({"role": "system", "content": system_prompt})
    api_messages.extend(st.session_state.messages)
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("Thinking..."):
            assistant_response, usage = call_openrouter_api(api_messages, model_name, temperature, api_key)
            full_response = assistant_response
            if display_mode == "Markdown":
                message_placeholder.markdown(replace_custom_latex_delimiters(full_response))
            else:
                message_placeholder.text(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Display usage and cost information
    if usage:
        prompt_cost, completion_cost = calculate_cost(usage, model_name)
        if prompt_cost is not None and completion_cost is not None:
            total_cost = prompt_cost + completion_cost
            total_tokens = usage['prompt_tokens'] + usage['completion_tokens']
            st.caption(f"**Cost**: ${total_cost:.6f}, **Tokens**: {total_tokens}")
        else:
            st.caption(f"Error: Model {model_name} not found in models.json")
    else:
        st.caption("Usage information not available")

# Add a button to clear the chat history
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()
