import streamlit as st
import google.generativeai as genai
import openai
import requests
from bs4 import BeautifulSoup
import os
import json
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="PodcastAI - Script Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure APIs
if "GEMINI_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]

class PodcastScriptGenerator:
    def __init__(self):
        self.gemini_model = None
        if "GEMINI_API_KEY" in os.environ:
            try:
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                st.warning(f"Gemini API initialization failed: {e}")
    
    def extract_content_from_url(self, url: str) -> Dict[str, any]:
        """Extract content from a URL using web scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            else:
                title = "Untitled Article"
            
            # Extract main content
            content = ""
            content_selectors = [
                'article', 'main', '.content', '.article-content', 
                '.post-content', '.entry-content', '#content', 
                '.story-body', '.article-body'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element and len(element.get_text().strip()) > 100:
                    content = element.get_text().strip()
                    break
            
            if not content:
                content = soup.get_text().strip()
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'\n\s*\n', '\n\n', content)
            
            if len(content) < 50:
                raise ValueError("Could not extract meaningful content from URL")
            
            word_count = len(content.split())
            
            return {
                "title": title,
                "content": content,
                "word_count": word_count
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch content from URL: {str(e)}")
    
    def generate_fallback_script(self, content: str, style: str, duration: str, show_name: str = "The Show") -> Dict[str, any]:
        """Generate a podcast script using local logic when APIs fail"""
        
        # Analyze content
        words = content.lower().split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip()) > 10]
        first_sentence = sentences[0] if sentences else "Welcome to today's discussion."
        
        # Determine category
        category = "General"
        if any(word in words for word in ["technology", "tech", "ai", "digital", "software"]):
            category = "Technology"
        elif any(word in words for word in ["business", "market", "company", "finance", "economy"]):
            category = "Business"
        elif any(word in words for word in ["health", "medical", "wellness", "fitness"]):
            category = "Health"
        elif any(word in words for word in ["education", "learning", "school", "university"]):
            category = "Education"
        elif any(word in words for word in ["science", "research", "study", "discovery"]):
            category = "Science"
        
        # Extract key topics
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        meaningful_words = [w for w in words if len(w) > 4 and w not in stop_words]
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        key_topics = [word.capitalize() for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]]
        if not key_topics:
            key_topics = ["Analysis", "Discussion", "Insights"]
        
        # Style-specific formatting
        style_formats = {
            "conversational": {"transition": "So let's dive in", "tone": "friendly and welcoming"},
            "professional": {"transition": "Let's examine this in detail", "tone": "authoritative and polished"},
            "educational": {"transition": "Today we'll learn about", "tone": "knowledgeable and approachable"},
            "interview": {"transition": "Our guest today brings unique insights", "tone": "curious and engaging"}
        }
        
        format_style = style_formats.get(style, style_formats["conversational"])
        
        # Generate script sections
        intro = f"""[INTRO MUSIC FADES IN]

Welcome to {show_name}! I'm your host, and today we're diving into a fascinating topic that's sure to capture your attention.

[MUSIC FADES TO BACKGROUND]

{first_sentence} This is exactly the kind of story that deserves our attention, and I'm excited to break it down for you in today's episode.

[MUSIC FADES OUT]

{format_style['transition']}, and explore what this means for all of us. Grab your coffee, settle in, and let's get started."""

        content_chunks = sentences[1:min(len(sentences), 8)]
        main_content = f"""Now, let me walk you through the key points of this story.

[TRANSITION MUSIC - 3 SECONDS]

First, let's establish the context. {content_chunks[0] if content_chunks else "We're looking at a development that has significant implications."}

{content_chunks[1] if len(content_chunks) > 1 else "The details are quite compelling when you examine them closely."} This brings us to an important consideration that affects how we should interpret these findings.

[TRANSITION MUSIC - 3 SECONDS]

What's particularly interesting is how this connects to broader trends we've been seeing. {content_chunks[2] if len(content_chunks) > 2 else "The patterns are becoming clearer as more information emerges."}

Let me break down the key implications:

{chr(10).join([f"{i+1}. {chunk}" for i, chunk in enumerate(content_chunks[3:6]) if chunk])}

[TRANSITION MUSIC - 3 SECONDS]

Now, you might be wondering what this means for the future. {content_chunks[6] if len(content_chunks) > 6 else "The trajectory suggests several possible outcomes that are worth monitoring."} 

This is where things get really interesting, and why I wanted to share this story with you today."""

        outro = f"""[OUTRO MUSIC FADES IN]

So, what's the takeaway from all of this? I think the key insight is that {key_topics[0] if key_topics else "this topic"} continues to evolve in ways that demand our attention.

As we wrap up today's episode, I encourage you to think about how this might impact your own perspective on {key_topics[1] if len(key_topics) > 1 else "related matters"}.

[MUSIC BUILDS]

Thanks for joining me on {show_name}. If you enjoyed today's discussion, don't forget to subscribe and share this episode with friends who might find it interesting.

Next time, we'll be exploring another compelling story, so make sure you're subscribed so you don't miss it.

Until then, keep questioning, keep learning, and I'll see you in the next episode.

[OUTRO MUSIC FADES OUT]"""

        # Generate timestamps
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
        
        return {
            "intro": intro,
            "mainContent": main_content,
            "outro": outro,
            "showNotes": {
                "keyTopics": key_topics,
                "resources": [
                    "Episode transcript available on our website",
                    "Follow us on social media for updates",
                    "Submit topic suggestions via our contact form"
                ],
                "timestamps": timestamps,
                "episodeDetails": {
                    "duration": f"~{duration.replace('+', '')} minutes",
                    "category": category,
                    "format": "Interview Style" if style == "interview" else "Solo Commentary"
                }
            }
        }
    
    def generate_script_with_gemini(self, content: str, style: str, duration: str, show_name: str = "The Show") -> Dict[str, any]:
        """Generate script using Google Gemini AI"""
        
        prompt = f"""You are a professional podcast script writer. Create an engaging, well-structured podcast script based on the provided content.

Style: {style}
Target Duration: {duration} minutes
Show Name: {show_name}

The script should include:
1. A compelling intro that hooks the audience
2. Well-structured main content with natural transitions
3. A strong outro with call-to-action
4. Comprehensive show notes

Content to convert:
{content}

Format the response as JSON with this exact structure:
{{
  "intro": "Complete intro segment with host dialogue and music cues",
  "mainContent": "Main content with segments and transitions",
  "outro": "Outro segment with wrap-up and next episode teaser",
  "showNotes": {{
    "keyTopics": ["topic1", "topic2"],
    "resources": ["resource1", "resource2"],
    "timestamps": [{{"time": "0:00", "topic": "Introduction"}}],
    "episodeDetails": {{
      "duration": "~20 minutes",
      "category": "Technology",
      "format": "Solo Commentary"
    }}
  }}
}}

Make the script conversational, engaging, and professional. Include music cues like [INTRO MUSIC FADES IN] and [TRANSITION MUSIC]. Ensure natural flow between segments."""

        try:
            response = self.gemini_model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            st.warning(f"Gemini API failed: {e}. Using fallback generation.")
            return None
    
    def generate_script_with_openai(self, content: str, style: str, duration: str, show_name: str = "The Show") -> Dict[str, any]:
        """Generate script using OpenAI API"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional podcast script writer. Always respond with valid JSON."},
                    {"role": "user", "content": f"""Create a podcast script for:
Style: {style}
Duration: {duration} minutes
Show: {show_name}
Content: {content[:3000]}

Return JSON with intro, mainContent, outro, and showNotes fields."""}
                ],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            return json.loads(response_text)
            
        except Exception as e:
            st.warning(f"OpenAI API failed: {e}. Using fallback generation.")
            return None
    
    def generate_script(self, content: str, style: str, duration: str, show_name: str = "The Show") -> Dict[str, any]:
        """Main method to generate podcast script with fallback"""
        
        # Try Gemini first
        if self.gemini_model:
            script = self.generate_script_with_gemini(content, style, duration, show_name)
            if script:
                return script
        
        # Try OpenAI as backup
        if openai.api_key:
            script = self.generate_script_with_openai(content, style, duration, show_name)
            if script:
                return script
        
        # Use fallback generation
        return self.generate_fallback_script(content, style, duration, show_name)

def main():
    # Initialize the generator
    generator = PodcastScriptGenerator()
    
    # Sidebar configuration
    st.sidebar.title("🎙️ PodcastAI")
    st.sidebar.markdown("Transform content into professional podcast scripts")
    
    # API Status
    st.sidebar.subheader("API Status")
    gemini_status = "✅ Connected" if generator.gemini_model else "❌ Not configured"
    openai_status = "✅ Connected" if openai.api_key else "❌ Not configured"
    
    st.sidebar.write(f"**Gemini AI:** {gemini_status}")
    st.sidebar.write(f"**OpenAI:** {openai_status}")
    st.sidebar.write("**Fallback:** ✅ Always available")
    
    # Main interface
    st.title("🎙️ PodcastAI Script Generator")
    st.markdown("Transform any content into professional podcast scripts with AI-powered generation and smart fallback.")
    
    # Input method selection
    input_method = st.radio("Choose input method:", ["Direct Text", "URL Import"])
    
    content = ""
    
    if input_method == "Direct Text":
        content = st.text_area(
            "Paste your content here:",
            height=200,
            placeholder="Paste your article, transcript, or any text content here..."
        )
        
        if content:
            word_count = len(content.split())
            st.info(f"📊 {word_count} words • {len(content)} characters")
    
    else:  # URL Import
        url = st.text_input("Enter URL:", placeholder="https://example.com/article")
        
        if url and st.button("Fetch Content"):
            try:
                with st.spinner("Fetching content from URL..."):
                    fetched_data = generator.extract_content_from_url(url)
                    
                st.success(f"✅ Fetched: {fetched_data['title']}")
                st.info(f"📊 {fetched_data['word_count']} words extracted")
                
                # Show preview
                with st.expander("Content Preview"):
                    st.write(f"**Title:** {fetched_data['title']}")
                    st.write(f"**Content:** {fetched_data['content'][:500]}...")
                
                content = fetched_data['content']
                
            except Exception as e:
                st.error(f"Failed to fetch content: {e}")
    
    # Configuration options
    st.subheader("Podcast Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        style = st.selectbox(
            "Podcast Style:",
            ["conversational", "professional", "educational", "interview"]
        )
        
    with col2:
        duration = st.selectbox(
            "Target Duration:",
            ["5-10", "10-20", "20-30", "30+"]
        )
    
    show_name = st.text_input("Show Name (Optional):", placeholder="Tech Today, News Weekly, etc.")
    
    # Generate script
    if st.button("🚀 Generate Podcast Script", type="primary") and content:
        if len(content.strip()) < 10:
            st.error("Please provide at least 10 characters of content.")
        else:
            with st.spinner("Generating your podcast script..."):
                try:
                    script = generator.generate_script(
                        content=content,
                        style=style,
                        duration=duration,
                        show_name=show_name or "The Show"
                    )
                    
                    st.success("✅ Script generated successfully!")
                    
                    # Display script
                    st.subheader("📝 Generated Podcast Script")
                    
                    # Tabs for different sections
                    tab1, tab2, tab3, tab4 = st.tabs(["🎬 Intro", "📖 Main Content", "🎯 Outro", "📋 Show Notes"])
                    
                    with tab1:
                        st.text_area("Intro Segment:", script["intro"], height=200, key="intro")
                        
                    with tab2:
                        st.text_area("Main Content:", script["mainContent"], height=300, key="main")
                        
                    with tab3:
                        st.text_area("Outro Segment:", script["outro"], height=200, key="outro")
                        
                    with tab4:
                        show_notes = script["showNotes"]
                        
                        st.write("**Key Topics:**")
                        for topic in show_notes["keyTopics"]:
                            st.write(f"• {topic}")
                        
                        st.write("**Timestamps:**")
                        for timestamp in show_notes["timestamps"]:
                            st.write(f"• {timestamp['time']} - {timestamp['topic']}")
                        
                        st.write("**Episode Details:**")
                        details = show_notes["episodeDetails"]
                        st.write(f"• Duration: {details['duration']}")
                        st.write(f"• Category: {details['category']}")
                        st.write(f"• Format: {details['format']}")
                        
                        st.write("**Resources:**")
                        for resource in show_notes["resources"]:
                            st.write(f"• {resource}")
                    
                    # Export options
                    st.subheader("📤 Export Script")
                    
                    # Create export text
                    export_text = f"""# {show_name or 'Podcast Script'}

## Intro
{script['intro']}

## Main Content
{script['mainContent']}

## Outro
{script['outro']}

## Show Notes
### Key Topics
{chr(10).join(['• ' + topic for topic in show_notes['keyTopics']])}

### Timestamps
{chr(10).join(['• ' + ts['time'] + ' - ' + ts['topic'] for ts in show_notes['timestamps']])}

### Episode Details
• Duration: {show_notes['episodeDetails']['duration']}
• Category: {show_notes['episodeDetails']['category']}
• Format: {show_notes['episodeDetails']['format']}
"""
                    
                    st.download_button(
                        label="📥 Download as TXT",
                        data=export_text,
                        file_name="podcast_script.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"Failed to generate script: {e}")
    
    elif not content and st.button("🚀 Generate Podcast Script", type="primary"):
        st.error("Please provide content first!")

if __name__ == "__main__":
    main()