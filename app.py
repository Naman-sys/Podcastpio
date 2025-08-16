"""
PodcastAI — Streamlit App (Dark Theme, Structured, Robust)
----------------------------------------------------------
• Turns raw text or an article URL into a professional podcast script.
• Uses Google Gemini (if configured) with a graceful local fallback.
• No .env required. Reads key from:
    1) st.secrets["GEMINI_API_KEY"]  (preferred for Streamlit Cloud)
    2) environment variable GEMINI_API_KEY
• Clean dark UI, two-pane layout, history of generated scripts, exports.
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
        --bg: #0b1220;          /* page bg */
        --panel: #121a2b;       /* card bg */
        --muted: #94a3b8;       /* secondary text */
        --text: #e5e7eb;        /* text */
        --brand: #6e7cff;       /* primary */
        --brand-2: #8a5cf6;     /* gradient */
        --ok: #10b981;
        --warn: #f59e0b;
        --err: #ef4444;
    }
    .stApp { background: var(--bg); color: var(--text); }

    .hero {
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
        border-radius: 18px;
        padding: 24px 22px;
        color: white;
        margin: 12px 0 22px 0;
        box-shadow: 0 10px 30px rgba(108, 99, 255, 0.25);
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

    textarea, .stTextInput>div>div>input {
        background: #0f172a !important;
        color: var(--text) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,.1) !important;
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

# =========== Session Helpers ===========
def _init_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history: Dict[str, PodcastScript] = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id: Optional[str] = None
    if "fetched" not in st.session_state:
        st.session_state.fetched: Optional[str] = None
_init_state()

# =========== Gemini API ===========
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
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": 2048})
        return getattr(resp, "text", None)
    except Exception:
        return None

# =========== Content Fetch ===========
def fetch_article(url: str, max_chars: int = 8000) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        r.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    body = soup.select_one("article") or soup.select_one("main") or soup.body
    text = body.get_text(" ", strip=True) if body else ""
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:max_chars] if len(text) >= 120 else None

# =========== Local Fallback ===========
def local_fallback_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    topics = ["Insights", "Trends", "Takeaways"]
    details = EpisodeDetails(duration=f"~{duration} minutes", category="General", format=style.title())
    intro = f"[INTRO MUSIC] Welcome to {show_name}! Let's dive in."
    main = "Main discussion: Context, Why it matters, and Next steps."
    outro = f"[OUTRO MUSIC] Thanks for listening to {show_name}!"
    notes = ShowNotes(
        key_topics=topics,
        resources=["Transcript available", "Follow us for more"],
        timestamps=[{"time": "0:00", "topic": "Intro"}, {"time": "2:00", "topic": "Main"}, {"time": "5:00", "topic": "Outro"}],
        episode_details=details,
    )
    return GeneratedScript(intro=intro, main_content=main, outro=outro, show_notes=notes)

# =========== Script Generation ===========
def build_llm_prompt(content: str, style: str, duration: str, show_name: str) -> str:
    return f"""
Write a podcast script in {style} style for {show_name}.
Duration: {duration} minutes.
Content:
{content[:2000]}
Include JSON with intro, main_content, outro, and show_notes.
"""

def generate_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    llm_text = try_gemini_generate(build_llm_prompt(content, style, duration, show_name))
    if llm_text:
        try:
            data = json.loads(llm_text.strip().strip("`"))
            details = EpisodeDetails(**data["show_notes"]["episode_details"])
            notes = ShowNotes(
                key_topics=data["show_notes"]["key_topics"],
                resources=data["show_notes"]["resources"],
                timestamps=data["show_notes"]["timestamps"],
                episode_details=details,
            )
            return GeneratedScript(intro=data["intro"], main_content=data["main_content"], outro=data["outro"], show_notes=notes)
        except Exception:
            pass
    return local_fallback_script(content, style, duration, show_name)

# =========== Helpers ===========
def script_to_txt(p: PodcastScript) -> str:
    s = p.script
    lines = [f"{p.title}", "INTRO:", s.intro, "MAIN:", s.main_content, "OUTRO:", s.outro]
    return "\n\n".join(lines)

def build_podcast_script(content: str, input_type: str, source_url: Optional[str], style: str, duration: str, show_name: str) -> PodcastScript:
    gen = generate_script(content, style, duration, show_name)
    pid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return PodcastScript(
        id=pid,
        title=f"{show_name} — {datetime.now().strftime('%Y-%m-%d')}",
        input_content=content,
        input_type=input_type,
        source_url=source_url,
        script=gen,
        podcast_style=style,
        target_duration=duration,
        show_name=show_name,
        word_count=len(content.split()),
        char_count=len(content),
        created_at=now,
    )

# =========== UI ===========
st.markdown('<div class="hero"><h1>🎙️ PodcastAI</h1><p>Turn articles into podcast scripts instantly.</p></div>', unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Input")
    tabs = st.tabs(["✏️ Manual Text", "🔗 URL Import"])
    with tabs[0]:
        raw_text = st.text_area("Paste text...", height=220, label_visibility="collapsed")
    with tabs[1]:
        url = st.text_input("Paste article URL")
        if st.button("Fetch", disabled=not url):
            text = fetch_article(url)
            st.session_state.fetched = text if text else None
            st.success("Fetched!") if text else st.error("Could not fetch.")
    st.markdown("---")
    style = st.selectbox("Style", ["conversational", "professional"], index=0)
    duration = st.selectbox("Duration", ["5-10", "10-20", "20+"], index=0)
    show_name = st.text_input("Show Name", value="The Show")
    content = (raw_text or "").strip() or (st.session_state.fetched or "")
    can_generate = len(content) >= 40
    if st.button("⚡ Generate Script", use_container_width=True, disabled=not can_generate):
        ps = build_podcast_script(content, "url" if url and not raw_text else "text", url, style, duration, show_name)
        st.session_state.history[ps.id] = ps
        st.session_state.current_id = ps.id
        st.success("🎉 Script generated!")

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎬 Generated Script")
    if st.session_state.current_id:
        script_obj: PodcastScript = st.session_state.history[st.session_state.current_id]
        s = script_obj.script
        t1, t2, t3, t4 = st.tabs(["Intro", "Main", "Outro", "Notes"])
        with t1: st.text_area("Intro", s.intro, height=220)
        with t2: st.text_area("Main", s.main_content, height=220)
        with t3: st.text_area("Outro", s.outro, height=220)
        with t4:
            st.markdown("### 📝 Show Notes")
            st.markdown("**Key Topics:** " + ", ".join(s.show_notes.key_topics))
            st.markdown("**Resources:**")
            for r in s.show_notes.resources: st.markdown(f"- {r}")
            st.markdown("**Timestamps:**")
            for ts in s.show_notes.timestamps: st.markdown(f"- {ts['time']}: {ts['topic']}")
            st.markdown("**Episode Details:**")
            st.write(s.show_notes.episode_details.__dict__)
        st.markdown("---")
        e1, e2 = st.columns(2)
        with e1:
            st.download_button("📄 Export TXT", data=script_to_txt(script_obj), file_name=f"podcast-{script_obj.id[:8]}.txt")
        with e2:
            st.download_button("📊 Export JSON", data=json.dumps(asdict(script_obj), indent=2), file_name=f"podcast-{script_obj.id[:8]}.json")
    else:
        st.info("👈 Add content and click Generate.")
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p class='muted' style='text-align:center'>Built with Streamlit • Gemini optional • Local fallback included</p>", unsafe_allow_html=True)
