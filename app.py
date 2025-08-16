"""
Podcast Script Generator - Streamlit Application
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
import time

# Gemini API key (hardcoded for now)
GEMINI_API_KEY = "YOUR_API_KEY_HERE"

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

# Configure Gemini API
def configure_gemini_api(api_key: str):
    if api_key and GENAI_AVAILABLE and genai:
        try:
            genai.configure(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"Failed to configure Gemini API: {str(e)}")
            return False
    return False


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


# ---------------- GEMINI SCRIPT GENERATION ---------------- #

def generate_fallback_script(content: str, style: str, duration: str, show_name: str = "The Show") -> GeneratedScript:
    """Fallback script if Gemini API is not available"""
    return GeneratedScript(
        intro=f"[INTRO] Welcome to {show_name}! (fallback)",
        main_content="This is a placeholder main content script.",
        outro="Thank you for listening! (fallback)",
        show_notes=ShowNotes(
            key_topics=["Topic1", "Topic2"],
            resources=["Resource1"],
            timestamps=[{"time": "0:00", "topic": "Intro"}],
            episode_details=EpisodeDetails(duration="~15 minutes", category="General", format="Solo Commentary")
        )
    )


def generate_podcast_script_with_gemini(content: str, style: str, duration: str, show_name: str = "The Show") -> GeneratedScript:
    system_prompt = f"""
You are a professional podcast script writer. Create a structured script.

Style: {style}
Target Duration: {duration} minutes
Show Name: {show_name}

Format JSON with:
intro, main_content, outro, show_notes
"""

    try:
        api_key = GEMINI_API_KEY
        if not api_key or not GENAI_AVAILABLE or not genai:
            raise Exception("Gemini API unavailable")

        if not configure_gemini_api(api_key):
            raise Exception("Failed to configure Gemini API")

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(
            f"{system_prompt}\n\nContent: {content}",
            generation_config={"response_mime_type": "application/json"}
        )

        if not response.text:
            raise Exception("Empty response from Gemini API")

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
        st.warning(f"Gemini API unavailable ({str(e)}). Using fallback...")
        return generate_fallback_script(content, style, duration, show_name)


# ---------------- CONTENT FETCHING ---------------- #

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


# ---------------- EXPORT FUNCTIONS ---------------- #

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


# ---------------- UI FUNCTIONS ---------------- #

def display_navigation():
    st.markdown("""
    <div style="text-align:center; background:#1f2937; padding:1rem; border-radius:8px; margin-bottom:2rem;">
        <h1 style="color:white;">🎙️ PodcastAI</h1>
        <p style="color:#9ca3af;">Transform Content into Professional Podcasts</p>
    </div>
    """, unsafe_allow_html=True)


def display_hero_section():
    st.markdown("""
    <div style="text-align:center; background:linear-gradient(135deg,#667eea,#764ba2); 
        color:white; padding:2rem; border-radius:1rem; margin-bottom:2rem;">
        <h2>Transform Content into <span style="color:#fbbf24;">Professional Podcasts</span></h2>
        <p>AI-powered tool that converts transcripts and articles into polished podcast scripts.</p>
    </div>
    """, unsafe_allow_html=True)


# ---------------- MAIN APP ---------------- #

def main():
    st.set_page_config(page_title="PodcastAI", page_icon="🎙️", layout="wide", initial_sidebar_state="collapsed")
    init_session_state()

    display_navigation()
    display_hero_section()

    col1, col2 = st.columns([1, 1])

    # ---------- LEFT COLUMN (INPUT) ----------
    with col1:
        st.markdown("### 📝 Input Content")
        tab1, tab2 = st.tabs(["✏️ Manual Text", "🔗 URL Import"])

        input_text, input_url = "", None

        with tab1:
            input_text = st.text_area("Content", placeholder="Paste text...", height=200, label_visibility="collapsed")
            if input_text:
                st.caption(f"📊 {len(input_text.split())} words • {len(input_text)} characters")

        with tab2:
            input_url = st.text_input("URL", placeholder="https://example.com/article", label_visibility="collapsed")
            if st.button("🔍 Fetch", disabled=not input_url):
                with st.spinner("Fetching content..."):
                    try:
                        fetched = fetch_content_from_url(input_url)
                        st.session_state.fetched_content = fetched
                        st.success(f"✅ Fetched {fetched['word_count']} words!")
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

            if st.session_state.fetched_content:
                with st.expander("📰 Preview", expanded=True):
                    st.text_area("Preview", st.session_state.fetched_content['content'][:300] + "...", height=100, disabled=True)

                    if st.button("✅ Use This Content"):
                        input_text = st.session_state.fetched_content['content']
                        st.session_state.fetched_content = None
                        st.rerun()

        with st.expander("⚙️ Advanced Options", expanded=False):
            podcast_style = st.selectbox("🎭 Style", ["conversational", "professional", "educational", "interview"])
            target_duration = st.selectbox("⏱️ Duration", ["5-10", "10-20", "20-30", "30+"])
            show_name = st.text_input("📻 Show Name", placeholder="Tech Today, News Weekly, etc.")

        content_to_use = input_text or (st.session_state.fetched_content['content'] if st.session_state.fetched_content else "")

        if st.button("⚡ Generate Podcast Script", type="primary", disabled=len(content_to_use.strip()) < 10, use_container_width=True):
            with st.spinner("🤖 Generating..."):
                try:
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
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")

    # ---------- RIGHT COLUMN (OUTPUT) ----------
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
                st.write(f"Duration: {details.duration}, Category: {details.category}, Format: {details.format}")

            st.markdown("---")
            st.download_button("📄 Export TXT", export_script_as_text(script), file_name=f"podcast-{script.id[:8]}.txt")
            st.download_button("📊 Export JSON", export_script_as_json(script), file_name=f"podcast-{script.id[:8]}.json")
        else:
            st.info("👈 Generate a script to see it here.")


if __name__ == "__main__":
    main()
