
import os
import time
import logging

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors

# ======================================
# 1. APPLICATION CONFIGURATION
# ======================================

load_dotenv()

st.set_page_config(
    page_title="Chandu-Nexora AI",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Chandu-Nexora AI")
st.caption("Your personal AI assistant")

# ======================================
# 2. GEMINI API KEY
# ======================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except (FileNotFoundError, KeyError):
        api_key = None

if not api_key:
    st.error(
        "Gemini API key is missing. "
        "Set GEMINI_API_KEY in your .env file "
        "or Streamlit Cloud Secrets."
    )
    st.stop()

# ======================================
# 3. GEMINI CLIENT
# ======================================

client = genai.Client(api_key=api_key)

# Can be changed if your API key supports
# a different Gemini model.
MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

SYSTEM_INSTRUCTIONS = """
You are Chandu-Nexora, a friendly and
helpful AI assistant created by Chandu Guthula.

Help users with:
- Artificial Intelligence
- Machine Learning
- Python programming
- Education and studying
- Coding and debugging
- Writing and general knowledge
- Everyday questions

Answer clearly and naturally.

Remember previous messages within the
current chat session.

If you do not know something, be honest.
"""

# ======================================
# 4. CHAT HISTORY
# ======================================

if "messages" not in st.session_state:
    st.session_state.messages = []

# ======================================
# 5. SIDEBAR
# ======================================

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

# ======================================
# 6. DISPLAY EXISTING MESSAGES
# ======================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ======================================
# 7. BUILD GEMINI CHAT HISTORY
# ======================================

def build_history(messages):
    history = []

    for message in messages:
        role = (
            "user"
            if message["role"] == "user"
            else "model"
        )

        content = message["content"]

        if history and history[-1]["role"] == role:
            history[-1]["parts"][0]["text"] += (
                "\n" + content
            )
        else:
            history.append({
                "role": role,
                "parts": [
                    {"text": content}
                ]
            })

    return history

# ======================================
# 8. GENERATE AI RESPONSE
# ======================================

def generate_response(prompt, history):
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            chat = client.chats.create(
                model=MODEL_NAME,
                history=history,
                config={
                    "system_instruction":
                        SYSTEM_INSTRUCTIONS
                }
            )

            # Only one API request per attempt
            response = chat.send_message(prompt)

            answer = response.text

            if not answer:
                raise ValueError(
                    "Empty response from Gemini"
                )

            return answer, True

        except errors.APIError as e:
            logging.warning(
                "Gemini API error: %s",
                e.code
            )

            # Retry temporary server failures
            if e.code in (500, 502, 503, 504):
                if attempt < max_attempts - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)
                    continue

                return (
                    "⚠️ Gemini is currently busy. "
                    "Please try again shortly.",
                    False
                )

            if e.code == 429:
                return (
                    "⚠️ API rate limit reached. "
                    "Please try again later.",
                    False
                )

            if e.code in (400, 404):
                return (
                    "⚠️ Gemini request or model "
                    "configuration error. "
                    "Please check the model name.",
                    False
                )

            if e.code in (401, 403):
                return (
                    "⚠️ API authentication or "
                    "permission error. "
                    "Please check your API key.",
                    False
                )

            return (
                "Sorry, the AI service is "
                "unavailable right now.",
                False
            )

        except Exception:
            logging.exception(
                "Unexpected Nexora error"
            )

            return (
                "Sorry, something went wrong. "
                "Please try again.",
                False
            )

    return (
        "Unable to generate a response.",
        False
    )

# ======================================
# 9. USER CHAT INPUT
# ======================================

prompt = st.chat_input(
    "Message Chandu-Nexora..."
)

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    # History contains only successful
    # user-assistant conversations.
    history = build_history(
        st.session_state.messages
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, success = generate_response(
                prompt,
                history
            )

        st.markdown(answer)

    # Save messages only after a
    # successful AI response.
    if success:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

# ======================================
# END OF NEXORA AI APPLICATION
# ======================================
