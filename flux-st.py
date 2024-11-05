import streamlit as st
import os
from openai import OpenAI

def get_flux_image(api_key, prompt="A flying cat", model="black-forest-labs/FLUX.1-schnell-Free"):
    try:
        client = OpenAI(
            api_key=api_key, base_url="https://api.together.xyz/v1"
        )
        response = client.images.generate(
            prompt=prompt,
            model=model,
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return str(e)

def main():
    st.title("FLUX Image Generator")
    st.subheader("Prompt Refinement Exercise")
    
    # Initialize session state for storing prompts and images
    if 'prompts' not in st.session_state:
        st.session_state.prompts = []
    if 'images' not in st.session_state:
        st.session_state.images = []
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0

    # Input field for API key
    api_key = st.text_input("TogetherAI API Key", type="password")

    # Model selection dropdown
    models = [
        "black-forest-labs/FLUX.1-schnell-Free",
        "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1.1-pro",
        "black-forest-labs/FLUX.1-pro"
    ]
    selected_model = st.selectbox("Select Model", models)

    # Display all previous prompts and images
    for i in range(len(st.session_state.prompts)):
        st.markdown(f"### Step {i + 1}")
        st.text_area(
            f"Prompt {i + 1}",
            st.session_state.prompts[i],
            key=f"prompt_display_{i}",
            disabled=True
        )
        if st.session_state.images[i]:
            if "https://" in st.session_state.images[i]:
                st.image(st.session_state.images[i], caption=f"Generated Image {i + 1}")
            else:
                st.error(f"Error in step {i + 1}: {st.session_state.images[i]}")
        
        # Place "Start Over from Here" and "Regenerate" buttons on the same line
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Start Over from Here (Step {i + 1})", key=f"start_over_{i}"):
                # Truncate history and images from the selected point onwards
                st.session_state.prompts = st.session_state.prompts[:i + 1]
                st.session_state.images = st.session_state.images[:i + 1]
                st.session_state.current_step = i + 1
                st.rerun()
        with col2:
            if st.button(f"Regenerate Image (Step {i + 1})", key=f"regenerate_{i}"):
                if api_key:
                    with st.spinner(f"Regenerating image for Step {i + 1}..."):
                        image_url = get_flux_image(api_key, st.session_state.prompts[i], selected_model)
                        st.session_state.images[i] = image_url
                        st.rerun()
                else:
                    st.warning("Please enter your TogetherAI API key.")

    # Current prompt input
    st.markdown(f"### Step {st.session_state.current_step + 1}")
    
    # Pre-fill with previous prompt if it exists
    default_prompt = ""
    if st.session_state.prompts:
        default_prompt = st.session_state.prompts[-1]
    
    current_prompt = st.text_area(
        f"Prompt {st.session_state.current_step + 1}",
        value=default_prompt,
        key=f"current_prompt"
    )

    # Button to generate image
    if st.button("Generate Image"):
        if api_key:
            if current_prompt:
                with st.spinner("Generating image..."):
                    image_url = get_flux_image(api_key, current_prompt, selected_model)
                    
                    # Store the prompt and image
                    st.session_state.prompts.append(current_prompt)
                    st.session_state.images.append(image_url)
                    st.session_state.current_step += 1
                    
                    # Rerun to update the display
                    st.rerun()
            else:
                st.warning("Please enter a prompt.")
        else:
            st.warning("Please enter your TogetherAI API key.")

    # Reset button
    if st.button("Start Over"):
        st.session_state.prompts = []
        st.session_state.images = []
        st.session_state.current_step = 0
        st.rerun()

if __name__ == "__main__":
    main()
