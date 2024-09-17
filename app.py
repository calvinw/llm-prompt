import streamlit as st
import os
from langchain_openai import ChatOpenAI
import re

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
    
    # Add temperature slider
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=1.0, step=0.1)

st.title(model_name)

def get_response(prompt):
    api_key = openrouter_api_key if openrouter_api_key else os.environ.get("OPENROUTER_API_KEY")
    llm = ChatOpenAI(
        model_name=model_name,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature  # Use the temperature value from the slider
    )
    
    response = llm.invoke(prompt)
    return replace_custom_latex_delimiters(response.content)

if "response" not in st.session_state:
    st.session_state.response = ""
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

st.markdown("### Prompt")
with st.form("prompt_form"):
    prompt = st.text_area("Enter your prompt:", value=st.session_state.prompt, height=200, key="prompt_input")
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        submitted = st.form_submit_button("Submit")
    with col2:
        reset = st.form_submit_button("Reset")

if reset:
    st.session_state.prompt = ""
    st.rerun()

if submitted:
    if not openrouter_api_key and not os.environ.get("OPENROUTER_API_KEY"):
        st.warning("Please enter your OPENROUTER API key!", icon="⚠")
    elif prompt.strip() != "":
        st.session_state.prompt = prompt
        st.session_state.response = get_response(prompt)
        st.rerun()

st.markdown("### Response:")
if st.session_state.response:
    st.markdown(st.session_state.response)
