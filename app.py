import streamlit as st
import os
from langchain_openai import ChatOpenAI
#from dotenv import load_dotenv
import re

#load_dotenv()

def replace_custom_latex_delimiters(text):
    # Replace custom inline LaTeX delimiters \( ... \) with $
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    
    # Replace custom display-style LaTeX delimiters \[ ... \] with $$
    # Adjusting to handle potential newlines within the delimiters
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    
    return text

# Define the list of specified models
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

# app config
st.set_page_config(page_title="Prompt Editor", page_icon="📝", layout="wide")

# Sidebar for API key input and model selection
with st.sidebar:
    st.title("Prompt Editor Settings")
    
    openrouter_api_key = st.text_input("Enter your OPENROUTER_API_KEY:", type="password")
    st.caption("If left empty, the app will use the API key from the .env file.")
    
    # Add dropdown for model selection with default set to gpt-4o-mini
    model_name = st.selectbox("Select a model:", SPECIFIED_MODELS, index=0)

# Main content area
st.title(model_name)

def get_response(prompt):
    # Use the user-provided API key if available, otherwise use the one from .env
    api_key = openrouter_api_key if openrouter_api_key else os.environ.get("OPENROUTER_API_KEY")

    llm = ChatOpenAI(model_name=model_name,
                     openai_api_key=api_key,
                     openai_api_base="https://openrouter.ai/api/v1")
    
    response = llm.invoke(prompt)
    
    return replace_custom_latex_delimiters(response.content)

# Initialize session state for the response and prompt
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
    st.session_state.prompt = ""  # Only clear the prompt in session state
    st.rerun()  # Rerun to update the text area

if submitted:
    if not openrouter_api_key and not os.environ.get("OPENROUTER_API_KEY"):
        st.warning("Please enter your OPENROUTER API key!", icon="⚠")
    elif prompt.strip() != "":
        st.session_state.prompt = prompt  # Update the prompt in session state
        st.session_state.response = get_response(prompt)
        st.rerun()  # Rerun the app to reflect the changes

# Display the response
st.markdown("### Response:")
if st.session_state.response:
    st.markdown(st.session_state.response)
