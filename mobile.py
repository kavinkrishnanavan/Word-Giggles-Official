import streamlit as st
from PIL import Image
from openai import OpenAI
import requests
import re
import base64

# ---------------- Page Setup ----------------
im = Image.open("logo.png")
st.set_page_config(
    page_title="Word Giggles",
    page_icon=im,
    layout="centered"
)

logo_bytes = open("logo.png", "rb").read()
logo_base64 = base64. b64encode(logo_bytes).decode()

# ---------------- Initialize Groq Client ----------------
try:
    client = OpenAI(
        api_key=st.secrets["GROQ"],
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    st.error(f"Error initializing AI Client: {e}")

# ---------------- GIPHY Function ----------------
def fetch_gif(word):
    if word == "N/A":
        return None

    GIPHY_API_KEY = st.secrets.get("GIPHY", "YOUR_GIPHY_API_KEY")
    if GIPHY_API_KEY == "YOUR_GIPHY_API_KEY":
        return None

    try:
        params = {
            "api_key": GIPHY_API_KEY,
            "q": word,
            "limit": 1,
            "rating": "g"
        }
        r = requests.get("https://api.giphy.com/v1/gifs/search", params=params)
        r.raise_for_status()
        data = r.json()
        if data["data"]:
            return data["data"][0]["images"]["downsized_medium"]["url"]
    except Exception:
        return None

    return None

# ---------------- Response Parser ----------------
def parse_and_format_response(text):
    joke_match = re.search(r"Joke:\s*(.*)", text, re.DOTALL)
    word_match = re.search(r"New Word:\s*(.*)", text)
    meaning_match = re.search(r"Meaning:\s*(.*)", text)


    if not joke_match:
        return text, "N/A", "N/A"

    joke_raw = joke_match.group(1).strip()
    sentences = [s.strip() for s in re.split(r'([.!?])\s*', joke_raw) if s.strip()]

    formatted = ""
    for i in range(0, len(sentences), 2):
        formatted += sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "") + "\n"

    return (
        formatted.strip(),
        word_match.group(1).strip() if word_match else "N/A",
        meaning_match.group(1).strip() if meaning_match else "N/A"
    )

# ---------------- Styling ----------------
st.markdown("""
<style>
.logo {
    border-radius: 15px;
    transition: transform 0.3s ease;
}
.logo:hover {
    transform: scale(1.05);
}
.center {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown(
    f"""
    <div class="center">
        <img src="data:image/png;base64,{logo_base64}" class="logo" width="200">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<div style="text-align:center;">
    <h1 style="margin-bottom:0.2rem;">Word Giggles 🔤 🤭</h1>
    <p style="margin-top:0; font-size:1.05rem;">
        Enter a word and we will generate a funny and catchy joke for children to easily remember the word!
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------- Input ----------------
st.text_input(
    "Enter a word",
    placeholder="e.g., Enormous",
    label_visibility="collapsed",
    key="word_input",
    on_change=lambda: generate_joke()
)

st.button("Make", on_click=lambda: generate_joke())

st.markdown("---")

# ---------------- Output Container ----------------
output_container = st.container()

# ---------------- Joke Generator ----------------
def generate_joke():
    word = st.session_state.get("word_input", "").strip()

    if not word:
        with output_container:
            st.warning("Please enter a word.")
        return

    prompt = f"""You are a creative children's joke writer.
Create one simple, short, and funny joke that helps children learn a new English word.

Requirements:
Use easy vocabulary suitable for children
The joke must be short, catchy, and memorable
Clearly highlight or repeat the new English word in a natural way
Keep the humor friendly and age-appropriate
Meaning in one simple sentence
No asterisks (*) in the answer allowed
The word is {word}.
Block any bad or inappropriate words immediately
No parentheses allowed
Please follow the instructions exactly
Output format:

New Word: {word}

Meaning:

Joke:"""

    with output_container:
        with st.spinner(f"Creating a joke for **{word}**..."):
            try:
                response = client.responses.create(
                    model="openai/gpt-oss-120b",
                    input=prompt
                )
                text = response.output_text
                joke, new_word, meaning = parse_and_format_response(text)
            except Exception as e:
                st.error(f"AI Error: {e}")
                return

        if new_word == "N/A":
            st.error("Inappropriate or invalid response detected.")
            return

        st.subheader(f"✨ Word: {new_word.capitalize()}")
        st.markdown(f"**Meaning:** {meaning}")
        st.markdown("---")
        st.markdown("**Your Learning Joke:**")
        st.markdown(f"```text\n{joke}  ```")

        gif_url = fetch_gif(new_word)
        if gif_url:
            st.markdown(
                f"""
                <img src="{gif_url}" style="
                    width:100%;
                    max-width:400px;
                    height:250px;
                    object-fit:cover;
                    border-radius:12px;
                    display:block;
                    margin:auto;
                ">
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("No GIF found for this word.")
