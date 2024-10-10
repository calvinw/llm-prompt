import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    st.title("Chat with an LLM")
    
    # Sidebar for OpenRouter API key and model selection
    st.sidebar.header("API Settings")
    api_key = st.sidebar.text_input("Enter your OpenRouter API Key:", type="password")
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
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "Custom (type your own)"  # Add this option at the end
    ]

    model = st.sidebar.selectbox("Select Model:", SPECIFIED_MODELS, index=0, key="model_select")

    # Handle custom model input
    custom_model = ""
    if model == "Custom (type your own)":
        custom_model = st.sidebar.text_input("Enter Custom Model Name:")
        model = custom_model

    # Input for optional system prompt
    system_prompt = st.text_area("Enter System Prompt (optional):", "You are a helpful assistant.")

    # Get API key from .env if available
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")

    # Chat UI
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display previous chat messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # User input
    if api_key:
        user_input = st.chat_input("You:")
        if user_input:
            # Append user message
            st.session_state["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Set headers for OpenRouter API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # Define the request payload
            messages = [{"role": "system", "content": system_prompt}] + st.session_state["messages"]
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 150
            }

            try:
                # Call the OpenRouter API
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                bot_response = data['choices'][0]['message']['content'].strip()

                # Append LLM response
                st.session_state["messages"].append({"role": "assistant", "content": bot_response})
                with st.chat_message("assistant"):
                    st.write(bot_response)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter your OpenRouter API key in the sidebar or ensure it is set in the .env file.")

if __name__ == "__main__":
    main()
