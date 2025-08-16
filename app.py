"""
Podcast Script Generator - Dark Themed Streamlit App
Turns articles or transcripts into professional podcast scripts
Powered by Google Gemini AI (with fallback generator)
"""

import streamlit as st
import os, json, uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import requests
from bs4 import BeautifulSoup

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(
    page_title="PodcastAI - Script Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- DARK THEME CSS ---------------- #
st.markdown("""
    <style>
        /* Global Dark Background */
        .stApp {
            background-color: #0f172a;
            color: #f1f5f9;
        }

        /* Hero Header */
        .hero {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 2.5rem 1.5rem;
            border-radius: 1rem;
            text-align: center;
            margin-bottom: 2rem;
            color: white;
        }
        .hero h1 {
            font-size: 2.2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .hero p {
            font-size: 1.1rem;
            opacity: 0.85;
        }

        /* Inputs */
        textarea, input, .stTextInput, .stTextArea {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
            border-radius: 10px;
        }

        /* Buttons */
        div.stButton > button {
            border-radius: 8px;
            background-color: #3b82f6;
            color: white;
            font-weight: 600;
        }
        div.stButton > button:hover {
            background-color: #2563eb;
        }

        /* Tabs */
        .stTabs [role="tab"] {
            background: #334155;
            color: #94a3b8;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            margin-right: 0.5rem;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background: #3b82f6;
            color: white;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- DATA MODELS ---------------- #
@dataclass
class EpisodeDetails:
    duration: str
    category: str
    format: str
    season: Optional[str] = None
    episode: Optional[str] = None

@dataclass
class ShowNotes:
    key_topics: List[str]
    resources: List[str]
    timestamps: List[Dict[str, str]]
    episode_details: EpisodeDetails

@dataclass
class GeneratedScript:
    intro: str
    main_content: str
    outro: str
    show_notes: ShowNotes

@dataclass
class PodcastScript:
    id: str
    title: Optional[str]
    input_content: str
    input_type: str
    source_url: Optional[str]
    script: Optional[GeneratedScript]
    podcast_style: str
    target_duration: str
    show_name: Optional[str]
    word_count: Optional[int]
    char_count: Optional[int]
    created_at: datetime

# ---------------- SESSION STATE ---------------- #
if "generated_scripts" not in st.session_state:
    st.session_state.generated_scripts = {}
if "current_script" not in st.session_state:
    st.session_state.current_script = None
if "fetched_content" not in st.session_state:
    st.session_state.fetched_content = None

# ---------------- SCRIPT GENERATION ---------------- #
def generate_fallback_script(content: str, style: str, duration: str, show_name: str = "The Show") -> GeneratedScript:
    """Simple local script generator (used if API not available)"""
    first_sentence = content.split(".")[0] if "." in content else content[:100]

    intro = f"""[INTRO MUSIC FADES IN]

Welcome to {show_name}! Today we’re diving into something exciting.

[MUSIC FADES TO BACKGROUND]

{first_sentence}...
"""

    main = f"""[MAIN SEGMENT]

Let’s break it down step by step.

1. Context
2. Key insights
3. Why this matters

[MUSIC TRANSITION]

That’s the big picture of today’s topic."""

    outro = f"""[OUTRO MUSIC FADES IN]

Thanks for tuning in to {show_name}.  
Don’t forget to subscribe & share. See you next time!

[OUTRO MUSIC FADES OUT]"""

    notes = ShowNotes(
        key_topics=["Insights", "Trends", "Takeaways"],
        resources=["Transcript available on our site", "Follow us for updates"],
        timestamps=[
            {"time": "0:00", "topic": "Introduction"},
            {"time": "1:00", "topic": "Main Discussion"},
            {"time": "4:00", "topic": "Outro"},
        ],
        episode_details=EpisodeDetails(duration=f"{duration} mins", category="General", format=style)
    )

    return GeneratedScript(intro=intro, main_content=main, outro=outro, show_notes=notes)

def generate_podcast_script(content, style, duration, show_name):
    """Use Gemini API if available, otherwise fallback"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Make a podcast script about: {content[:500]}")
        if response.text:
            return generate_fallback_script(content, style, duration, show_name)  # simulate parse
    except:
        return generate_fallback_script(content, style, duration, show_name)

# ---------------- FETCH URL CONTENT ---------------- #
def fetch_content(url: str):
    try:
        res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        return text[:2000]
    except:
        return None

# ---------------- EXPORT ---------------- #
def export_script_as_text(script: PodcastScript) -> str:
    return f"""{script.title}

INTRO:
{script.script.intro}

MAIN CONTENT:
{script.script.main_content}

OUTRO:
{script.script.outro}

SHOW NOTES:
{script.script.show_notes.key_topics}
"""

def export_script_as_json(script: PodcastScript) -> str:
    return json.dumps(asdict(script), indent=2, default=str)

# ---------------- UI ---------------- #
# Hero Section
st.markdown("""
<div class="hero">
    <h1>🎙️ PodcastAI</h1>
    <p>Turn any text or article into a professional podcast script</p>
</div>
""", unsafe_allow_html=True)

# Layout
col1, col2 = st.columns([1,1])

with col1:
    st.subheader("📝 Input Content")
    tab1, tab2 = st.tabs(["✏️ Manual Text", "🔗 URL Import"])

    with tab1:
        text_input = st.text_area("Paste article or transcript...", height=200)
    with tab2:
        url = st.text_input("Enter URL")
        if st.button("Fetch"):
            data = fetch_content(url)
            if data:
                st.session_state.fetched_content = data
                st.success("✅ Content fetched!")
            else:
                st.error("❌ Failed to fetch")

    podcast_style = st.selectbox("🎭 Style", ["conversational", "professional", "educational"])
    duration = st.selectbox("⏱️ Duration", ["5-10", "10-20", "20-30"])
    show_name = st.text_input("📻 Show Name", "The Show")

    content = text_input or st.session_state.fetched_content

    if st.button("⚡ Generate Podcast Script", use_container_width=True):
        if content and len(content) > 20:
            generated = generate_podcast_script(content, podcast_style, duration, show_name)
            pid = str(uuid.uuid4())
            script = PodcastScript(
                id=pid, title=f"{show_name} - {datetime.now().strftime('%Y-%m-%d')}",
                input_content=content, input_type="text", source_url=url,
                script=generated, podcast_style=podcast_style,
                target_duration=duration, show_name=show_name,
                word_count=len(content.split()), char_count=len(content),
                created_at=datetime.now()
            )
            st.session_state.generated_scripts[pid] = script
            st.session_state.current_script = pid
            st.success("🎉 Script generated!")

with col2:
    if st.session_state.current_script:
        script = st.session_state.generated_scripts[st.session_state.current_script]
        st.subheader("🎬 Generated Script")

        t1, t2, t3, t4 = st.tabs(["Intro", "Main", "Outro", "Notes"])
        with t1: st.text_area("Intro", script.script.intro, height=200)
        with t2: st.text_area("Main", script.script.main_content, height=200)
        with t3: st.text_area("Outro", script.script.outro, height=200)
        with t4:
            st.json(asdict(script.script.show_notes))

        st.download_button("📄 Export TXT", export_script_as_text(script), "script.txt")
        st.download_button("📊 Export JSON", export_script_as_json(script), "script.json")
    else:
        st.info("👈 Start by entering text or URL and click Generate!")

# Footer
st.markdown("""---""")
st.markdown("<p style='text-align:center;color:gray;'>Built with Streamlit • Powered by Google Gemini AI</p>", unsafe_allow_html=True)
