import streamlit as st
from PIL import Image
from openai import OpenAI
import requests
import re 

im = Image.open("logo.png")
st.set_page_config(
    page_title="Word Giggles",
    page_icon=im,
    layout="wide",
)
try:
    # Initialize the client for Groq API using OpenAI SDK interface
    # Ensure you have st.secrets["GROQ"] configured with your Groq API key
    client = OpenAI(
        api_key=st.secrets["GROQ"],
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    # Display an error if the client fails to initialize (e.g., missing API key)
    st.error(f"Error initializing AI Client. Make sure the 'GROQ' API key is set correctly in secrets. Error: {e}")
    # st.stop() 

# --- GIPHY Function (No change, keeping for completeness) ---

def fetch_gif(word):
    """Fetches a single GIF URL from GIPHY based on the search word."""
    # Ensure you have st.secrets["GIPHY"] configured with your GIPHY API key
    GIPHY_API_KEY = st.secrets.get("GIPHY", "YOUR_GIPHY_API_KEY") 
    GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
    
    if GIPHY_API_KEY == "YOUR_GIPHY_API_KEY":
        return None

    try:
        params = {
            "api_key": GIPHY_API_KEY,
            "q": word,
            "limit": 1,
            "rating": "g"
        }
        
        response = requests.get(GIPHY_SEARCH_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        
        if data["data"]:
            return data["data"][0]["images"]["downsized_medium"]["url"]
        else:
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Error making GIPHY API request: {e}")
        return None
    except KeyError:
        st.error("Error parsing the GIF data from the API response.")
        return None
    except Exception:
        return None 

# --- Response Parsing Function (No change, keeping for completeness) ---

def parse_and_format_response(full_response_text):
    """
    Parses the full AI response to extract the word, meaning, and formats the joke 
    to have each sentence on a new line.
    """
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
            
        return formatted_joke.strip(), \
               word_match.group(1).strip() if word_match else "N/A", \
               meaning_match.group(1).strip() if meaning_match else "N/A"
    
    return full_response_text, "N/A", "N/A"

# --- Streamlit UI ---

st.set_page_config(layout="wide")
st.title("🔤 Word  🤭 Giggles")

st.markdown("Enter a word and it will generate a funny, educational joke for children to easily remember the word!")

# Use st.container to group the input elements
input_container = st.container()

# 1. Get the word input and the button in a single, narrow row/column group
with input_container:
    # Use two columns for the input area: narrow for the word, even narrower for the button
    col_input, col_button, col_spacer = st.columns([3, 1, 6]) 
    
    with col_input:
        # 1. Get the word input
        word_input = st.text_input("Enter a word:", label_visibility="collapsed", placeholder="e.g., Enormous")
    
    with col_button:
        # 2. Define the button
        # The key is necessary to prevent Streamlit from thinking the button is being clicked
        # on every rerun if it's placed immediately after an input widget.
        generate_button = st.button("Generate", key="generate_joke_button") 
    
    # The third column (col_spacer) simply fills the remaining space

# --- Output Logic ---
# The rest of the logic only executes when the button is clicked
if generate_button:
    
    if not word_input:
        st.warning("Please enter a word before generating the joke.")
    else:
        # Create the prompt string
        query = f"""You are a creative children's joke writer.
Create one simple, short, and funny joke that helps children learn a new English word.

Requirements:
Use easy vocabulary suitable for children
The joke must be short, catchy, and memorable
Clearly highlight or repeat the new English word in a natural way
Keep the humor friendly and age-appropriate
Meaning in one simple sentence
No asterisks (*) in the answer allowed
Please follow the instructions exactly
The word is {word_input}.
Block any bad words immediately

Output format:

New Word: {word_input}

Meaning:

Joke:"""
        
        # Output columns for the results
        st.write("---")
        
        col_joke_output, col_gif_output = st.columns([2, 1]) # Joke (2) : GIF (1) ratio

        with st.spinner(f"Generating a joke for **{word_input}**..."):
            try:
                # 3. Call the AI API (using the Groq client)
                response = client.responses.create(
                    input=query,
                    model="openai/gpt-oss-120b"
                )

                full_output = response.output_text
                
                # Parse the response and format the joke
                formatted_joke, new_word, meaning = parse_and_format_response(full_output)
                
                # Fetch GIF URL
                gif_url = fetch_gif(new_word)

                # --- 4. Display the response using the Output Columns ---
                
                with col_joke_output:
                    st.subheader(f"✨ Word: {new_word.capitalize().replace('*','')}")
                    st.markdown(f"**Meaning:**  {meaning.replace('*','')}")
                    st.markdown("---")
                    st.markdown("**Your Learning Joke:**")
                    # Display the joke using st.markdown with fenced code block (no copy button)
                    st.markdown(
                        f"""
```text
{formatted_joke.replace('*','')}
"""
                )

                with col_gif_output:
                    if gif_url:
                        st.markdown("<br><br>", unsafe_allow_html=True) # Add vertical space
                        st.markdown("**GIF to help you remember!**")
                        # Use st.image to display the GIF directly from the URL
                        st.image(gif_url)
                    else:
                        st.info(f"Sorry, no GIF found for '{new_word}'.")

            except Exception as e:
                # Handle API errors gracefully

                st.error(f"An error occurred during AI generation! Error: {e}")











