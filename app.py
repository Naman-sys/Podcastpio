"""
PodcastAI — Streamlit App (Dark Theme, Structured, Robust)
----------------------------------------------------------
• Turns raw text or an article URL into a professional podcast script.
• Uses Google Gemini (if configured) with a graceful local fallback.
• No .env required. Reads key from:
    1) st.secrets["GEMINI_API_KEY"]  (preferred for Streamlit Cloud)
    2) environment variable GEMINI_API_KEY
• Clean dark UI, two-pane layout, history of generated scripts, exports.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import os
import re
import json
import uuid
import html
import requests
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List

import streamlit as st
from bs4 import BeautifulSoup

# =========================
# Page Setup & Global Style
# =========================

st.set_page_config(
    page_title="PodcastAI — Script Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Polished dark theme
st.markdown(
    """
<style>
    :root {
        --bg: #0b1220;         
        --panel: #121a2b;      
        --muted: #94a3b8;      
        --text: #e5e7eb;       
        --brand: #6e7cff;      
        --brand-2: #8a5cf6;    
        --ok: #10b981;
        --err: #ef4444;
    }
    .stApp { background: var(--bg); color: var(--text); }

    .hero {
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
        border-radius: 18px;
        padding: 24px 22px;
        color: white;
        margin: 12px 0 22px 0;
        text-align: center;
    }
    .hero h1 { margin: 0 0 6px 0; font-size: 2rem; font-weight: 800; }
    .hero p  { margin: 0; opacity: .92; }

    .card {
        background: var(--panel);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 14px;
        padding: 16px 16px 12px 16px;
    }

    div.stButton>button {
        background: var(--brand) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700;
        padding: .6rem 1rem;
    }
    div.stButton>button:hover { filter: brightness(1.08); }

    .muted { color: var(--muted); font-size: .9rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ============
# Data Classes
# ============

@dataclass
class EpisodeDetails:
    duration: str
    category: str
    format: str

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
    title: str
    input_content: str
    input_type: str
    source_url: Optional[str]
    script: GeneratedScript
    podcast_style: str
    target_duration: str
    show_name: str
    word_count: int
    char_count: int
    created_at: str

# =====================
# Session State Helpers
# =====================

def _init_state():
    if "history" not in st.session_state:
        st.session_state.history = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None
    if "fetched" not in st.session_state:
        st.session_state.fetched = None

_init_state()

# ====================
# Gemini API Utilities
# ====================

def get_gemini_key():
    key = st.secrets.get("GEMINI_API_KEY", None) if hasattr(st, "secrets") else None
    return key or os.getenv("GEMINI_API_KEY")

def try_gemini_generate(prompt: str):
    api_key = get_gemini_key()
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": 2048})
        return getattr(resp, "text", None)
    except Exception:
        return None

# =========================
# Content Processing
# =========================

def fetch_article(url: str, max_chars=8000):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    content = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", html.unescape(content))[:max_chars]

# =========================
# Local Script Generator
# =========================

def local_fallback_script(content, style, duration, show_name):
    intro = f"""[INTRO MUSIC]
Welcome to {show_name}! Let's dive into today's topic.
"""
    main = """We'll break this down into key sections for clarity and insights."""
    outro = f"""[OUTRO MUSIC]
Thanks for listening to {show_name}!"""
    notes = ShowNotes(
        key_topics=["Insights", "Trends", "Takeaways"],
        resources=["Transcript available", "Follow us for updates"],
        timestamps=[{"time":"0:00","topic":"Intro"},{"time":"1:00","topic":"Main"},{"time":"3:00","topic":"Outro"}],
        episode_details=EpisodeDetails(duration=f"{duration} min", category="General", format=style)
    )
    return GeneratedScript(intro, main, outro, notes)

def generate_script(content, style, duration, show_name):
    prompt = f"""Create a podcast script in {style} style, duration {duration} minutes, for {show_name}.
Content:
{content[:4000]}"""
    llm_text = try_gemini_generate(prompt)
    if llm_text:
        try:
            data = json.loads(llm_text)
            details = EpisodeDetails(**data["show_notes"]["episode_details"])
            notes = ShowNotes(
                key_topics=data["show_notes"]["key_topics"],
                resources=data["show_notes"]["resources"],
                timestamps=data["show_notes"]["timestamps"],
                episode_details=details,
            )
            return GeneratedScript(
                intro=data["intro"], main_content=data["main_content"],
                outro=data["outro"], show_notes=notes
            )
        except Exception:
            pass
    return local_fallback_script(content, style, duration, show_name)

# =========
# UI Parts
# =========

def hero():
    st.markdown(
        """<div class="hero"><h1>🎙️ PodcastAI</h1><p>Turn any text or URL into a polished podcast script.</p></div>""",
        unsafe_allow_html=True,
    )

def script_to_txt(p: PodcastScript):
    s = p.script
    return f"""{p.title}

INTRO:
{s.intro}

MAIN:
{s.main_content}

OUTRO:
{s.outro}

KEY TOPICS: {', '.join(s.show_notes.key_topics)}
"""

# =========
# Main View
# =========

hero()

# Gemini indicator
if get_gemini_key():
    st.markdown("<p style='color: var(--ok)'>🟢 Gemini API Connected</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='color: var(--err)'>🔴 Gemini API Not Configured — using local fallback</p>", unsafe_allow_html=True)

left, right = st.columns([1, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Input")
    tabs = st.tabs(["✏️ Manual", "🔗 URL"])
    with tabs[0]:
        raw_text = st.text_area("Paste text...", height=200, label_visibility="collapsed")
    with tabs[1]:
        url = st.text_input("Paste URL")
        if st.button("Fetch", disabled=not url):
            text = fetch_article(url)
            if text:
                st.session_state.fetched = text
                st.success("✅ Content fetched")
            else:
                st.error("Couldn’t extract content.")
        if st.session_state.fetched:
            st.text_area("Preview", st.session_state.fetched[:1000], height=150)

    st.markdown("---")
    style = st.selectbox("Style", ["conversational","professional","educational","interview"])
    duration = st.selectbox("Duration", ["5-10","10-20","20-30"])
    show_name = st.text_input("Show Name", value="The Show")

    content = (raw_text.strip() if raw_text else "") or (st.session_state.fetched or "")
    if st.button("⚡ Generate Script", disabled=len(content) < 40):
        ps = PodcastScript(
            id=str(uuid.uuid4()),
            title=f"{show_name} — {datetime.now().strftime('%Y-%m-%d')}",
            input_content=content, input_type="text",
            source_url=url if url else None,
            script=generate_script(content, style, duration, show_name),
            podcast_style=style, target_duration=duration, show_name=show_name,
            word_count=len(content.split()), char_count=len(content),
            created_at=datetime.utcnow().isoformat()+"Z"
        )
        st.session_state.history[ps.id] = ps
        st.session_state.current_id = ps.id
        st.success("🎉 Script generated!")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎬 Generated Script")

    if st.session_state.current_id:
        ps = st.session_state.history[st.session_state.current_id]
        s = ps.script
        t1, t2, t3, t4 = st.tabs(["Intro", "Main", "Outro", "Notes"])
        with t1: st.text_area("Intro", s.intro, height=200)
        with t2: st.text_area("Main", s.main_content, height=200)
        with t3: st.text_area("Outro", s.outro, height=200)
        with t4:
            st.markdown("### 📝 Show Notes")
            st.markdown("**Key Topics:** " + ", ".join(s.show_notes.key_topics))
            st.markdown("**Resources:**")
            for r in s.show_notes.resources: st.markdown(f"- {r}")
            st.markdown("**Timestamps:**")
            for ts in s.show_notes.timestamps: st.markdown(f"- {ts['time']}: {ts['topic']}")
            st.markdown("**Episode Details:**")
            st.write(s.show_notes.episode_details.__dict__)

        # Export buttons side-by-side
        e1, e2 = st.columns(2)
        with e1: st.download_button("📄 Export TXT", data=script_to_txt(ps), file_name=f"{ps.id}.txt")
        with e2: st.download_button("📊 Export JSON", data=json.dumps(asdict(ps), indent=2), file_name=f"{ps.id}.json")

        # Now Quick Summary BELOW the export buttons
        st.markdown("---")
        st.markdown("### 📊 Quick Episode Summary")
        st.info(f"**Title:** {ps.title}\n\n**Words:** {ps.word_count} | **Characters:** {ps.char_count}\n\n**Target Duration:** {ps.target_duration} minutes")

    else:
        st.info("👈 Add content and generate a script.")

    st.markdown("</div>", unsafe_allow_html=True)
