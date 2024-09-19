import streamlit as st
import os
from dotenv import load_dotenv
import asyncio
import aiohttp
import re

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
    "google/gemini-pro",
    "google/gemma-2-27b-it",
    "google/gemini-flash-1.5",
    "mistralai/mistral-large",
    "mistralai/mistral-medium",
    "meta-llama/llama-3-70b-instruct",
    "meta-llama/llama-3-8b-instruct:free",
    "microsoft/wizardlm-2-8x22b",
    "cognitivecomputations/dolphin-mixtral-8x22b",
    "cognitivecomputations/dolphin-mixtral-8x7b",
    "qwen/qwen-72b-chat",
    "cohere/command-r-plus",
    "cohere/command-r",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

st.set_page_config(page_title="Prompt Editor", page_icon="📝", layout="wide")

with st.sidebar:
    st.title("Prompt Editor Settings")
    openrouter_api_key = st.text_input("Enter your OPENROUTER_API_KEY:", type="password")
    st.caption("If left empty, the app will use the API key from the .env file.")
    model_name = st.selectbox("Select a model:", SPECIFIED_MODELS, index=0)
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=1.0, step=0.1)

st.title(model_name)

async def call_openrouter_api(session, prompt, model, temperature, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",  # Replace with your actual URL
        "X-Title": "Streamlit OpenRouter App",
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    
    async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as response:
        if response.status == 200:
            data = await response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"Error: {response.status}"

async def get_responses_async(prompt, num_responses, model, temperature, api_key):
    async with aiohttp.ClientSession() as session:
        tasks = [call_openrouter_api(session, prompt, model, temperature, api_key) for _ in range(num_responses)]
        responses = await asyncio.gather(*tasks)
    return [replace_custom_latex_delimiters(response) for response in responses]

def get_responses(prompt, num_responses):
    api_key = openrouter_api_key if openrouter_api_key else os.environ.get("OPENROUTER_API_KEY")
    return asyncio.run(get_responses_async(prompt, num_responses, model_name, temperature, api_key))

if "responses" not in st.session_state:
    st.session_state.responses = []
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

st.markdown("### Prompt")
with st.form("prompt_form"):
    prompt = st.text_area("Enter your prompt:", value=st.session_state.prompt, height=100, key="prompt_input")
    num_responses = st.radio("Select number of responses", options=[1, 2, 3, 4], index=0, horizontal=True)
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        submitted = st.form_submit_button("Submit")
    with col2:
        reset = st.form_submit_button("Reset")

if reset:
    st.session_state.prompt = ""
    st.session_state.responses = []
    st.rerun()

if submitted:
    if not openrouter_api_key and not os.environ.get("OPENROUTER_API_KEY"):
        st.warning("Please enter your OPENROUTER API key!", icon="⚠")
    elif prompt.strip() != "":
        st.session_state.prompt = prompt
        with st.spinner("Generating responses..."):
            st.session_state.responses = get_responses(prompt, num_responses)
        st.rerun()

st.markdown("### Responses:")
if st.session_state.responses:
    tabs = st.tabs([f"Response {i+1}" for i in range(len(st.session_state.responses))])
    for i, (tab, response) in enumerate(zip(tabs, st.session_state.responses)):
        with tab:
            st.markdown(response)
