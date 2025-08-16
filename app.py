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
import time
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

    /* hero */
    .hero {
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
        border-radius: 18px;
        padding: 24px 22px;
        color: white;
        margin: 12px 0 22px 0;
        box-shadow: 0 10px 30px rgba(108, 99, 255, 0.25);
        text-align: center;
    }
    .hero h1 { margin: 0 0 6px 0; font-size: 2rem; font-weight: 800; letter-spacing: .2px; }
    .hero p  { margin: 0; opacity: .92; }

    /* containers / cards */
    .card {
        background: var(--panel);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 14px;
        padding: 16px 16px 12px 16px;
    }

    /* inputs */
    textarea, .stTextInput>div>div>input {
        background: #0f172a !important;
        color: var(--text) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,.1) !important;
    }
    .stSelectbox>div>div {
        background: #0f172a !important;
        border-radius: 10px !important;
    }

    /* buttons */
    div.stButton>button {
        background: var(--brand) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700;
        padding: .6rem 1rem;
    }
    div.stButton>button:hover { filter: brightness(1.08); }

    /* tabs */
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

    /* expander header */
    .streamlit-expanderHeader {
        background: #0f172a !important;
        color: var(--text) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,.06);
    }

    /* small details */
    .muted { color: var(--muted); font-size: .9rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ===========
# Data Models
# ===========

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
    input_type: str           # "text" | "url"
    source_url: Optional[str]
    script: GeneratedScript
    podcast_style: str
    target_duration: str
    show_name: str
    word_count: int
    char_count: int
    created_at: str           # iso format for JSON serializability


# ======================
# Session State Helpers
# ======================

def _init_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history: Dict[str, PodcastScript] = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id: Optional[str] = None
    if "fetched" not in st.session_state:
        st.session_state.fetched: Optional[str] = None

_init_state()


# =====================
# Gemini API Management
# =====================

def get_gemini_key() -> Optional[str]:
    # Preferred: Streamlit Cloud secrets
    key = st.secrets.get("GEMINI_API_KEY", None) if hasattr(st, "secrets") else None
    if key:
        return key
    # Fallback: environment variable
    return os.getenv("GEMINI_API_KEY")


def try_gemini_generate(prompt: str) -> Optional[str]:
    """
    Return model text if Gemini is available and returns text, else None.
    We keep it minimal and robust — parsing handled by caller.
    """
    api_key = get_gemini_key()
    if not api_key:
        return None

    try:
        import google.generativeai as genai  # lazy import
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": 2048})
        text = getattr(resp, "text", None)
        return text if text and text.strip() else None
    except Exception:
        return None


# ==========================
# Content & Text Processing
# ==========================

def fetch_article(url: str, max_chars: int = 8000) -> Optional[str]:
    """Fetch & extract readable text from a URL (best-effort, resilient)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (PodcastAI/1.0)"}
        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "iframe"]):
        tag.decompose()

    # Prefer semantic containers
    candidates = [
        soup.select_one("article"),
        soup.select_one("main"),
        soup.select_one('[role="main"]'),
        soup.select_one(".article-content, .post-content, .entry-content, .story-body"),
        soup.body,
    ]
    text = ""
    for c in candidates:
        if c:
            t = c.get_text(" ", strip=True)
            if len(t) > len(text):
                text = t

    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    return text[:max_chars] if len(text) >= 120 else None


def extract_key_topics(text: str, top_k: int = 5) -> List[str]:
    stop = {
        "the","a","an","and","or","but","in","on","at","to","for","of","with","by",
        "is","are","was","were","be","been","have","has","had","do","does","did",
        "will","would","could","should","may","might","can","this","that","these",
        "those","i","you","he","she","it","we","they","me","him","her","us","them",
        "from","as","about","more","most","other","some","such","no","not","only",
        "own","same","so","than","too","very","just","into","over","after","before"
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text.lower())
    freq: Dict[str,int] = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1
    return [w.capitalize() for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_k]] or ["Insights","Trends","Takeaways"]


# =========================
# Script Generation Routines
# =========================

SYSTEM_JSON_SCHEMA = """
Return ONLY JSON with this structure (no backticks, no prose outside JSON):
{
  "intro": "string",
  "main_content": "string",
  "outro": "string",
  "show_notes": {
    "key_topics": ["string", "..."],
    "resources": ["string", "..."],
    "timestamps": [{"time": "0:00", "topic": "Intro"}, "..."],
    "episode_details": {
      "duration": "string",
      "category": "string",
      "format": "string"
    }
  }
}
"""

def build_llm_prompt(content: str, style: str, duration: str, show_name: str) -> str:
    return f"""
You are a senior podcast writer. Create an engaging, well-structured podcast script.

Style: {style}
Target duration: {duration} minutes
Show name: {show_name}

Content to base on (keep it faithful, concise, and natural):
\"\"\"{content[:5000]}\"\"\"

Include music cues like [INTRO MUSIC FADES IN] and [TRANSITION].
Follow this schema strictly:
{SYSTEM_JSON_SCHEMA}
""".strip()


def local_fallback_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    first = (content.split(".")[0] + ".").strip() if "." in content else content[:140] + "..."
    topics = extract_key_topics(content)
    details = EpisodeDetails(
        duration=f"~{duration} minutes",
        category="General",
        format=style.title(),
    )
    intro = f"""[INTRO MUSIC FADES IN]
Welcome to {show_name}! {first}
[TRANSITION MUSIC]
Let's explore the key ideas in a clear, friendly way."""
    main = """We'll break it down into three parts:
1) Context & background
2) What’s happening and why it matters
3) What to watch next

[TRANSITION]
Here are the essential insights, explained simply and precisely."""
    outro = f"""[OUTRO MUSIC FADES IN]
Thanks for listening to {show_name}. If this helped, share it with a friend!
[OUTRO MUSIC FADES OUT]"""

    notes = ShowNotes(
        key_topics=topics,
        resources=["Episode transcript available", "Follow us for updates"],
        timestamps=[
            {"time": "0:00", "topic": "Intro"},
            {"time": "1:30", "topic": "Main discussion"},
            {"time": "4:00", "topic": "Outro"},
        ],
        episode_details=details,
    )
    return GeneratedScript(intro=intro, main_content=main, outro=outro, show_notes=notes)


def generate_script(content: str, style: str, duration: str, show_name: str) -> GeneratedScript:
    """Try Gemini → parse JSON → fallback if anything fails."""
    llm_text = try_gemini_generate(build_llm_prompt(content, style, duration, show_name))
    if llm_text:
        # Strip code fences if any
        llm_text = llm_text.strip()
        if llm_text.startswith("```"):
            llm_text = re.sub(r"^```(?:json)?", "", llm_text).strip()
            llm_text = re.sub(r"```$", "", llm_text).strip()
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
                intro=data["intro"],
                main_content=data["main_content"],
                outro=data["outro"],
                show_notes=notes,
            )
        except Exception:
            pass  # fall through

    # Fallback
    return local_fallback_script(content, style, duration, show_name)


# ===========
# UI Helpers
# ===========

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
    lines = [
        f"{p.title}",
        "",
        "INTRO:",
        s.intro,
        "",
        "MAIN CONTENT:",
        s.main_content,
        "",
        "OUTRO:",
        s.outro,
        "",
        "SHOW NOTES:",
        f"Key Topics: {', '.join(s.show_notes.key_topics)}",
        "",
        "Resources:",
    ]
    lines += [f"• {r}" for r in s.show_notes.resources]
    lines += ["", "Timestamps:"]
    lines += [f"{t['time']} — {t['topic']}" for t in s.show_notes.timestamps]
    lines += [
        "",
        "Episode Details:",
        f"Duration: {s.show_notes.episode_details.duration}",
        f"Category: {s.show_notes.episode_details.category}",
        f"Format: {s.show_notes.episode_details.format}",
    ]
    return "\n".join(lines)


def build_podcast_script(
    content: str,
    input_type: str,
    source_url: Optional[str],
    style: str,
    duration: str,
    show_name: str,
) -> PodcastScript:
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


# =========
# Main View
# =========

hero()
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Input")
    tabs = st.tabs(["✏️ Manual Text", "🔗 URL Import"])

    # --- Manual Text
    with tabs[0]:
        raw_text = st.text_area(
            "Paste text...",
            height=220,
            placeholder="Paste an article, transcript, or notes…",
            label_visibility="collapsed",
        )

    # --- URL Import
    with tabs[1]:
        url = st.text_input(
            "Paste article URL",
            placeholder="https://example.com/great-article",
        )
        fetch_col1, fetch_col2 = st.columns([1, 3])
        with fetch_col1:
            if st.button("Fetch", use_container_width=True, disabled=not url):
                with st.spinner("Fetching & extracting content…"):
                    text = fetch_article(url)
                    if text:
                        st.session_state.fetched = text
                        st.success("✅ Content fetched.")
                    else:
                        st.error("Failed to extract meaningful content from that URL.")

        if st.session_state.fetched:
            with st.expander("Preview fetched content", expanded=False):
                st.caption(f"Characters: {len(st.session_state.fetched)}")
                st.text_area("Preview", st.session_state.fetched[:2000], height=160, label_visibility="collapsed")

    st.markdown("---")

    # --- Options
    st.subheader("⚙️ Options")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        style = st.selectbox("Style", ["conversational", "professional", "educational", "interview"], index=0)
    with c2:
        duration = st.selectbox("Target Duration", ["5-10", "10-20", "20-30", "30+"], index=1)
    with c3:
        show_name = st.text_input("Show Name", value="The Show")

    # Determine content to use
    content = (raw_text or "").strip() or (st.session_state.fetched or "")
    can_generate = len(content) >= 40

    st.markdown("</div>", unsafe_allow_html=True)  # /card

    # --- Generate
    if st.button("⚡ Generate Podcast Script", type="primary", use_container_width=True, disabled=not can_generate):
        with st.spinner("Writing your script…"):
            ps = build_podcast_script(
                content=content,
                input_type="text" if raw_text.strip() else "url",
                source_url=url if (url and not raw_text.strip()) else None,
                style=style,
                duration=duration,
                show_name=show_name.strip() or "The Show",
            )
            st.session_state.history[ps.id] = ps
            st.session_state.current_id = ps.id
            st.success("🎉 Script ready!")

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎬 Generated Script")

    # History selector
    if st.session_state.history:
        ids = list(st.session_state.history.keys())
        nice = [f"{st.session_state.history[i].title} ({st.session_state.history[i].id[:8]})" for i in ids]
        pick = st.selectbox("History", options=list(range(len(ids))), format_func=lambda i: nice[i])
        st.session_state.current_id = ids[pick]

    if st.session_state.current_id:
        script_obj: PodcastScript = st.session_state.history[st.session_state.current_id]
        s = script_obj.script

        t1, t2, t3, t4 = st.tabs(["Intro", "Main", "Outro", "Notes"])

        with t1:
            st.text_area("Intro", s.intro, height=220, label_visibility="collapsed")
        with t2:
            st.text_area("Main", s.main_content, height=220, label_visibility="collapsed")
        with t3:
            st.text_area("Outro", s.outro, height=220, label_visibility="collapsed")
        with t4:
            st.write("**Key Topics:**", ", ".join(s.show_notes.key_topics))
            st.write("**Resources:**")
            for r in s.show_notes.resources:
                st.write(f"• {r}")
            st.write("**Timestamps:**")
            for t in s.show_notes.timestamps:
                st.write(f"**{t['time']}** — {t['topic']}")
            st.write("**Episode Details:**")
            st.write(f"Duration: {s.show_notes.episode_details.duration}")
            st.write(f"Category: {s.show_notes.episode_details.category}")
            st.write(f"Format: {s.show_notes.episode_details.format}")

        st.markdown("---")
        e1, e2 = st.columns(2)
        with e1:
            st.download_button(
                "📄 Export TXT",
                data=script_to_txt(script_obj),
                file_name=f"podcast-{script_obj.id[:8]}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with e2:
            st.download_button(
                "📊 Export JSON",
                data=json.dumps(asdict(script_obj), indent=2),
                file_name=f"podcast-{script_obj.id[:8]}.json",
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.info("👈 Add content and click **Generate** to see your script here.")

    st.markdown("</div>", unsafe_allow_html=True)  # /card

# Footer
st.markdown("---")
st.markdown(
    "<p class='muted' style='text-align:center'>Built with Streamlit • Gemini optional • Local fallback included</p>",
    unsafe_allow_html=True,
)
