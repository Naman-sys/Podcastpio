# PodcastAI - Streamlit Version

A powerful podcast script generator that converts any content into professional podcast scripts using AI and smart fallback generation.

## Features

🎙️ **AI-Powered Generation**
- Google Gemini AI integration
- OpenAI GPT backup
- Smart local fallback when APIs fail

📝 **Multiple Input Methods**
- Direct text input
- URL content extraction
- Web scraping with BeautifulSoup

🎨 **Customizable Styles**
- Conversational
- Professional
- Educational  
- Interview

⚡ **Robust & Reliable**
- Always generates scripts (even when APIs fail)
- Multiple duration options
- Professional formatting with music cues

## Installation & Setup

### Requirements
Create a `requirements.txt` file with:
```
streamlit==1.29.0
google-generativeai==0.3.2
openai==1.6.1
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
```

### Local Development

1. **Clone and setup:**
```bash
git clone <your-repo>
cd podcast-ai-streamlit
pip install -r requirements.txt
```

2. **Configure API keys:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Run locally:**
```bash
python run_local.py
# OR
streamlit run streamlit_app.py --server.port 8501
```

### Streamlit Cloud Deployment

1. **Push to GitHub:**
```bash
git add .
git commit -m "PodcastAI Streamlit app"
git push origin main
```

2. **Deploy on Streamlit Cloud:**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub repository
- Set main file: `streamlit_app.py`
- Add environment variables:
  - `GEMINI_API_KEY`: Your Google Gemini API key
  - `OPENAI_API_KEY`: Your OpenAI API key (optional)

3. **Deploy:**
```bash
./deploy.sh  # Prepares deployment files
```

## API Keys Setup

### Google Gemini AI (Recommended)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to `.env`: `GEMINI_API_KEY=your_key_here`

### OpenAI (Optional Backup)
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create an API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

## Usage

1. **Choose Input Method:**
   - Direct text input
   - URL import (automatic content extraction)

2. **Configure Podcast:**
   - Select style (conversational, professional, educational, interview)
   - Choose duration (5-10, 10-20, 20-30, 30+ minutes)
   - Set show name (optional)

3. **Generate Script:**
   - Click "Generate Podcast Script"
   - View intro, main content, outro, and show notes
   - Export as text file

## Architecture

- **Frontend**: Streamlit web interface
- **AI Integration**: Google Generative AI + OpenAI backup
- **Fallback System**: Local script generation when APIs fail
- **Web Scraping**: BeautifulSoup for URL content extraction
- **Deployment**: Streamlit Cloud ready

## Configuration

### Port Settings
- **Local**: Port 8501 (configurable)
- **Deployment**: Automatic port assignment

### Environment Variables
- `GEMINI_API_KEY`: Primary AI service
- `OPENAI_API_KEY`: Backup AI service
- `PORT`: Custom port (optional)

## Deployment Options

### 1. Streamlit Cloud (Recommended)
- Free hosting
- Automatic deployments
- Built-in secrets management

### 2. Local Machine
```bash
python run_local.py
```

### 3. Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Features Overview

### Smart Fallback System
When APIs fail, the app automatically:
- Analyzes content for key topics
- Adapts to selected style
- Generates professional scripts
- Creates realistic timestamps
- Maintains full functionality

### Content Analysis
- Automatic category detection
- Key topic extraction
- Word frequency analysis
- Intelligent content structuring

### Export Options
- Plain text download
- Formatted markdown
- Complete show notes
- Timestamp generation

## Troubleshooting

### Common Issues

1. **API Keys not working:**
   - Check `.env` file exists and has correct keys
   - Verify API keys are valid and have quota
   - App will use fallback generation automatically

2. **URL extraction fails:**
   - Some sites block scraping
   - Try copying content manually
   - App provides helpful error messages

3. **Port already in use:**
   - Change port in `run_local.py`
   - Or use: `streamlit run streamlit_app.py --server.port 8502`

### Support
- App always works with fallback generation
- No API keys required for basic functionality
- Professional scripts generated locally when needed