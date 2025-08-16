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

import os, re, json, uuid, html, requests
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, List

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

# Dark theme
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
    .card {
        background: var(--panel);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 14px;
        padding: 16px 16px 12px 16px;
    }
    .stats-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 14px;
        margin: 10px 0 20px 0;
    }
    .stats-card h3 {
        margin: 0 0 6px 0;
        font-size: 1.1rem;
        color: var(--brand);
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stats-card p { margin: 3px 0; font-size: .9rem; color: var(--muted); }
</style>
""",
    unsafe_allow_html=True,
)

# =========
# Data Models
# =========

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

# ======================
# Session State Helpers
# ======================

def _init_state():
    if "history" not in st.session_state:
        st.session_state.history = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None
    if "fetched" not in st.session_state:
        st.session_state.fetched = None
    if "last_summary" not in st.session_state:
        st.session_state.last_summary = None

_init_state()

# =====================
# Gemini API Management
# =====================

def get_gemini_key() -> Optional[str]:
    key = st.secrets.get("GEMINI_API_KEY", None) if hasattr(st, "secrets") else None
    return key or os.getenv("GEMINI_API_KEY")

def check_gemini_status() -> bool:
    key = get_gemini_key()
    if not key:
        return False
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        _ = genai.GenerativeModel("gemini-1.5-pro")
        return True
    except Exception:
        return False

def try_gemini_generate(prompt: str) -> Optional[str]:
    key = get_gemini_key()
    if not key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": 2048})
        return getattr(resp, "text", None)
    except Exception:
        return None

# =========================
# Content Fetcher
# =========================

def fetch_article(url: str, max_chars: int = 8000) -> Optional[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (PodcastAI/1.0)"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "iframe"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    return text[:max_chars] if len(text) >= 120 else None

# =========================
# Script Generation
# =========================

def local_fallback_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    intro = f"[INTRO MUSIC] Welcome to {show_name}! Today we explore: {content[:120]}..."
    main = "Here’s a breakdown of the main points, explained clearly and engagingly..."
    outro = f"[OUTRO MUSIC] Thanks for listening to {show_name}. Join us again soon!"
    notes = ShowNotes(
        key_topics=["Overview", "Insights", "Takeaways"],
        resources=["Episode transcript available"],
        timestamps=[{"time": "0:00", "topic": "Intro"}, {"time": "5:00", "topic": "Main"}, {"time": "10:00", "topic": "Outro"}],
        episode_details=EpisodeDetails(duration=f"~{duration} minutes", category="General", format=style.title())
    )
    return GeneratedScript(intro, main, outro, notes)

def generate_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    prompt = f"""
You are a podcast writer. Style: {style}, Duration: {duration} minutes, Show: {show_name}.
Content:
\"\"\"{content[:3000]}\"\"\"
Return JSON with intro, main_content, outro, and show_notes.
"""
    llm_text = try_gemini_generate(prompt)
    if llm_text:
        try:
            data = json.loads(llm_text.strip().strip("```").strip("json"))
            notes = ShowNotes(
                key_topics=data["show_notes"]["key_topics"],
                resources=data["show_notes"]["resources"],
                timestamps=data["show_notes"]["timestamps"],
                episode_details=EpisodeDetails(**data["show_notes"]["episode_details"]),
            )
            return GeneratedScript(
                intro=data["intro"], main_content=data["main_content"], outro=data["outro"], show_notes=notes
            )
        except Exception:
            pass
    return local_fallback_script(content, style, duration, show_name)

# =========
# UI Helpers
# =========

def hero():
    st.markdown(
        """
<div class="hero">
  <h1>🎙️ PodcastAI</h1>
  <p>Transform any text or article into a polished podcast script — fast.</p>
</div>
""",
        unsafe_allow_html=True,
    )

def script_to_txt(p: PodcastScript) -> str:
    s = p.script
    return f"{p.title}\n\nINTRO:\n{s.intro}\n\nMAIN:\n{s.main_content}\n\nOUTRO:\n{s.outro}"

def build_podcast_script(content, input_type, source_url, style, duration, show_name) -> PodcastScript:
    gen = generate_script(content, style, duration, show_name)
    pid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    return PodcastScript(
        id=pid, title=f"{show_name} — {datetime.now().strftime('%Y-%m-%d')}",
        input_content=content, input_type=input_type, source_url=source_url,
        script=gen, podcast_style=style, target_duration=duration,
        show_name=show_name, word_count=len(content.split()), char_count=len(content),
        created_at=now
    )

# =========
# Main UI
# =========

hero()

# Gemini status indicator
status = check_gemini_status()
st.markdown(
    f"<p style='text-align:center;font-size:1.1rem;'>Gemini Status: {'🟢 Online' if status else '🔴 Offline'}</p>",
    unsafe_allow_html=True,
)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Input")
    tabs = st.tabs(["✏️ Manual Text", "🔗 URL Import"])

    raw_text, url = "", ""
    with tabs[0]:
        raw_text = st.text_area("Paste text...", height=220, placeholder="Paste article…", label_visibility="collapsed")
    with tabs[1]:
        url = st.text_input("Paste article URL", placeholder="https://example.com/article")
        if st.button("Fetch", use_container_width=True, disabled=not url):
            with st.spinner("Fetching..."):
                text = fetch_article(url)
                if text:
                    st.session_state.fetched = text
                    st.success("✅ Content fetched.")
                else:
                    st.error("Failed to extract content.")
        if st.session_state.fetched:
            st.text_area("Preview", st.session_state.fetched[:1000], height=160, label_visibility="collapsed")

    st.markdown("---")
    style = st.selectbox("Style", ["conversational", "professional", "educational", "interview"])
    duration = st.selectbox("Duration", ["5-10", "10-20", "20-30", "30+"])
    show_name = st.text_input("Show Name", value="The Show")

    content = (raw_text.strip() or st.session_state.fetched or "")
    if st.button("⚡ Generate Script", use_container_width=True, disabled=len(content) < 40):
        ps = build_podcast_script(content, "text" if raw_text else "url", url if url else None, style, duration, show_name)
        st.session_state.history[ps.id] = ps
        st.session_state.current_id = ps.id
        st.session_state.last_summary = {
            "words": ps.word_count,
            "chars": ps.char_count,
            "duration": ps.target_duration,
            "title": ps.title
        }
        st.success("🎉 Script generated!")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎬 Generated Script")

    # Place summary card here on right side
    if st.session_state.last_summary:
        summ = st.session_state.last_summary
        st.markdown(
            f"""
<div class="stats-card">
    <h3>📊 Quick Episode Summary</h3>
    <p><b>Title:</b> {summ['title']}</p>
    <p><b>Words:</b> {summ['words']} | <b>Characters:</b> {summ['chars']}</p>
    <p><b>Target Duration:</b> {summ['duration']} minutes</p>
</div>
""",
            unsafe_allow_html=True,
        )

    if st.session_state.current_id:
        ps = st.session_state.history[st.session_state.current_id]
        s = ps.script
        t1, t2, t3, t4 = st.tabs(["Intro", "Main", "Outro", "Notes"])
        with t1: st.text_area("Intro", s.intro, height=220, label_visibility="collapsed")
        with t2: st.text_area("Main", s.main_content, height=220, label_visibility="collapsed")
        with t3: st.text_area("Outro", s.outro, height=220, label_visibility="collapsed")
        with t4: st.json(asdict(s.show_notes))
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📄 Export TXT", data=script_to_txt(ps), file_name="podcast.txt", use_container_width=True)
        with col2:
            st.download_button("📊 Export JSON", data=json.dumps(asdict(ps), indent=2), file_name="podcast.json", use_container_width=True)
    else:
        st.info("👈 Add content and click Generate.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p class='muted' style='text-align:center'>Built with Streamlit • Gemini optional • Local fallback included</p>", unsafe_allow_html=True)
