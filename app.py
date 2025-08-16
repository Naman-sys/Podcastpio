import streamlit as st
import json
import uuid
from datetime import datetime
import google.generativeai as genai

# ==============================
# CONFIG
# ==============================
APP_TITLE = "🎙️ PodcastAI"
APP_SUBTITLE = "Transform Any Article into a Professional Podcast Script"
API_KEY = "YOUR_GEMINI_API_KEY_HERE"   # <--- 🔑 Replace with your key

# ==============================
# DATA CLASSES
# ==============================
class EpisodeDetails:
    def __init__(self, duration, category, format):
        self.duration = duration
        self.category = category
        self.format = format

class ShowNotes:
    def __init__(self, key_topics, resources, timestamps, episode_details):
        self.key_topics = key_topics
        self.resources = resources
        self.timestamps = timestamps
        self.episode_details = episode_details

class GeneratedScript:
    def __init__(self, intro, main_content, outro, show_notes):
        self.intro = intro
        self.main_content = main_content
        self.outro = outro
        self.show_notes = show_notes

# ==============================
# HELPER FUNCTIONS
# ==============================
def check_gemini_status():
    """Check if Gemini API is online and key works"""
    try:
        genai.configure(api_key=API_KEY)
        _ = genai.GenerativeModel("gemini-1.5-pro")
        return True
    except Exception:
        return False

def build_llm_prompt(content: str, style: str, duration: str, show_name: str) -> str:
    return f"""
You are a professional podcast scriptwriter. Write a FULL, engaging script.

Requirements:
- Style: {style}
- Target duration: {duration} minutes
- Show name: {show_name}
- Intro: 2–3 engaging paragraphs with music cues.
- Main Content: 4–6 paragraphs with examples, explanations, and natural flow.
- Outro: 2 paragraphs with a clear wrap-up and call-to-action.
- Show Notes: At least 5 key topics, 3 resources, and detailed timestamps.

Content to base on (summarize, explain, and expand where needed):
\"\"\"{content[:8000]}\"\"\"

Return ONLY JSON in this structure (no prose outside JSON):
{{
  "intro": "...",
  "main_content": "...",
  "outro": "...",
  "show_notes": {{
    "key_topics": ["topic1", "topic2"],
    "resources": ["res1", "res2"],
    "timestamps": [{{"time": "0:00", "topic": "Intro"}}],
    "episode_details": {{
      "duration": "~{duration} minutes",
      "category": "Technology",
      "format": "Solo Commentary"
    }}
  }}
}}
"""

def generate_with_gemini(content, style, duration, show_name):
    """Call Gemini API"""
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = build_llm_prompt(content, style, duration, show_name)

        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 4096,
                "temperature": 0.9,
            }
        )
        data = json.loads(resp.text)

        notes = ShowNotes(
            key_topics=data["show_notes"]["key_topics"],
            resources=data["show_notes"]["resources"],
            timestamps=data["show_notes"]["timestamps"],
            episode_details=EpisodeDetails(**data["show_notes"]["episode_details"]),
        )

        return GeneratedScript(
            intro=data["intro"],
            main_content=data["main_content"],
            outro=data["outro"],
            show_notes=notes,
        )
    except Exception as e:
        st.warning(f"⚠️ Gemini API failed: {e}")
        return None

def generate_fallback(content, style, duration, show_name):
    """Fallback multi-paragraph generator"""
    intro = f"""[INTRO MUSIC FADES IN]
Welcome to {show_name}! Today, we’re diving into {content[:100]}...
In this episode, I’ll set the stage, highlight why this topic matters, and get you ready for an exciting discussion.
[TRANSITION MUSIC]"""

    main = f"""In our main discussion, we’ll explore the topic step by step.

First, background and context to understand the bigger picture. 
Then, key developments shaping this area today. 
Finally, opportunities, challenges, and future possibilities.

Along the way, I’ll highlight key points, examples, and keep things engaging.
"""

    outro = f"""[OUTRO MUSIC FADES IN]
That wraps up today’s episode of {show_name}. We’ve covered the essentials and shared insights.
Be sure to subscribe, share, and join us next time for another great discussion.
[OUTRO MUSIC FADES OUT]"""

    notes = ShowNotes(
        key_topics=["Overview", "Context", "Key Developments", "Implications", "Future"],
        resources=["Transcript available", "Extra readings", "Follow us online"],
        timestamps=[
            {"time": "0:00", "topic": "Intro"},
            {"time": "2:00", "topic": "Background"},
            {"time": "6:00", "topic": "Key Points"},
            {"time": "12:00", "topic": "Future"},
            {"time": "15:00", "topic": "Outro"},
        ],
        episode_details=EpisodeDetails(duration=f"~{duration} minutes", category="General", format=style),
    )

    return GeneratedScript(intro, main, outro, notes)

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="PodcastAI", layout="wide")

# Header
st.markdown(
    f"<h1 style='text-align:center;'>{APP_TITLE}</h1>"
    f"<p style='text-align:center;color:gray;'>{APP_SUBTITLE}</p>",
    unsafe_allow_html=True,
)

# Gemini Status
online = check_gemini_status()
status_color = "🟢 Online" if online else "🔴 Offline"
st.markdown(f"### Gemini Status: {status_color}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Input Content")
    content = st.text_area("Paste article or transcript...", height=250)
    style = st.selectbox("Podcast Style", ["Conversational", "Professional", "Educational", "Interview"])
    duration = st.selectbox("Target Duration", ["5-10", "10-20", "20-30", "30+"])
    show_name = st.text_input("Show Name", value="The Show")

    if st.button("⚡ Generate Podcast Script", use_container_width=True):
        if content.strip():
            with st.spinner("Generating script..."):
                script = generate_with_gemini(content, style, duration, show_name) if online else None
                if not script:
                    script = generate_fallback(content, style, duration, show_name)
                st.session_state["script"] = script
        else:
            st.error("Please provide content!")

with col2:
    st.subheader("🎬 Generated Script")
    if "script" in st.session_state:
        script = st.session_state["script"]
        tabs = st.tabs(["Intro", "Main", "Outro", "Notes"])
        with tabs[0]:
            st.text_area("Intro", script.intro, height=200)
        with tabs[1]:
            st.text_area("Main Content", script.main_content, height=300)
        with tabs[2]:
            st.text_area("Outro", script.outro, height=150)
        with tabs[3]:
            st.json({
                "Key Topics": script.show_notes.key_topics,
                "Resources": script.show_notes.resources,
                "Timestamps": script.show_notes.timestamps,
                "Details": script.show_notes.episode_details.__dict__,
            })

        st.download_button("📥 Export JSON", data=json.dumps(script.__dict__, default=lambda o: o.__dict__, indent=2), file_name="podcast_script.json")
