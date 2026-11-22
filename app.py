import os
import logging
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Load local environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(
    page_title="Chandu-Nexora AI",
    page_icon="🤖",
    layout="centered"
)

# Page heading
st.title("🤖 Chandu-Nexora AI")
st.caption("Your personal AI assistant")

# Gemini API configuration
# Works with local .env and Streamlit Cloud secrets
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except (FileNotFoundError, KeyError):
        api_key = None

if not api_key:
    st.error(
        "GEMINI_API_KEY is missing. "
        "Configure it in your local .env file "
        "or Streamlit Cloud Secrets."
    )
    st.stop()

# Initialize Gemini client
from google.genai import types

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=3,
            initial_delay=1,
            max_delay=8,
            exp_base=2,
            http_status_codes=[429, 500, 502, 503, 504],
        )
    ),
)

# Use only one Gemini model
MODEL_NAME = "gemini-3.5-flash-lite"

SYSTEM_INSTRUCTIONS = """
You are Chandu-Nexora, a helpful, friendly,
intelligent AI assistant.

Answer questions clearly and naturally.

Help users with:
- Education and studying
- Python programming
- Coding and debugging
- Artificial Intelligence
- General knowledge
- Writing and creative ideas
- Everyday questions

Use conversation history to answer follow-up questions.

If you do not know an answer, be honest.
"""

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Powered by Google Gemini")

    if st.button(
        "🗑️ New Chat",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Developed by Chandu Guthula")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
prompt = st.chat_input("Message Chandu-Nexora...")

if prompt:
    # Display and save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Build previous conversation history
                history = []

                for msg in st.session_state.messages[:-1]:
                    role = (
                        "user"
                        if msg["role"] == "user"
                        else "model"
                    )

                    # Merge consecutive messages of same role
                    if (
                        history
                        and history[-1]["role"] == role
                    ):
                        history[-1]["parts"][0]["text"] += (
                            "\n" + msg["content"]
                        )
                    else:
                        history.append({
                            "role": role,
                            "parts": [
                                {"text": msg["content"]}
                            ]
                        })

                # Create ONE Gemini chat session
                chat = client.chats.create(
                    model=MODEL_NAME,
                    history=history,
                    config={
                        "system_instruction": SYSTEM_INSTRUCTIONS
                    }
                )

                # Send ONE API request
                response = chat.send_message(prompt)

                # Get response
                answer = (
                    response.text
                    or "Sorry, I couldn't generate a response."
                )

            
            except errors.APIError as e:
                logging.warning(
                    "Gemini API failed with status %s",
                    e.code
                )

                if e.code == 503:
                    answer = (
                        "⚠️ Gemini server is busy. "
                        "Please try again shortly."
                    )
                elif e.code == 429:
                    answer = (
                        "⚠️ API rate limit reached. "
                        "Please try again later."
                    )
                else:
                    answer = (
                        "Sorry, the AI service is unavailable. "
                        "Please try again."
                    )

            except Exception:
                logging.exception("Unexpected chatbot error")
                answer = (
                    "Something went wrong. "
                    "Please try again."
                )


            # Display response
            st.markdown(answer)

    # Save assistant message
    # Do not include failed responses in Gemini history
    if answer.startswith("Sorry, something went wrong."):
        st.session_state.messages.pop()
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })
