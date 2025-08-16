"""
Podcast Script Generator - Streamlit Application
A Python + Streamlit app that converts content into professional podcast scripts using Google Gemini AI

Setup Instructions:
1. Install dependencies: pip install -r python_requirements.txt
2. Set up your GEMINI_API_KEY environment variable
3. Run the app: streamlit run app.py

For Replit deployment:
- The app uses os.environ.get("PORT") for flexible port configuration
- Compatible with cloud deployment platforms (Render, Railway, Hugging Face Spaces)
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
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure Google Gemini API
def get_gemini_api_key():
    """Get Gemini API key from environment or user input"""
    # First try environment variable
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key
    
    # Then check session state
    if 'gemini_api_key' in st.session_state and st.session_state.gemini_api_key:
        return st.session_state.gemini_api_key
    
    return None

def configure_gemini_api(api_key: str):
    """Configure Gemini API with the provided key"""
    if api_key and GENAI_AVAILABLE and genai:
        try:
            genai.configure(api_key=api_key)  # type: ignore
            return True
        except Exception as e:
            st.error(f"Failed to configure Gemini API: {str(e)}")
            return False
    return False

# Data models
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

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'generated_scripts' not in st.session_state:
        st.session_state.generated_scripts = {}
    if 'current_script' not in st.session_state:
        st.session_state.current_script = None
    if 'fetched_content' not in st.session_state:
        st.session_state.fetched_content = None

# Gemini Service Functions
def generate_fallback_script(content: str, style: str, duration: str, show_name: str = "The Show") -> GeneratedScript:
    """Generate a fallback script when Gemini API is unavailable"""
    
    # Extract key themes and topics from content
    words = content.lower().split()
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 10]
    first_sentence = sentences[0] if sentences else "Welcome to today's discussion."
    
    # Determine category based on content keywords
    category = "General"
    if any(word in words for word in ["technology", "tech", "ai", "digital", "software"]):
        category = "Technology"
    elif any(word in words for word in ["business", "market", "company", "finance", "economy"]):
        category = "Business"
    elif any(word in words for word in ["health", "medical", "wellness", "fitness", "nutrition"]):
        category = "Health"
    elif any(word in words for word in ["education", "learning", "school", "university", "study"]):
        category = "Education"
    elif any(word in words for word in ["science", "research", "study", "discovery", "experiment"]):
        category = "Science"
    
    # Extract key topics (most frequent meaningful words)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", 
                  "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", 
                  "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", 
                  "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"}
    
    meaningful_words = [w for w in words if len(w) > 4 and w not in stop_words]
    word_freq = {}
    for word in meaningful_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    key_topics = [word.capitalize() for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]]
    if not key_topics:
        key_topics = ["Analysis", "Discussion", "Insights"]
    
    # Style-specific formatting
    style_formats = {
        "conversational": {
            "intro_tone": "friendly and welcoming",
            "transition_phrase": "So let's dive in",
            "host_voice": "casual and engaging"
        },
        "professional": {
            "intro_tone": "authoritative and polished",
            "transition_phrase": "Let's examine this in detail",
            "host_voice": "professional and informative"
        },
        "educational": {
            "intro_tone": "knowledgeable and approachable",
            "transition_phrase": "Today we'll learn about",
            "host_voice": "educational and clear"
        },
        "interview": {
            "intro_tone": "curious and engaging",
            "transition_phrase": "Our guest today brings unique insights",
            "host_voice": "inquisitive and thoughtful"
        }
    }
    
    format_info = style_formats.get(style, style_formats["conversational"])
    
    # Generate realistic intro
    intro = f"""[INTRO MUSIC FADES IN]

Welcome to {show_name}! I'm your host, and today we're diving into a fascinating topic that's sure to capture your attention.

[MUSIC FADES TO BACKGROUND]

{first_sentence} This is exactly the kind of story that deserves our attention, and I'm excited to break it down for you in today's episode.

[MUSIC FADES OUT]

{format_info['transition_phrase']}, and explore what this means for all of us. Grab your coffee, settle in, and let's get started."""

    # Generate main content with natural breaks
    content_chunks = sentences[1:min(len(sentences), 8)]
    main_content = f"""Now, let me walk you through the key points of this story.

[TRANSITION MUSIC - 3 SECONDS]

First, let's establish the context. {content_chunks[0] if content_chunks else "We're looking at a development that has significant implications."}

{content_chunks[1] if len(content_chunks) > 1 else "The details are quite compelling when you examine them closely."} This brings us to an important consideration that affects how we should interpret these findings.

[TRANSITION MUSIC - 3 SECONDS]

What's particularly interesting is how this connects to broader trends we've been seeing. {content_chunks[2] if len(content_chunks) > 2 else "The patterns are becoming clearer as more information emerges."}

Let me break down the key implications:

{chr(10).join([f"{i + 1}. {chunk}" for i, chunk in enumerate(content_chunks[3:6])])}

[TRANSITION MUSIC - 3 SECONDS]

Now, you might be wondering what this means for the future. {content_chunks[6] if len(content_chunks) > 6 else "The trajectory suggests several possible outcomes that are worth monitoring."} 

This is where things get really interesting, and why I wanted to share this story with you today."""

    # Generate outro
    outro = f"""[OUTRO MUSIC FADES IN]

So, what's the takeaway from all of this? I think the key insight is that {key_topics[0] if key_topics else "this topic"} continues to evolve in ways that demand our attention.

As we wrap up today's episode, I encourage you to think about how this might impact your own perspective on {key_topics[1] if len(key_topics) > 1 else "related matters"}.

[MUSIC BUILDS]

Thanks for joining me on {show_name}. If you enjoyed today's discussion, don't forget to subscribe and share this episode with friends who might find it interesting.

Next time, we'll be exploring another compelling story, so make sure you're subscribed so you don't miss it.

Until then, keep questioning, keep learning, and I'll see you in the next episode.

[OUTRO MUSIC FADES OUT]"""

    # Generate timestamps based on estimated duration
    duration_map = {"5-10": 8, "10-20": 15, "20-30": 25, "30+": 35}
    estimated_duration = duration_map.get(duration, 15)
    
    timestamps = [
        {"time": "0:00", "topic": "Introduction"},
        {"time": "1:30", "topic": "Topic Overview"},
        {"time": f"{int(estimated_duration * 0.2)}:00", "topic": "Key Points Analysis"},
        {"time": f"{int(estimated_duration * 0.5)}:00", "topic": "Main Discussion"},
        {"time": f"{int(estimated_duration * 0.8)}:00", "topic": "Implications & Takeaways"},
        {"time": f"{estimated_duration - 2}:00", "topic": "Wrap-up & Next Episode"}
    ]

    show_notes = ShowNotes(
        key_topics=key_topics,
        resources=[
            "Episode transcript available on our website",
            "Follow us on social media for updates",
            "Submit topic suggestions via our contact form"
        ],
        timestamps=timestamps,
        episode_details=EpisodeDetails(
            duration=f"~{duration.replace('+', '')} minutes",
            category=category,
            format="Interview Style" if style == "interview" else "Solo Commentary"
        )
    )

    return GeneratedScript(
        intro=intro,
        main_content=main_content,
        outro=outro,
        show_notes=show_notes
    )

def generate_podcast_script_with_gemini(content: str, style: str, duration: str, show_name: str = "The Show") -> GeneratedScript:
    """Generate podcast script using Google Gemini API"""
    
    system_prompt = f"""You are a professional podcast script writer. Create an engaging, well-structured podcast script based on the provided content. 

Style: {style}
Target Duration: {duration} minutes
Show Name: {show_name}

The script should include:
1. A compelling intro that hooks the audience
2. Well-structured main content with natural transitions
3. A strong outro with call-to-action
4. Comprehensive show notes

Format the response as JSON with this exact structure:
{{
  "intro": "Complete intro segment with host dialogue and music cues",
  "main_content": "Main content with segments and transitions",
  "outro": "Outro segment with wrap-up and next episode teaser",
  "show_notes": {{
    "key_topics": ["topic1", "topic2"],
    "resources": ["resource1", "resource2"],
    "timestamps": [{{"time": "0:00", "topic": "Introduction"}}],
    "episode_details": {{
      "duration": "~20 minutes",
      "category": "Technology",
      "format": "Solo Commentary"
    }}
  }}
}}

Make the script conversational, engaging, and professional. Include music cues like [INTRO MUSIC FADES IN] and [TRANSITION MUSIC]. Ensure natural flow between segments."""

    try:
        api_key = get_gemini_api_key()
        if not api_key or not GENAI_AVAILABLE or not genai:
            raise Exception("Gemini API key not found or library not available")
        
        # Configure API with current key
        if not configure_gemini_api(api_key):
            raise Exception("Failed to configure Gemini API")
            
        model = genai.GenerativeModel('gemini-1.5-pro')  # type: ignore
        response = model.generate_content(
            f"{system_prompt}\n\nContent: {content}",
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        
        if not response.text:
            raise Exception("Empty response from Gemini API")
        
        script_data = json.loads(response.text)
        
        # Parse the response into our data structure
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
        st.warning(f"Gemini API unavailable ({str(e)}). Using fallback script generation...")
        return generate_fallback_script(content, style, duration, show_name)

def fetch_content_from_url(url: str) -> Dict[str, Any]:
    """Fetch and extract content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "aside"]):
            script.decompose()
        
        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string
        elif soup.h1:
            title = soup.h1.get_text()
        else:
            title = "Untitled Article"
        
        # Try different selectors for main content
        content = ""
        content_selectors = [
            'article', 'main', '.content', '.article-content', '.post-content',
            '.entry-content', '#content', '.story-body', '.article-body'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text().strip()) > 100:
                content = element.get_text().strip()
                break
        
        # Fallback to body content if no specific content area found
        if not content:
            content = soup.body.get_text().strip() if soup.body else soup.get_text().strip()
        
        # Clean up the content
        content = ' '.join(content.split())  # Replace multiple spaces with single space
        
        if len(content) < 50:
            raise Exception("Could not extract meaningful content from the URL")
        
        word_count = len(content.split())
        
        return {
            "title": title.strip(),
            "content": content,
            "word_count": word_count
        }
        
    except Exception as e:
        raise Exception(f"Failed to fetch content from URL: {str(e)}")

# Streamlit UI Functions
def display_navigation():
    """Display the navigation header"""
    st.markdown("""
    <style>
    .nav-container {
        background-color: #1f2937;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .nav-title {
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
    }
    .nav-subtitle {
        color: #9ca3af;
        font-size: 0.875rem;
        margin: 0;
    }
    </style>
    
    <div class="nav-container">
        <div>
            <h1 class="nav-title">🎙️ PodcastAI</h1>
            <p class="nav-subtitle">Transform Content into Professional Podcasts</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_hero_section():
    """Display the hero section"""
    st.markdown("""
    <style>
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .hero-subtitle {
        font-size: 1.125rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    .hero-highlight {
        color: #fbbf24;
    }
    </style>
    
    <div class="hero-container">
        <h1 class="hero-title">
            Transform Content into<br>
            <span class="hero-highlight">Professional Podcasts</span>
        </h1>
        <p class="hero-subtitle">
            AI-powered tool that converts transcripts and articles into polished podcast scripts
            with intro/outro segments, show notes, and seamless transitions.
        </p>
    </div>
    """, unsafe_allow_html=True)

# def display_workflow_progress(current_step: int = 1):
#     """Display workflow progress indicator"""
#     steps = ["Input Content", "AI Processing", "Export Script"]
    
#     progress_html = """
#     <style>
#     .workflow-container {
#         display: flex;
#         justify-content: center;
#         align-items: center;
#         margin: 2rem 0;
#         padding: 1rem;
#     }
#     .workflow-step {
#         display: flex;
#         align-items: center;
#         margin: 0 1rem;
#     }
#     .step-circle {
#         width: 2rem;
#         height: 2rem;
#         border-radius: 50%;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         font-weight: bold;
#         margin-right: 0.5rem;
#     }
#     .step-active {
#         background-color: #3b82f6;
#         color: white;
#     }
#     .step-inactive {
#         background-color: #e5e7eb;
#         color: #6b7280;
#     }
#     .step-connector {
#         width: 3rem;
#         height: 2px;
#         background-color: #e5e7eb;
#         margin: 0 1rem;
#     }
#     </style>
    
#     <div class="workflow-container">
#     """
    
#     for i, step in enumerate(steps, 1):
#         is_active = i <= current_step
#         circle_class = "step-active" if is_active else "step-inactive"
        
#         progress_html += f"""
#         <div class="workflow-step">
#             <div class="step-circle {circle_class}">{i}</div>
#             <span style="color: {'#3b82f6' if is_active else '#6b7280'}">{step}</span>
#         </div>
#         """
        
#         if i < len(steps):
#             progress_html += '<div class="step-connector"></div>'
    
#     progress_html += "</div>"
#     st.markdown(progress_html, unsafe_allow_html=True)

def display_api_setup():
    """Display API key setup and status"""
    with st.container():
        st.subheader("🔑 API Configuration")
        
        current_key = get_gemini_api_key()
        
        # API Key Input
        with st.expander("🔐 Gemini API Key Setup", expanded=not current_key):
            st.write("**Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)**")
            
            api_key_input = st.text_input(
                "Enter your Gemini API Key:",
                type="password",
                value=current_key if current_key else "",
                placeholder="Enter your API key here...",
                help="Your API key is stored securely in this session only"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Update API Key", disabled=not api_key_input):
                    if api_key_input:
                        st.session_state.gemini_api_key = api_key_input
                        if configure_gemini_api(api_key_input):
                            st.success("✅ API key configured successfully!")
                        else:
                            st.error("❌ Failed to configure API key")
                        st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Key"):
                    if 'gemini_api_key' in st.session_state:
                        del st.session_state.gemini_api_key
                    st.rerun()
        
        # API Status Display
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Gemini AI Status:**")
        with col2:
            if current_key:
                st.success("🟢 Connected")
            else:
                st.error("🔴 Not Connected")
        
        if not current_key:
            st.info("💡 **Without an API key:** The app will use fallback script generation with realistic content structure.")

def export_script_as_text(script: PodcastScript) -> str:
    """Export script in text format"""
    if not script.script:
        return "No script content available"
    
    content = f"""{script.title or "Podcast Script"}

INTRO:
{script.script.intro}

MAIN CONTENT:
{script.script.main_content}

OUTRO:
{script.script.outro}

SHOW NOTES:
Key Topics: {', '.join(script.script.show_notes.key_topics)}

Resources:
{chr(10).join([f"• {resource}" for resource in script.script.show_notes.resources])}

Timestamps:
{chr(10).join([f"{ts['time']} - {ts['topic']}" for ts in script.script.show_notes.timestamps])}

Episode Details:
Duration: {script.script.show_notes.episode_details.duration}
Category: {script.script.show_notes.episode_details.category}
Format: {script.script.show_notes.episode_details.format}
"""
    return content

def export_script_as_json(script: PodcastScript) -> str:
    """Export script in JSON format"""
    # Convert dataclass to dict for JSON serialization
    script_dict = {
        "id": script.id,
        "title": script.title,
        "input_content": script.input_content,
        "input_type": script.input_type,
        "source_url": script.source_url,
        "podcast_style": script.podcast_style,
        "target_duration": script.target_duration,
        "show_name": script.show_name,
        "word_count": script.word_count,
        "char_count": script.char_count,
        "created_at": script.created_at.isoformat(),
        "script": asdict(script.script) if script.script else None
    }
    return json.dumps(script_dict, indent=2)

# Main Streamlit App
def main():
    # Configure Streamlit page
    st.set_page_config(
        page_title="PodcastAI - Script Generator",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    init_session_state()
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .stAlert > div {
        background-color: #f3f4f6;
        border-left: 4px solid #3b82f6;
    }
    .element-container iframe {
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display UI sections
    display_navigation()
    display_hero_section()
    # display_workflow_progress(1 if not st.session_state.current_script else 3)
    
    # Main content layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 Input Content")
        
        # Input method tabs
        tab1, tab2 = st.tabs(["✏️ Manual Text", "🔗 URL Import"])
        
        with tab1:
            st.write("**Paste Your Transcript or Article**")
            input_text = st.text_area(
                "Content",
                placeholder="Paste your speech transcript, news article, or any text content here...",
                height=200,
                label_visibility="collapsed"
            )
            
            if input_text:
                word_count = len(input_text.split())
                char_count = len(input_text)
                col_stats1, col_stats2, col_stats3 = st.columns([2, 1, 1])
                with col_stats1:
                    st.caption(f"📊 {word_count} words • {char_count} characters")
                with col_stats3:
                    if st.button("🗑️ Clear", key="clear_text"):
                        st.rerun()
        
        with tab2:
            st.write("**Article or Transcript URL**")
            input_url = st.text_input(
                "URL",
                placeholder="https://example.com/article",
                label_visibility="collapsed"
            )
            
            col_fetch1, col_fetch2 = st.columns([3, 1])
            with col_fetch2:
                if st.button("🔍 Fetch", disabled=not input_url):
                    with st.spinner("Fetching content..."):
                        try:
                            fetched_data = fetch_content_from_url(input_url)
                            st.session_state.fetched_content = fetched_data
                            st.success(f"✅ Fetched {fetched_data['word_count']} words!")
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
            
            # Display fetched content preview
            if st.session_state.fetched_content:
                with st.expander("📰 Fetched Content Preview", expanded=True):
                    st.write(f"**Title:** {st.session_state.fetched_content['title']}")
                    st.text_area(
                        "Preview",
                        st.session_state.fetched_content['content'][:300] + "..." if len(st.session_state.fetched_content['content']) > 300 else st.session_state.fetched_content['content'],
                        height=100,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    st.caption(f"Retrieved {st.session_state.fetched_content['word_count']} words")
                    
                    if st.button("✅ Use This Content"):
                        input_text = st.session_state.fetched_content['content']
                        st.session_state.fetched_content = None
                        st.rerun()
        
        # Advanced Options
        with st.expander("⚙️ Advanced Options", expanded=False):
            col_style, col_duration = st.columns(2)
            
            with col_style:
                podcast_style = st.selectbox(
                    "🎭 Podcast Style",
                    ["conversational", "professional", "educational", "interview"],
                    index=0,
                    format_func=lambda x: x.title()
                )
            
            with col_duration:
                target_duration = st.selectbox(
                    "⏱️ Target Duration",
                    ["5-10", "10-20", "20-30", "30+"],
                    index=1,
                    format_func=lambda x: f"{x} minutes"
                )
            
            show_name = st.text_input(
                "📻 Show Name (Optional)",
                placeholder="Tech Today, News Weekly, etc."
            )
        
        # Generate Script Button
        st.markdown("---")
        content_to_use = input_text if 'input_text' in locals() else (st.session_state.fetched_content['content'] if st.session_state.fetched_content else "")
        
        if st.button(
            "⚡ Generate Podcast Script",
            type="primary",
            disabled=not content_to_use or len(content_to_use.strip()) < 10,
            use_container_width=True
        ):
            if content_to_use and len(content_to_use.strip()) >= 10:
                with st.spinner("🤖 Generating your podcast script..."):
                    try:
                        # Generate script
                        generated_script = generate_podcast_script_with_gemini(
                            content_to_use,
                            podcast_style,
                            target_duration,
                            show_name or "The Show"
                        )
                        
                        # Create PodcastScript object
                        script_id = str(uuid.uuid4())
                        podcast_script = PodcastScript(
                            id=script_id,
                            title=f"{show_name or 'Podcast'} - {datetime.now().strftime('%Y-%m-%d')}",
                            input_content=content_to_use,
                            input_type="text" if 'input_text' in locals() and input_text else "url",
                            source_url=input_url if 'input_url' in locals() else None,
                            script=generated_script,
                            podcast_style=podcast_style,
                            target_duration=target_duration,
                            show_name=show_name,
                            word_count=len(content_to_use.split()),
                            char_count=len(content_to_use),
                            created_at=datetime.now()
                        )
                        
                        # Save to session state
                        st.session_state.generated_scripts[script_id] = podcast_script
                        st.session_state.current_script = script_id
                        st.success("🎉 Script generated successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Generation failed: {str(e)}")
            else:
                st.error("⚠️ Please provide at least 10 characters of content")
    
    with col2:
        # Display API Configuration
        display_api_setup()
        
        # Display Generated Script
        if st.session_state.current_script and st.session_state.current_script in st.session_state.generated_scripts:
            script = st.session_state.generated_scripts[st.session_state.current_script]
            
            st.markdown("### 🎬 Generated Script")
            
            # Script sections tabs
            script_tab1, script_tab2, script_tab3, script_tab4 = st.tabs(["🎬 Intro", "📖 Main", "🎬 Outro", "📋 Notes"])
            
            with script_tab1:
                st.text_area("Intro Section", script.script.intro, height=200, disabled=True, label_visibility="collapsed")
            
            with script_tab2:
                st.text_area("Main Content", script.script.main_content, height=200, disabled=True, label_visibility="collapsed")
            
            with script_tab3:
                st.text_area("Outro Section", script.script.outro, height=200, disabled=True, label_visibility="collapsed")
            
            with script_tab4:
                st.write("**🏷️ Key Topics:**")
                st.write(", ".join(script.script.show_notes.key_topics))
                
                st.write("**📚 Resources:**")
                for resource in script.script.show_notes.resources:
                    st.write(f"• {resource}")
                
                st.write("**⏰ Timestamps:**")
                for timestamp in script.script.show_notes.timestamps:
                    st.write(f"**{timestamp['time']}** - {timestamp['topic']}")
                
                st.write("**📺 Episode Details:**")
                details = script.script.show_notes.episode_details
                st.write(f"Duration: {details.duration}")
                st.write(f"Category: {details.category}")
                st.write(f"Format: {details.format}")
            
            # Action buttons
            st.markdown("---")
            col_actions1, col_actions2, col_actions3 = st.columns(3)
            
            with col_actions1:
                # Copy to clipboard (simplified for Streamlit)
                full_script = export_script_as_text(script)
                st.download_button(
                    "📋 Copy Script",
                    full_script,
                    file_name=f"podcast-script-{script.id[:8]}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_actions2:
                st.download_button(
                    "📄 Export TXT",
                    export_script_as_text(script),
                    file_name=f"podcast-script-{script.id[:8]}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_actions3:
                st.download_button(
                    "📊 Export JSON",
                    export_script_as_json(script),
                    file_name=f"podcast-script-{script.id[:8]}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        else:
            st.info("👈 **Generate a script to see it here!**\n\nEnter your content on the left and click 'Generate Podcast Script' to get started.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 1rem;">
        <p>🎙️ <strong>PodcastAI</strong> - Transform any content into professional podcast scripts</p>
        <p><small>Built with Streamlit • Powered by Google Gemini AI</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
