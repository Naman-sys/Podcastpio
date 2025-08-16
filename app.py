"""
PodcastAI — Streamlit App (Extended Output)
-------------------------------------------
• Generates longer, more detailed podcast scripts.
• Uses Google Gemini API if available (with higher token limit).
• Fallback is enhanced with multi-paragraph output.
"""

from __future__ import annotations
import os, re, json, uuid, html, requests
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st
from bs4 import BeautifulSoup

# =====================
# Page Config & Styles
# =====================
st.set_page_config(page_title="PodcastAI — Script Generator", page_icon="🎙️", layout="wide")

st.markdown(
    """
<style>
    .stApp { background: #0b1220; color: #e5e7eb; }
    .hero {
        background: linear-gradient(135deg, #6e7cff 0%, #8a5cf6 100%);
        border-radius: 14px; padding: 20px; color: white;
        margin: 10px 0 25px 0; text-align: center;
    }
    .hero h1 { margin: 0; font-size: 2rem; font-weight: 800; }
    .hero p  { margin: 0; opacity: .92; }
    .card {
        background: #121a2b;
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 14px; padding: 16px; margin-bottom: 12px;
    }
    div.stButton>button {
        background: #6e7cff !important; color: white !important;
        border-radius: 10px !important; font-weight: 700;
        padding: .6rem 1rem;
    }
    .muted { color: #94a3b8; font-size: .9rem; }
</style>
""",
    unsafe_allow_html=True,
)

# =====================
# Data Classes
# =====================
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
# Session Init
# =====================
if "history" not in st.session_state:
    st.session_state.history = {}
if "current_id" not in st.session_state:
    st.session_state.current_id = None
if "fetched" not in st.session_state:
    st.session_state.fetched = None

# =====================
# Gemini API
# =====================
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
        resp = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 8192}  # 🔥 increased length
        )
        return getattr(resp, "text", None)
    except Exception:
        return None

# =====================
# Fetch Content
# =====================
def fetch_article(url: str, max_chars=10000):
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

# =====================
# Local Fallback
# =====================
def local_fallback_script(content, style, duration, show_name):
    intro = f"""[INTRO MUSIC FADES IN]
Welcome to {show_name}, your trusted source for deep dives and engaging stories. 
Today’s episode brings you an in-depth discussion filled with insights, stories, and reflections.
"""
    main = f"""[MAIN DISCUSSION]
We’re breaking the topic into three detailed segments:
1. **Background** — setting the stage with essential context.
2. **Key Insights** — uncovering surprising facts, trends, and narratives.
3. **Implications** — why this matters for everyday life and industry.
Each section is designed to keep the conversation flowing naturally, while still being rich in value.
"""
    outro = f"""[OUTRO]
That’s it for today’s episode of {show_name}. We hope you enjoyed the journey and found the insights useful.
Stay tuned for the next one, and don’t forget to subscribe. Until then, take care and keep exploring!
"""
    notes = ShowNotes(
        key_topics=["Background", "Key Insights", "Implications"],
        resources=["Visit our website", "Follow us on socials"],
        timestamps=[
            {"time":"0:00","topic":"Intro"},
            {"time":"2:00","topic":"Main Discussion"},
            {"time":"8:00","topic":"Outro"},
        ],
        episode_details=EpisodeDetails(duration=f"{duration} min", category="General", format=style)
    )
    return GeneratedScript(intro, main, outro, notes)

# =====================
# Script Generator
# =====================
def generate_script(content, style, duration, show_name):
    prompt = f"""
You are a professional podcast script writer. Generate a **long and detailed podcast script**
for a show called "{show_name}". 

Style: {style}  
Target Duration: {duration} minutes  

The script MUST include:  
- A compelling INTRO (at least 2 paragraphs).  
- A MAIN section with **3–5 subsections**, each detailed and conversational.  
- A memorable OUTRO (1–2 paragraphs).  
- Show Notes with key topics, resources, and timestamps.  

Here’s the content to base it on:
{content[:8000]}
"""
    llm_text = try_gemini_generate(prompt)
    if llm_text:
        return GeneratedScript(
            intro=llm_text.split("MAIN")[0] if "MAIN" in llm_text else llm_text[:500],
            main_content=llm_text,
            outro="Thanks for tuning in — see you next episode!",
            show_notes=ShowNotes(
                key_topics=["Deep Dive", "Insights", "Implications"],
                resources=["Follow for updates", "More resources available"],
                timestamps=[{"time":"0:00","topic":"Intro"},{"time":"10:00","topic":"Main"},{"time":"25:00","topic":"Outro"}],
                episode_details=EpisodeDetails(duration=duration, category="General", format=style)
            )
        )
    return local_fallback_script(content, style, duration, show_name)

# =====================
# UI
# =====================
st.markdown('<div class="hero"><h1>🎙️ PodcastAI</h1><p>Create extended podcast scripts with AI</p></div>', unsafe_allow_html=True)

if get_gemini_key():
    st.markdown("<p style='color:#10b981'>🟢 Gemini API Connected</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#ef4444'>🔴 Gemini API Not Configured — using fallback</p>", unsafe_allow_html=True)

left, right = st.columns([1, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Input Content")
    tabs = st.tabs(["✏️ Manual", "🔗 URL"])
    with tabs[0]:
        raw_text = st.text_area("Paste text...", height=200, label_visibility="collapsed")
    with tabs[1]:
        url = st.text_input("Enter URL")
        if st.button("Fetch", disabled=not url):
            text = fetch_article(url)
            if text:
                st.session_state.fetched = text
                st.success("✅ Content fetched")
            else:
                st.error("❌ Couldn’t extract content.")
        if st.session_state.fetched:
            st.text_area("Preview", st.session_state.fetched[:1000], height=150)

    style = st.selectbox("Style", ["conversational","professional","educational","interview"])
    duration = st.selectbox("Duration", ["5-10","10-20","20-30","30+"])
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
        with t2: st.text_area("Main", s.main_content, height=300)
        with t3: st.text_area("Outro", s.outro, height=150)
        with t4: st.write(s.show_notes)

        e1, e2 = st.columns(2)
        with e1: st.download_button("📄 Export TXT", data=s.intro+s.main_content+s.outro, file_name=f"{ps.id}.txt")
        with e2: st.download_button("📊 Export JSON", data=json.dumps(asdict(ps), indent=2), file_name=f"{ps.id}.json")

        st.markdown("### 📊 Quick Episode Summary")
        st.info(f"**Title:** {ps.title}\n\n**Words:** {ps.word_count} | **Characters:** {ps.char_count}\n\n**Target Duration:** {ps.target_duration} minutes")
    else:
        st.info("👈 Add content and generate a script.")
    st.markdown("</div>", unsafe_allow_html=True)
