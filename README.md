# NEXUS AI — Multilingual Accessible Assistant (Hackathon Prototype)

A working prototype of the idea in your pitch deck: a Python + Streamlit chat
assistant that answers in the user's own language, in short plain sentences,
with accessibility options — built for people with disabilities, older
adults, regional-language speakers, and first-time digital users.

## How this maps to the pitch deck

| Deck slide | What it becomes in the code |
|---|---|
| Slide 7 (Tech stack) | Streamlit UI, `deep-translator` for translation, `gTTS`/`SpeechRecognition` for voice, OpenAI API for the LLM layer |
| Slide 8 (Program flow) | `main()` pipeline: detect language → translate → AI understands → simplify → translate back → accessible output |
| Slide 9 (Feasibility: EN/HI/KN) | `LANGUAGES` dict currently supports English, Hindi, Kannada — add more by adding one line |
| Slide 11 (Implementation approach) | `get_ai_response()` + `rule_based_response()` implement the "Aadhaar update" style step-by-step guidance example directly |
| Accessibility layer | Sidebar toggles: Large text, High-contrast, Voice output, Simple Mode |
| Feedback step | 👍 / 👎 buttons under every answer |

## Setup (5 minutes)

1. Install Python 3.9+ if you don't have it.
2. Open a terminal in this folder and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```
4. Your browser will open at `http://localhost:8501`.

## Using it without any API key (fully offline demo)

The app works out of the box with **no API key** — it uses a built-in
rule-based responder (`rule_based_response`) that gives real step-by-step
guidance for common asks like Aadhaar updates, filling online forms, and
education queries. This means your hackathon demo never breaks on stage
even without internet or a paid API key.

To turn on full generative AI answers, paste an OpenAI API key into the
sidebar field at runtime — nothing needs to change in the code.

## Try this demo script for judges

1. Set language to **Hindi**, type: `Mujhe Aadhaar update karna hai`
   → Shows translation + simplified step-by-step guidance in Hindi.
2. Toggle **Simple Mode** off/on to show the plain-language rewriting.
3. Toggle **High-contrast mode** and **Large text mode** to show accessibility.
4. Turn on **voice output** and replay the last answer as audio.
5. Click 👍/👎 to show the feedback loop mentioned in Slide 11.

## Notes on translation/voice quality

- `deep-translator` and `gTTS` call free Google-backed endpoints and need
  an internet connection. If offline, the app still runs — it just skips
  translation/audio and shows the English text (graceful degradation).
- Voice **input** currently accepts uploaded `.wav` files (simplest reliable
  path for a hackathon demo). Live microphone capture can be added later
  with `streamlit-webrtc` — listed under "Next steps" below.

## Next steps (matches Slide 10 — Scalability)

- Add more Indian languages by adding entries to the `LANGUAGES` dict.
- Swap the uploaded-file voice input for live mic capture (`streamlit-webrtc`).
- Add document upload + summarization (python-docx / PyPDF2) for the
  "document help" feature mentioned in the deck.
- Add a screen-reader-optimized layout pass for stronger accessibility.
