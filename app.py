"""
PodcastAI — Streamlit App (Dark Theme, Varied Output)
----------------------------------------------------
• Turns raw text or article URL into a professional podcast script.
• Uses Google Gemini (if configured) with a graceful local fallback.
• No .env required. Reads key from:
    1) st.secrets["GEMINI_API_KEY"]  (preferred for Streamlit Cloud)
    2) environment variable GEMINI_API_KEY
• Clean dark UI, two-pane layout, history of generated scripts, exports.
• NEW: Added Gemini randomness + multiple fallback templates for variety.
"""

from __future__ import annotations

import os
import re
import json
import uuid
import random
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
        --warn: #f59e0b;
        --err: #ef4444;
    }
    .stApp { background: var(--bg); color: var(--text); }
    .hero {
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
        border-radius: 18px;
        padding: 24px;
        color: white;
        margin: 12px 0 22px 0;
        text-align: center;
        box-shadow: 0 10px 30px rgba(108, 99, 255, 0.25);
    }
    .hero h1 { margin: 0 0 6px 0; font-size: 2rem; font-weight: 800; }
    .card {
        background: var(--panel);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,.06);
    }
    textarea, .stTextInput>div>div>input {
        background: #0f172a !important;
        color: var(--text) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,.1) !important;
    }
    div.stButton>button {
        background: var(--brand) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700;
        padding: .6rem 1rem;
        border: none !important;
    }
    div.stButton>button:hover { filter: brightness(1.08); }
    .stTabs [role="tab"] {
        background: #0f172a;
        color: var(--muted);
        border-radius: 10px;
        padding: .5rem .9rem;
        margin-right: .4rem;
        border: 1px solid rgba(255,255,255,.06);
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: var(--brand);
        color: white;
    }
    .muted { color: var(--muted); font-size: .9rem; }
</style>
""",
    unsafe_allow_html=True,
)

# =========== Data Models ===========
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

# Session state
if "history" not in st.session_state:
    st.session_state.history: Dict[str, PodcastScript] = {}
if "current_id" not in st.session_state:
    st.session_state.current_id: Optional[str] = None
if "fetched" not in st.session_state:
    st.session_state.fetched: Optional[str] = None

# ================== Gemini API ==================
def get_gemini_key() -> Optional[str]:
    key = st.secrets.get("GEMINI_API_KEY", None) if hasattr(st, "secrets") else None
    return key or os.getenv("GEMINI_API_KEY")

def try_gemini_generate(prompt: str) -> Optional[str]:
    api_key = get_gemini_key()
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.8,
                "top_p": 0.9,
                "max_output_tokens": 2048,
            }
        )
        return getattr(resp, "text", None)
    except Exception:
        return None

# =============== Content Processing ===============
def fetch_article(url: str, max_chars: int = 8000) -> Optional[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (PodcastAI/1.0)"}
        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()
    except Exception:
        return None
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script","style","nav","footer","header","noscript","aside"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:max_chars] if len(text) > 100 else None

def extract_key_topics(text: str, top_k: int = 5) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text.lower())
    freq: Dict[str,int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return [w.capitalize() for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_k]]

# =============== Script Generation ===============
SYSTEM_JSON_SCHEMA = """{ "intro": "...", "main_content": "...", "outro": "...", "show_notes": { "key_topics": [], "resources": [], "timestamps": [], "episode_details": { "duration": "", "category": "", "format": "" }}}"""

def build_llm_prompt(content: str, style: str, duration: str, show_name: str) -> str:
    return f"""You are a creative podcast writer.
Style: {style}, Duration: {duration} min, Show: {show_name}
Base content: \"\"\"{content[:5000]}\"\"\"
Follow JSON strictly: {SYSTEM_JSON_SCHEMA}"""

def local_fallback_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    topics = extract_key_topics(content)
    details = EpisodeDetails(f"~{duration} min", "General", style.title())

    templates = [
        (
            f"[MUSIC INTRO]\nWelcome to {show_name}! Today’s focus: {topics[0]}. Let's dive in.\n",
            "We’ll explore background, impacts, and key insights.\n[TRANSITION MUSIC]",
            f"[OUTRO] Thanks for tuning into {show_name}. Stay curious!"
        ),
        (
            f"[INTRO MUSIC]\nHello and welcome back to {show_name}. Ever wondered about {topics[1]}? Let's unpack it.\n",
            "Breaking it down: the origins, why it matters, and what’s next.\n[TRANSITION]",
            f"[CLOSING] That’s all for today’s {show_name}. Share this with a friend!"
        ),
        (
            f"[INTRO BEAT]\nThis is {show_name}. In this episode, we’re spotlighting {topics[2]}.\n",
            "Here’s the journey: where it started, today’s challenges, and tomorrow’s opportunities.\n",
            f"[OUTRO] Appreciate your time with {show_name}. Catch you in the next one!"
        ),
    ]

    intro, main, outro = random.choice(templates)

    notes = ShowNotes(
        key_topics=topics,
        resources=["Transcript available", "Follow us online"],
        timestamps=[{"time":"0:00","topic":"Intro"},{"time":"2:00","topic":"Main"},{"time":"5:00","topic":"Outro"}],
        episode_details=details,
    )
    return GeneratedScript(intro, main, outro, notes)

def generate_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    llm_text = try_gemini_generate(build_llm_prompt(content, style, duration, show_name))
    if llm_text:
        llm_text = llm_text.strip().strip("`")
        try:
            data = json.loads(llm_text)
            details = EpisodeDetails(**data["show_notes"]["episode_details"])
            notes = ShowNotes(data["show_notes"]["key_topics"], data["show_notes"]["resources"], data["show_notes"]["timestamps"], details)
            return GeneratedScript(data["intro"], data["main_content"], data["outro"], notes)
        except Exception:
            pass
    return local_fallback_script(content, style, duration, show_name)

# =============== UI ===============
def hero():
    st.markdown('<div class="hero"><h1>🎙️ PodcastAI</h1><p>Turn articles into engaging podcast scripts</p></div>', unsafe_allow_html=True)

def script_to_txt(p: PodcastScript) -> str:
    s = p.script
    return f"""{p.title}\n\nINTRO:\n{s.intro}\n\nMAIN:\n{s.main_content}\n\nOUTRO:\n{s.outro}\n"""

# Main Layout
hero()
left, right = st.columns([1,1], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Input")
    tabs = st.tabs(["✏️ Manual Text","🔗 URL Import"])
    with tabs[0]:
        raw_text = st.text_area("Paste text...", height=200, label_visibility="collapsed")
    with tabs[1]:
        url = st.text_input("Article URL")
        if st.button("Fetch", disabled=not url):
            with st.spinner("Fetching..."):
                txt = fetch_article(url)
                st.session_state.fetched = txt
                st.success("✅ Content fetched" if txt else "❌ Failed to fetch")
        if st.session_state.fetched:
            st.text_area("Preview", st.session_state.fetched[:1000], height=150)

    st.subheader("⚙️ Options")
    style = st.selectbox("Style", ["conversational","professional","educational","interview"])
    duration = st.selectbox("Duration", ["5-10","10-20","20-30"])
    show_name = st.text_input("Show Name", value="The Show")

    content = (raw_text or "").strip() or (st.session_state.fetched or "")
    can_generate = len(content) > 40

    if st.button("⚡ Generate Script", disabled=not can_generate, use_container_width=True):
        ps = PodcastScript(
            id=str(uuid.uuid4()),
            title=f"{show_name} — {datetime.now().strftime('%Y-%m-%d')}",
            input_content=content,
            input_type="text" if raw_text.strip() else "url",
            source_url=url if (url and not raw_text.strip()) else None,
            script=generate_script(content, style, duration, show_name),
            podcast_style=style,
            target_duration=duration,
            show_name=show_name,
            word_count=len(content.split()),
            char_count=len(content),
            created_at=datetime.utcnow().isoformat()+"Z",
        )
        st.session_state.history[ps.id] = ps
        st.session_state.current_id = ps.id
        st.success("🎉 Script generated!")

    # Blank space summary card
    if st.session_state.current_id:
        p = st.session_state.history[st.session_state.current_id]
        st.markdown(
            f"""<div class="card">
            <h4>📊 Quick Episode Summary</h4>
            <b>Title:</b> {p.title}<br>
            <b>Words:</b> {p.word_count} | <b>Characters:</b> {p.char_count}<br>
            <b>Target Duration:</b> {p.target_duration} minutes
            </div>""", unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎬 Generated Script")
    if st.session_state.current_id:
        s = st.session_state.history[st.session_state.current_id].script
        t1,t2,t3,t4 = st.tabs(["Intro","Main","Outro","Notes"])
        with t1: st.text_area("Intro", s.intro, height=200, label_visibility="collapsed")
        with t2: st.text_area("Main", s.main_content, height=200, label_visibility="collapsed")
        with t3: st.text_area("Outro", s.outro, height=200, label_visibility="collapsed")
        with t4: st.write(s.show_notes)
        e1,e2 = st.columns(2)
        with e1: st.download_button("📄 Export TXT", script_to_txt(st.session_state.history[st.session_state.current_id]), "script.txt")
        with e2: st.download_button("📊 Export JSON", json.dumps(asdict(st.session_state.history[st.session_state.current_id]), indent=2), "script.json")
    else:
        st.info("👈 Generate a script to see it here")
    st.markdown('</div>', unsafe_allow_html=True)

# Gemini Indicator
st.markdown("---")
if get_gemini_key():
    st.markdown("<p style='text-align:center;color:var(--ok)'>🟢 Gemini API Connected</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align:center;color:var(--warn)'>🟡 Gemini API Not Configured (using fallback)</p>", unsafe_allow_html=True)
