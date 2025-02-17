import streamlit as st
import os
from dotenv import load_dotenv
import asyncio
import aiohttp
import re
import json

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
    "openai/o1-mini",
    "openai/o1",
    "openai/o3-mini",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-chat:free",
    "deepseek/deepseek-r1:free",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.0-flash-001",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.0-flash-thinking-exp:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "google/gemini-2.0-pro-exp-02-05:free",
]

def get_model_pricing(model_info):
    pricing = model_info.get('pricing', {})
    prompt_price = float(pricing.get('prompt', 0)) * 1000  # Convert to price per 1000 tokens
    completion_price = float(pricing.get('completion', 0)) * 1000  # Convert to price per 1000 tokens
    return prompt_price, completion_price

async def fetch_models_data_async(api_key):
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",  # Replace with your actual URL
        "X-Title": "Streamlit OpenRouter App",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                st.error(f"Failed to fetch models data: {response.status}")
                return None

@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def get_models_data(api_key):
    return asyncio.run(fetch_models_data_async(api_key))

st.set_page_config(page_title="Prompt Editor", page_icon="📝", layout="wide")

with st.sidebar:
    st.title("Prompt Editor Settings")
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
    # Create a dictionary for quick model lookup
    models_dict = {model['id']: model for model in models_data['data']}
    
    # Create a list of all model names from the API
    all_model_options = [model['id'] for model in models_data['data']]
    
    # Create the final model_options list
    model_options = []
    
    # Add specified models that exist in the API data
    for model in SPECIFIED_MODELS:
        if model in all_model_options:
            model_options.append(model)
    
    # Add remaining models from the API data
    for model in all_model_options:
        if model not in SPECIFIED_MODELS:
            model_options.append(model)
    
    # Add the custom option at the end
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
    
    # Display pricing information
    if model_name in models_dict:
        prompt_price, completion_price = get_model_pricing(models_dict[model_name])
        st.markdown("""
        <div style='font-size: 18px; font-weight: bold;'>
        Pricing: ${:.4f}/${:.4f} per 1k tokens
        </div>
        """.format(prompt_price, completion_price), unsafe_allow_html=True)
    
    # Display model description in sidebar
    if model_name in models_dict:
        model_description = models_dict[model_name].get('description', 'No description available.')
        st.markdown("### Model Description")
        st.write(model_description)
    
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=1.0, step=0.1)

# Display only the model name as the main title
st.markdown(f"# `{model_name}`")

# Replace the part where you load models data from the file
async def call_openrouter_api(session, system_prompt, prompt, model, temperature, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",  # Replace with your actual URL
        "X-Title": "Streamlit OpenRouter App",
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as response:
        if response.status == 200:
            data = await response.json()
            content = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            return content, usage
        else:
            return f"Error: {response.status}", None

def calculate_cost(usage, model_id):
    model = models_dict.get(model_id)
    if not model:
        return None, None

    prompt_tokens = usage['prompt_tokens']
    completion_tokens = usage['completion_tokens']
    
    prompt_cost = float(model['pricing']['prompt']) * prompt_tokens
    completion_cost = float(model['pricing']['completion']) * completion_tokens
    
    return prompt_cost, completion_cost

async def get_responses_async(system_prompt, prompt, num_responses, model, temperature, api_key):
    async with aiohttp.ClientSession() as session:
        tasks = [call_openrouter_api(session, system_prompt, prompt, model, temperature, api_key) for _ in range(num_responses)]
        results = await asyncio.gather(*tasks)
    return [(replace_custom_latex_delimiters(content), usage) for content, usage in results]

def get_responses(system_prompt, prompt, num_responses):
    api_key = openrouter_api_key if openrouter_api_key else os.environ.get("OPENROUTER_API_KEY")
    return asyncio.run(get_responses_async(system_prompt, prompt, num_responses, model_name, temperature, api_key))

if "responses" not in st.session_state:
    st.session_state.responses = []
if "prompt" not in st.session_state:
    st.session_state.prompt = ""
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""

st.markdown("### Prompt")
with st.form("prompt_form"):
    system_prompt = st.text_area("System Prompt (optional):", value=st.session_state.system_prompt, height=50, key="system_prompt_input")
    prompt = st.text_area("User Prompt:", value=st.session_state.prompt, height=200, key="prompt_input")
    num_responses = st.radio("Select number of responses", options=[1, 2, 3, 4], index=0, horizontal=True)
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        submitted = st.form_submit_button("Submit")
    with col2:
        reset = st.form_submit_button("Reset")

if reset:
    st.session_state.prompt = ""
    st.session_state.system_prompt = ""
    st.session_state.responses = []
    st.rerun()

if submitted:
    if not openrouter_api_key and not os.environ.get("OPENROUTER_API_KEY"):
        st.warning("Please enter your OPENROUTER API key!", icon="⚠")
    elif prompt.strip() != "":
        st.session_state.prompt = prompt
        st.session_state.system_prompt = system_prompt
        with st.spinner("Generating responses..."):
            st.session_state.responses = get_responses(system_prompt, prompt, num_responses)
        st.rerun()

st.markdown("### Responses:")
if st.session_state.responses:
    tabs = st.tabs([f"Response {i+1}" for i in range(len(st.session_state.responses))])
    for i, (tab, (response, usage)) in enumerate(zip(tabs, st.session_state.responses)):
        with tab:
            st.markdown(response)
            if usage:
                prompt_cost, completion_cost = calculate_cost(usage, model_name)
                if prompt_cost is not None and completion_cost is not None:
                    total_cost = prompt_cost + completion_cost
                    total_tokens = usage['prompt_tokens'] + usage['completion_tokens']
                    st.markdown(f"**Cost**: ${total_cost:.6f}, **Tokens**: {total_tokens}")
                else:
                    st.markdown(f"Error: Model {model_name} not found in models.json")
            else:
                st.markdown("Usage information not available")
