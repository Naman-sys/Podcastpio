"""
🎙️ Podcast Script Generator - Streamlit Application
"""

import streamlit as st
import os
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import requests
from bs4 import BeautifulSoup

# Gemini API key (hardcoded for now)
GEMINI_API_KEY = "YOUR_API_KEY_HERE"

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False


# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="PodcastAI 🎙️", page_icon="🎧", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for nicer look
st.markdown("""
    <style>
        /* Background */
        .stApp {
            background: #f8fafc;
        }
        /* Card-like containers */
        .block-container {
            padding: 2rem 2rem;
        }
        /* Headings */
        h1, h2, h3 {
            font-family: "Segoe UI", sans-serif;
        }
        /* Buttons */
        div.stButton > button {
            border-radius: 10px;
            background-color: #2563eb;
            color: white;
            font-weight: 600;
        }
        div.stButton > button:hover {
            background-color: #1d4ed8;
        }
        /* Tabs */
        .stTabs [role="tab"] {
            background: #e2e8f0;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-right: 0.5rem;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background: #2563eb;
            color: white;
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

def init_session_state():
    if 'generated_scripts' not in st.session_state:
        st.session_state.generated_scripts = {}
    if 'current_script' not in st.session_state:
        st.session_state.current_script = None
    if 'fetched_content' not in st.session_state:
        st.session_state.fetched_content = None


# ---------------- GEMINI ---------------- #

def configure_gemini_api(api_key: str):
    if api_key and GENAI_AVAILABLE and genai:
        try:
            genai.configure(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"⚠️ Failed to configure Gemini API: {str(e)}")
            return False
    return False


@st.cache_data(show_spinner=False)
def fetch_content_from_url(url: str) -> Dict[str, Any]:
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup(["script", "style", "nav", "footer", "aside"]):
        script.decompose()

    title = soup.title.string if soup.title else "Untitled Article"
    content = soup.body.get_text().strip() if soup.body else soup.get_text().strip()

    return {
        "title": title.strip(),
        "content": ' '.join(content.split()),
        "word_count": len(content.split())
    }


def generate_podcast_script_with_gemini(content: str, style: str, duration: str, show_name: str = "The Show") -> GeneratedScript:
    system_prompt = f"""
You are a professional podcast script writer. Create a structured, engaging script.

Style: {style}
Target Duration: {duration} minutes
Show Name: {show_name}

Format JSON with:
intro, main_content, outro, show_notes
"""

    try:
        if not configure_gemini_api(GEMINI_API_KEY):
            raise Exception("Gemini not available")

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(
            f"{system_prompt}\n\nContent: {content}",
            generation_config={"response_mime_type": "application/json"}
        )

        if not response.text:
            raise Exception("Empty response")

        script_data = json.loads(response.text)

        show_notes = ShowNotes(
            key_topics=script_data["show_notes"]["key_topics"],
            resources=script_data["show_notes"]["resources"],
            timestamps=script_data["show_notes"]["timestamps"],
            episode_details=EpisodeDetails(**script_data["show_notes"]["episode_details"])
        )

        return GeneratedScript(
            intro=script_data["intro"],
            main_content=script_data["main_content"],
            outro=script_data["outro"],
            show_notes=show_notes
        )

    except Exception as e:
        st.error(f"⚠️ Script generation failed: {str(e)}")
        return GeneratedScript(
            intro="(Failed to generate intro)",
            main_content="(Failed to generate main content)",
            outro="(Failed to generate outro)",
            show_notes=ShowNotes(
                key_topics=[],
                resources=[],
                timestamps=[],
                episode_details=EpisodeDetails(duration="Unknown", category="N/A", format="N/A")
            )
        )


# ---------------- EXPORT ---------------- #

def export_script_as_text(script: PodcastScript) -> str:
    if not script.script:
        return "No script content available"
    return f"""{script.title or "Podcast Script"}

INTRO:
{script.script.intro}

MAIN CONTENT:
{script.script.main_content}

OUTRO:
{script.script.outro}
"""


def export_script_as_json(script: PodcastScript) -> str:
    return json.dumps(asdict(script), indent=2, default=str)


# ---------------- UI ---------------- #

def display_navigation():
    st.markdown("""
    <div style="text-align:center; background:#1f2937; padding:1rem; border-radius:10px; margin-bottom:2rem;">
        <h1 style="color:white;">🎙️ PodcastAI</h1>
        <p style="color:#9ca3af;">Turn Articles into Podcast Scripts with AI</p>
    </div>
    """, unsafe_allow_html=True)


def display_hero_section():
    st.markdown("""
    <div style="text-align:center; background:linear-gradient(135deg,#3b82f6,#9333ea); 
        color:white; padding:2rem; border-radius:1rem; margin-bottom:2rem;">
        <h2>✨ From Content to Podcast in Seconds ✨</h2>
        <p>Paste an article or transcript, and get a polished podcast script with intros, outros, and notes.</p>
    </div>
    """, unsafe_allow_html=True)


# ---------------- MAIN ---------------- #

def main():
    init_session_state()
    display_navigation()
    display_hero_section()

    col1, col2 = st.columns([1.2, 1])

    # ---------- LEFT (INPUT) ----------
    with col1:
        st.markdown("### 📝 Input Content")
        tab1, tab2 = st.tabs(["✏️ Manual Text", "🔗 URL Import"])

        input_text, input_url = "", None

        with tab1:
            input_text = st.text_area("Paste text", placeholder="Paste article or transcript...", height=200)
            if input_text:
                st.caption(f"📊 {len(input_text.split())} words • {len(input_text)} characters")

        with tab2:
            input_url = st.text_input("URL", placeholder="https://example.com/article")
            if st.button("🔍 Fetch", disabled=not input_url):
                with st.spinner("Fetching content..."):
                    try:
                        fetched = fetch_content_from_url(input_url)
                        st.session_state.fetched_content = fetched
                        st.success(f"✅ {fetched['word_count']} words fetched!")
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

            if st.session_state.fetched_content:
                with st.expander("📰 Preview", expanded=True):
                    st.write(f"**{st.session_state.fetched_content['title']}**")
                    st.text_area("Preview", st.session_state.fetched_content['content'][:300] + "...", height=100, disabled=True)

                    if st.button("✅ Use This Content"):
                        input_text = st.session_state.fetched_content['content']
                        st.session_state.fetched_content = None
                        st.rerun()

        with st.expander("⚙️ Options", expanded=False):
            podcast_style = st.selectbox("🎭 Style", ["Conversational", "Professional", "Educational", "Interview"])
            target_duration = st.selectbox("⏱️ Duration", ["5-10", "10-20", "20-30", "30+"])
            show_name = st.text_input("📻 Show Name", placeholder="Tech Today, News Weekly, etc.")

        content_to_use = input_text or (st.session_state.fetched_content['content'] if st.session_state.fetched_content else "")

        st.markdown("---")
        if st.button("⚡ Generate Script", type="primary", use_container_width=True, disabled=len(content_to_use.strip()) < 10):
            with st.spinner("🤖 Generating your podcast script..."):
                generated = generate_podcast_script_with_gemini(content_to_use, podcast_style, target_duration, show_name or "The Show")
                script_id = str(uuid.uuid4())
                podcast_script = PodcastScript(
                    id=script_id,
                    title=f"{show_name or 'Podcast'} - {datetime.now().strftime('%Y-%m-%d')}",
                    input_content=content_to_use,
                    input_type="text" if input_text else "url",
                    source_url=input_url,
                    script=generated,
                    podcast_style=podcast_style,
                    target_duration=target_duration,
                    show_name=show_name,
                    word_count=len(content_to_use.split()),
                    char_count=len(content_to_use),
                    created_at=datetime.now()
                )
                st.session_state.generated_scripts[script_id] = podcast_script
                st.session_state.current_script = script_id
                st.success("🎉 Script generated!")

    # ---------- RIGHT (OUTPUT) ----------
    with col2:
        if st.session_state.current_script and st.session_state.current_script in st.session_state.generated_scripts:
            script = st.session_state.generated_scripts[st.session_state.current_script]
            st.markdown("### 🎬 Generated Script")

            tab1, tab2, tab3, tab4 = st.tabs(["🎬 Intro", "📖 Main", "🎬 Outro", "📋 Notes"])
            with tab1: st.text_area("Intro", script.script.intro, height=200, disabled=True)
            with tab2: st.text_area("Main Content", script.script.main_content, height=200, disabled=True)
            with tab3: st.text_area("Outro", script.script.outro, height=200, disabled=True)
            with tab4:
                st.write("**Key Topics:**", ", ".join(script.script.show_notes.key_topics))
                st.write("**Resources:**", *[f"• {r}" for r in script.script.show_notes.resources])
                st.write("**Timestamps:**")
                for ts in script.script.show_notes.timestamps:
                    st.write(f"**{ts['time']}** - {ts['topic']}")
                details = script.script.show_notes.episode_details
                st.write(f"🎧 {details.duration} • {details.category} • {details.format}")

            st.markdown("---")
            st.download_button("📄 Export TXT", export_script_as_text(script), file_name=f"podcast-{script.id[:8]}.txt")
            st.download_button("📊 Export JSON", export_script_as_json(script), file_name=f"podcast-{script.id[:8]}.json")
        else:
            st.info("👈 Enter content and click **Generate** to see your script here.")


if __name__ == "__main__":
    main()
