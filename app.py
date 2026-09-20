"""
NEXUS AI — A Multilingual Generative AI Assistant
for People with Disabilities and Low Digital Literacy

Hackathon prototype — Team NEXUS
Built with: Python + Streamlit + translation APIs + TTS/STT + LLM API

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os
import re
import io
import base64
import streamlit as st

# ---------------------------------------------------------------------------
# Optional third-party libraries.
# The app is built to DEGRADE GRACEFULLY: if a library or API key is missing,
# that feature is turned off automatically instead of crashing, so the demo
# always works even with partial setup.
# ---------------------------------------------------------------------------
try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

try:
    from langdetect import detect as detect_lang
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_LIB_AVAILABLE = True
except ImportError:
    OPENAI_LIB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Supported languages for the initial prototype (per the feasibility plan:
# English, Hindi, Kannada). deep_translator uses these ISO codes.
# ---------------------------------------------------------------------------
LANGUAGES = {
    "English": "en",
    "Hindi (हिन्दी)": "hi",
    "Kannada (ಕನ್ನಡ)": "kn",
}

JARGON_REPLACEMENTS = {
    "utilize": "use",
    "commence": "start",
    "terminate": "end",
    "prerequisite": "requirement",
    "facilitate": "help",
    "obtain": "get",
    "authenticate": "verify",
    "aforementioned": "this",
    "subsequently": "then",
    "in order to": "to",
}


# ---------------------------------------------------------------------------
# Core pipeline functions — mirrors the 6-step flow from the pitch deck:
# input -> detect/translate -> AI understanding -> simplify -> translate back
# -> accessible output (text/voice) -> feedback.
# ---------------------------------------------------------------------------

def detect_language_code(text: str) -> str:
    """Best-effort language detection; falls back to English."""
    if LANGDETECT_AVAILABLE:
        try:
            code = detect_lang(text)
            # langdetect uses 'hi', 'kn', 'en' too, so this lines up directly.
            if code in LANGUAGES.values():
                return code
        except Exception:
            pass
    return "en"


def translate_text(text: str, source: str, target: str) -> str:
    """Translate text between supported languages. No-op if same language
    or if the translation library/network isn't available."""
    if not text.strip() or source == target:
        return text
    if not TRANSLATION_AVAILABLE:
        return text
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except Exception:
        # Network/API issue during a live demo shouldn't break the app.
        return text


def simplify_text(text: str, simple_mode: bool) -> str:
    """Rule-based simplification: shorter sentences, plainer words.
    This is the 'Simple Mode' toggle described in the deck."""
    if not simple_mode:
        return text

    simplified = text
    for hard, easy in JARGON_REPLACEMENTS.items():
        simplified = re.sub(rf"\b{re.escape(hard)}\b", easy, simplified, flags=re.IGNORECASE)

    # Break up long sentences at commas/semicolons for shorter reading chunks.
    sentences = re.split(r"(?<=[.!?])\s+", simplified)
    short_sentences = []
    for s in sentences:
        if len(s.split()) > 22:
            parts = re.split(r",\s*", s)
            short_sentences.extend(p.strip().rstrip(",") + "." for p in parts if p.strip())
        else:
            short_sentences.append(s)
    return " ".join(short_sentences)


FALLBACK_RESPONSES = {
    "aadhaar": (
        "Here are simple steps to update your Aadhaar:\n"
        "1. Go to the UIDAI website or nearest Aadhaar Seva Kendra.\n"
        "2. Choose 'Update Aadhaar Details'.\n"
        "3. Enter your Aadhaar number and the detail you want to change.\n"
        "4. Upload or show the supporting document.\n"
        "5. Submit and note your Update Request Number (URN) to track status."
    ),
    "form": (
        "Here is simple guidance for filling an online form:\n"
        "1. Read each field name carefully before typing.\n"
        "2. Keep your ID documents ready before you start.\n"
        "3. Fill one section at a time; save your progress if possible.\n"
        "4. Double-check your name, date of birth, and phone number.\n"
        "5. Submit and take a screenshot or note the confirmation number."
    ),
    "education": (
        "Here is simple guidance for education-related help:\n"
        "1. Check the official school/college or scholarship website.\n"
        "2. Note the required documents and the last date to apply.\n"
        "3. Fill the form carefully, one step at a time.\n"
        "4. Ask a teacher, librarian, or helpline if any step is unclear.\n"
        "5. Keep a copy of everything you submit."
    ),
    "default": (
        "I can help you with simple, step-by-step guidance. "
        "Try asking about a government service, an online form, "
        "or an education-related question — for example: "
        "\"How do I update my Aadhaar?\""
    ),
}


def rule_based_response(query: str) -> str:
    """A safe, always-available fallback so the demo works with no API key."""
    q = query.lower()
    if "aadhaar" in q or "aadhar" in q:
        return FALLBACK_RESPONSES["aadhaar"]
    if "form" in q:
        return FALLBACK_RESPONSES["form"]
    if "school" in q or "college" in q or "scholarship" in q or "education" in q:
        return FALLBACK_RESPONSES["education"]
    return FALLBACK_RESPONSES["default"]


def get_ai_response(query_en: str, api_key: str) -> str:
    """Send the (English-translated) query to an LLM if a key is configured;
    otherwise use the rule-based fallback so the prototype always responds."""
    if api_key and OPENAI_LIB_AVAILABLE:
        try:
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are NEXUS AI, an assistant for people with disabilities, "
                            "older adults, and users with low digital literacy. "
                            "Always answer in short sentences, plain everyday words, "
                            "and clear numbered steps when guiding the user through a task. "
                            "Avoid technical jargon."
                        ),
                    },
                    {"role": "user", "content": query_en},
                ],
                max_tokens=350,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"(AI service unavailable, showing basic guidance instead — {e})\n\n" + rule_based_response(query_en)
    return rule_based_response(query_en)


def text_to_speech_bytes(text: str, lang_code: str):
    """Return mp3 audio bytes for the given text, or None if unavailable."""
    if not TTS_AVAILABLE or not text.strip():
        return None
    try:
        tts = gTTS(text=text, lang=lang_code if lang_code in ("en", "hi", "kn") else "en")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def speech_to_text(audio_bytes: bytes) -> str:
    """Transcribe an uploaded WAV audio file to text (English acoustic model)."""
    if not STT_AVAILABLE:
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def apply_accessibility_css(large_text: bool, high_contrast: bool):
    font_size = "20px" if large_text else "16px"
    css = f"""
    <style>
        html, body, [class*="css"] {{ font-size: {font_size} !important; }}
        .stButton>button {{ font-size: {font_size} !important; padding: 0.6em 1.2em; }}
    </style>
    """
    if high_contrast:
        css += """
        <style>
            body, .stApp { background-color: #000000 !important; color: #FFFF00 !important; }
            .stTextInput input, .stTextArea textarea { background-color: #000000 !important; color: #FFFF00 !important; border: 2px solid #FFFF00 !important; }
            .stButton>button { background-color: #FFFF00 !important; color: #000000 !important; border: 2px solid #FFFF00 !important; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="NEXUS AI — Multilingual Accessible Assistant", page_icon="🗣️", layout="centered")

    if "history" not in st.session_state:
        st.session_state.history = []
    if "feedback" not in st.session_state:
        st.session_state.feedback = {"up": 0, "down": 0}

    with st.sidebar:
        st.header("⚙️ Settings")
        language_label = st.selectbox("Preferred language / भाषा / ಭಾಷೆ", list(LANGUAGES.keys()))
        lang_code = LANGUAGES[language_label]

        st.subheader("Accessibility")
        large_text = st.checkbox("Large text mode", value=False)
        high_contrast = st.checkbox("High-contrast mode", value=False)
        voice_output = st.checkbox("Read answers aloud (voice output)", value=False, disabled=not TTS_AVAILABLE)
        if not TTS_AVAILABLE:
            st.caption("Install `gTTS` to enable voice output.")

        st.subheader("Response style")
        simple_mode = st.checkbox("Simple Mode (short, plain-language answers)", value=True)

        st.subheader("AI connection (optional)")
        api_key = st.text_input("OpenAI API key (leave blank to use offline demo mode)", type="password")
        st.caption("Without a key, NEXUS AI still answers using built-in guidance for common tasks.")

        st.divider()
        st.caption(f"👍 {st.session_state.feedback['up']}  ·  👎 {st.session_state.feedback['down']}")

    apply_accessibility_css(large_text, high_contrast)

    st.title("🗣️ NEXUS AI")
    st.caption("A multilingual generative AI assistant for people with disabilities and low digital literacy.")

    # ---- Input: text or voice ----
    st.subheader("Ask your question")
    tab_text, tab_voice = st.tabs(["⌨️ Type", "🎙️ Voice"])

    query = ""
    with tab_text:
        query = st.text_area("Type your question in any supported language", height=90,
                              placeholder="e.g. Mujhe Aadhaar update karna hai / How do I fill this form?")
        ask_clicked = st.button("Ask NEXUS AI", type="primary")

    with tab_voice:
        st.caption("Upload a short WAV recording of your question." if STT_AVAILABLE else
                   "Install `SpeechRecognition` and `PyAudio`/`pydub` to enable voice input.")
        audio_file = st.file_uploader("Upload audio (.wav)", type=["wav"], disabled=not STT_AVAILABLE)
        voice_ask_clicked = st.button("Transcribe & Ask", disabled=not STT_AVAILABLE)
        if voice_ask_clicked and audio_file is not None:
            transcribed = speech_to_text(audio_file.read())
            if transcribed:
                query = transcribed
                ask_clicked = True
                st.success(f"Heard: \"{transcribed}\"")
            else:
                st.error("Could not understand the audio. Please try typing instead.")

    # ---- Pipeline: detect -> translate -> AI -> simplify -> translate back ----
    if ask_clicked and query.strip():
        with st.spinner("Understanding your question..."):
            detected = detect_language_code(query)
            query_en = translate_text(query, source=detected, target="en") if detected != "en" else query

        with st.spinner("Finding a clear answer..."):
            answer_en = get_ai_response(query_en, api_key)
            answer_en = simplify_text(answer_en, simple_mode)

        with st.spinner("Translating your answer..."):
            answer_final = translate_text(answer_en, source="en", target=lang_code) if lang_code != "en" else answer_en

        st.session_state.history.append({"query": query, "answer": answer_final, "lang": lang_code})

    # ---- Conversation display ----
    st.subheader("Conversation")
    if not st.session_state.history:
        st.info("Your questions and answers will appear here.")

    for i, turn in enumerate(reversed(st.session_state.history)):
        idx = len(st.session_state.history) - i
        with st.chat_message("user"):
            st.write(turn["query"])
        with st.chat_message("assistant"):
            st.write(turn["answer"])
            if voice_output and TTS_AVAILABLE:
                audio_bytes = text_to_speech_bytes(turn["answer"], turn["lang"])
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
            col1, col2 = st.columns([1, 1])
            if col1.button("👍 Helpful", key=f"up_{idx}"):
                st.session_state.feedback["up"] += 1
                st.toast("Thanks for your feedback!")
            if col2.button("👎 Not helpful", key=f"down_{idx}"):
                st.session_state.feedback["down"] += 1
                st.toast("Thanks — we'll use this to improve.")

    st.divider()
    st.caption("NEXUS AI · Team NEXUS · Bharat Academics Hackathon 2026")


if __name__ == "__main__":
    main()
