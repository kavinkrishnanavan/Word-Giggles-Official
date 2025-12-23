import streamlit as st
from PIL import Image
from openai import OpenAI
import requests
import re
import base64

# ================== SESSION STATE ==================
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# ================== PAGE SETUP ==================
im = Image.open("logo.png")
st.set_page_config(
    page_title="Word Giggles",
    page_icon=im,
    layout="centered"
)

logo_bytes = open("logo.png", "rb").read()
logo_base64 = base64.b64encode(logo_bytes).decode()

# ================== INIT GROQ CLIENT ==================
client = OpenAI(
    api_key=st.secrets["GROQ"],
    base_url="https://api.groq.com/openai/v1"
)

# ================== GIPHY ==================
def fetch_gif(word):
    key = st.secrets.get("GIPHY")
    if not key:
        return None

    try:
        r = requests.get(
            "https://api.giphy.com/v1/gifs/search",
            params={
                "api_key": key,
                "q": word,
                "limit": 1,
                "rating": "g"
            },
            timeout=5
        )
        r.raise_for_status()
        data = r.json()
        if data["data"]:
            return data["data"][0]["images"]["downsized_medium"]["url"]
    except Exception:
        return None

    return None

# ================== PARSER ==================
def parse_and_format_response(text):
    joke = re.search(r"Joke:\s*(.*)", text, re.DOTALL)
    word = re.search(r"New Word:\s*(.*)", text)
    meaning = re.search(r"Meaning:\s*(.*)", text)

    if not joke or not word or not meaning:
        return None, None, None

    parts = [s for s in re.split(r'([.!?])', joke.group(1)) if s.strip()]
    formatted = ""
    for i in range(0, len(parts), 2):
        formatted += parts[i] + (parts[i + 1] if i + 1 < len(parts) else "") + "\n"

    return formatted.strip(), word.group(1).strip(), meaning.group(1).strip()

# ================== STYLES ==================
st.markdown("""
<style>
.logo {
    border-radius: 15px;
}
.center {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ================== HEADER ==================
st.markdown(
    f"""
    <div class="center">
        <img src="data:image/png;base64,{logo_base64}" width="200">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<div style="text-align:center;">
    <h1>Word Giggles 🔤 🤭</h1>
    <p>Enter a word and get a funny learning joke!</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ================== OUTPUT CONTAINER (FIXED POSITION) ==================
output_container = st.container()

# ================== GENERATOR ==================
def generate_joke(source=None):
    if st.session_state.is_generating:
        return

    word = st.session_state.get("word_input", "").strip()
    if not word:
        return

    st.session_state.is_generating = True

    prompt = f"""You are a creative children's joke writer.

New Word: {word}

Meaning:

Joke:"""

    with output_container:
        st.empty()

        with st.spinner(f"Creating a joke for **{word}**..."):
            try:
                response = client.responses.create(
                    model="openai/gpt-oss-120b",
                    input=prompt
                )
            except Exception as e:
                st.error(f"AI Error: {e}")
                st.session_state.is_generating = False
                return

        joke, new_word, meaning = parse_and_format_response(response.output_text)

        if not new_word:
            st.error("Invalid response from AI.")
            st.session_state.is_generating = False
            return

        st.subheader(f"✨ Word: {new_word.capitalize()}")
        st.markdown(f"**Meaning:** {meaning}")
        st.markdown("**Your Learning Joke:**")
        st.markdown(f"```text\n{joke}")

        gif = fetch_gif(new_word)
        if gif:
            st.markdown(
                f"""
                <img src="{gif}" style="
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

    st.session_state.is_generating = False

# ================== INPUT AREA (ALWAYS TOP) ==================
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.text_input(
        "Enter a word",
        placeholder="e.g., Enormous",
        label_visibility="collapsed",
        key="word_input",
        on_change=lambda: generate_joke("enter")
    )

    st.button(
        "Make",
        use_container_width=True,
        on_click=lambda: generate_joke("button")
    )

st.markdown("---")
