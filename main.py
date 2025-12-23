import streamlit as st
from PIL import Image
from openai import OpenAI
import requests
import re
import base64

# --- Page setup ---
im = Image.open("logo.png")
st.set_page_config(
    page_title="Word Giggles",
    page_icon=im,
    layout="wide",
)
logo_bytes = open("logo.png", "rb").read()
logo_base64 = base64.b64encode(logo_bytes).decode()

# --- Initialize Groq API Client ---
try:
    client = OpenAI(
        api_key=st.secrets["GROQ"],
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    st.error(f"Error initializing AI Client. Make sure the 'GROQ' API key is set correctly in secrets. Error: {e}")

# --- GIPHY Function ---
def fetch_gif(word):
    if word == "N/A":
        return None
    GIPHY_API_KEY = st.secrets.get("GIPHY", "YOUR_GIPHY_API_KEY") 
    GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
    if GIPHY_API_KEY == "YOUR_GIPHY_API_KEY":
        return None
    try:
        params = {"api_key": GIPHY_API_KEY, "q": word, "limit": 1, "rating": "g"}
        response = requests.get(GIPHY_SEARCH_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        if data["data"]:
            return data["data"][0]["images"]["downsized_medium"]["url"]
        return None
    except Exception:
        return None 

# --- Response Parsing Function ---
def parse_and_format_response(full_response_text):
    joke_match = re.search(r"Joke:\s*(.*)", full_response_text, re.DOTALL)
    word_match = re.search(r"New Word:\s*(.*)", full_response_text)
    meaning_match = re.search(r"Meaning:\s*(.*)", full_response_text)
    if joke_match:
        joke_raw = joke_match.group(1).strip()
        sentences = [s.strip() for s in re.split(r'([.!?])\s*', joke_raw) if s.strip()]
        formatted_joke = ""
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i+1] if i + 1 < len(sentences) else ""
            formatted_joke += f"{sentence}{punctuation}\n"
        return (
            formatted_joke.strip(),
            word_match.group(1).strip() if word_match else "N/A",
            meaning_match.group(1).strip() if meaning_match else "N/A"
        )
    return full_response_text, "N/A", "N/A"

# --- Streamlit UI ---

logo, title = st.columns([1,10])
with logo:
    st.markdown("""
<style>
.header-logo {
    border-radius: 15px;
    
    transition: transform 0.3s ease;
}
.header-logo:hover {
    transform: scale(1.05);
}

</style>
""", unsafe_allow_html=True)
    st.markdown(f"""
<div class="main-header">
    <img src="data:image/png;base64,{logo_base64}" class="header-logo" width="120" height="120">
</div>
""", unsafe_allow_html=True)

with title:
    st.markdown("<br>" ,unsafe_allow_html=True)
    st.title("Word Giggles 🔤 🤭")
st.markdown("Enter a word and we will generate a funny and catchy joke for children to easily remember the word!")

# --- Input container (always fixed at top) ---
input_container = st.container()
with input_container:
    col_input, col_button, col_spacer = st.columns([4, 1, 2])
    with col_input:
        one,two = st.columns([4,1])
        with one:
            
            st.text_input(
                "Enter a word:", 
                label_visibility="collapsed", 
                placeholder="e.g., Enormous", 
                key="word_input", 
                on_change=lambda: generate_joke()  # Enter key triggers generation
            )
        with two:
            
            st.button("Make", key="generate_joke_button", on_click=lambda: generate_joke())


# --- Output container (reserved below input) ---
output_container = st.container()

# --- Function to generate the joke ---
def generate_joke():
    word_input = st.session_state.get("word_input", "").strip()
    if not word_input:
        with output_container:
            st.warning("Please enter a word before generating the joke.")
        return
    
    query = f"""You are a creative children's joke writer.
Create one simple, short, and funny joke that helps children learn a new English word.

Requirements:
Use easy vocabulary suitable for children
The joke must be short, catchy, and memorable
Clearly highlight or repeat the new English word in a natural way
Keep the humor friendly and age-appropriate
Meaning in one simple sentence
No asterisks (*) in the answer allowed
The word is {word_input}.
Block any bad or inappropriate words immediately
No parentheses allowed
Please follow the instructions exactly
Output format:

New Word: {word_input}

Meaning:

Joke:"""



    with output_container:
        # Display results
        if new_word == "N/A":
            st.error("The use of profane or inappropriate language is strictly prohibited.")
        else:
            
            with col_input:
                st.subheader(f"✨ Word: {new_word.capitalize().replace('*','')}")
                st.markdown(f"**Meaning:** {meaning.replace('*','')}")
                st.markdown("---")
                st.markdown("**Your Learning Joke:**")
                st.markdown(f"```text\n{formatted_joke.replace('*','')}")
            with col_spacer:
                gif_url = fetch_gif(new_word)
                if gif_url:
                    
                    st.markdown(
                        f"""
                        <img src="{gif_url}" style="
                            width:100%;
                            height:250px;
                            object-fit:cover;
                            border-radius:10px;
                        ">
                        """,
                        unsafe_allow_html=True
                    )
                    
                else:
                    st.info(f"Sorry, no GIF found for '{new_word}'.")
            def spinnercalling():
                with st.spinner(f"Generating a joke for **{word_input}**..."):
                    try:
                        response = client.responses.create(
                            input=query,
                            model="openai/gpt-oss-120b"
                        )
                        full_output = response.output_text
                        formatted_joke, new_word, meaning = parse_and_format_response(full_output)
                    except Exception as e:
                        st.error(f"An error occurred during AI generation! Error: {e}")
                        return
            spinnercalling()





