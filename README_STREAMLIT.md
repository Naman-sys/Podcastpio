# 🎙️ PodcastAI - Python + Streamlit Application

## Overview
A complete refactor of the original React/Express podcast script generator into **Python + Streamlit**, featuring the same UI design, functionality, and Google Gemini AI integration.

## ✨ Features
- **Text & URL Input**: Manual text entry or automatic content fetching from URLs
- **Multiple Podcast Styles**: Conversational, Professional, Educational, Interview
- **AI-Powered Script Generation**: Uses Google Gemini API with intelligent fallback
- **Structured Output**: Professional scripts with intro/main/outro sections
- **Show Notes Generation**: Key topics, resources, timestamps, and episode details
- **Export Functionality**: Download scripts as TXT or JSON format
- **Copy to Clipboard**: Easy sharing and editing capabilities
- **Dark/Light Theme**: Streamlit's built-in theming support
- **Cross-Platform**: Works on Windows, macOS, Linux, Replit, and cloud platforms

## 🚀 Quick Start

### Local Installation
```bash
# 1. Install Python dependencies
pip install -r python_requirements.txt

# 2. Set up your Google Gemini API key (optional but recommended)
export GEMINI_API_KEY="your_api_key_here"

# 3. Run the application
streamlit run app.py

# OR use the custom runner script
python run_streamlit.py
```

### Replit Deployment
1. The application is already configured for Replit
2. Set your `GEMINI_API_KEY` in Replit Secrets
3. Run: `python run_streamlit.py`
4. The app will automatically bind to the correct port

### Cloud Deployment (Render, Railway, Hugging Face Spaces)
1. Deploy the repository to your platform
2. Set `GEMINI_API_KEY` environment variable
3. Use start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. The app automatically detects and uses the `PORT` environment variable

## 📦 Dependencies
Core dependencies are listed in `python_requirements.txt`:
- **streamlit**: Web application framework
- **google-generativeai**: Google Gemini AI integration
- **beautifulsoup4**: HTML parsing for URL content extraction
- **requests**: HTTP requests for content fetching
- **pydantic**: Data validation and serialization
- **python-dotenv**: Environment variable management

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- `PORT`: Application port (automatically detected for cloud deployments)

### Streamlit Configuration
The app includes a `.streamlit/config.toml` file with optimized settings:
- Headless mode for server deployment
- CORS disabled for cloud compatibility
- Custom theme matching the original design
- Performance optimizations

## 🎨 UI/UX Features Maintained
- **Hero Section**: Gradient background with call-to-action buttons
- **Workflow Progress**: Visual steps indicator
- **Tabbed Interface**: Text input vs URL import
- **Advanced Options**: Collapsible settings panel
- **Real-time Feedback**: Word count, character count, loading states
- **Script Sections**: Tabbed view of intro/main/outro/notes
- **Export Options**: Multiple download formats
- **API Status**: Connection indicator for Gemini API

## 🔄 Migration from Original App
This Streamlit version maintains 100% feature parity with the original React/Express application:

### Original Features → Streamlit Equivalent
- ✅ React Components → Streamlit Widgets
- ✅ Express Routes → Python Functions
- ✅ Gemini API Integration → Direct Python SDK
- ✅ URL Content Fetching → BeautifulSoup + Requests
- ✅ Export Functionality → Streamlit Download Buttons
- ✅ Copy to Clipboard → Download as Text
- ✅ Theme Toggle → Streamlit Theme Support
- ✅ Session Management → Streamlit Session State
- ✅ Error Handling → Try/Catch with User Feedback

## 🛠️ Development

### Running in Development Mode
```bash
# Install dependencies
pip install -r python_requirements.txt

# Set environment variables
export GEMINI_API_KEY="your_key_here"

# Run with auto-reload
streamlit run app.py --server.runOnSave true
```

### Testing Without API Key
The application includes a comprehensive fallback script generator that works without the Gemini API:
- Analyzes content for key topics and themes
- Generates realistic podcast scripts with proper structure
- Creates timestamps and show notes
- Maintains all functionality except AI-enhanced content

### Code Structure
```
app.py                  # Main Streamlit application
run_streamlit.py        # Cross-platform runner script
python_requirements.txt # Python dependencies
.streamlit/config.toml  # Streamlit configuration
README_STREAMLIT.md     # This documentation
```

## 🌐 Deployment Examples

### Render
```yaml
# render.yaml
services:
  - type: web
    name: podcastai
    env: python
    buildCommand: "pip install -r python_requirements.txt"
    startCommand: "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
```

### Railway
```json
{
  "build": {
    "commands": ["pip install -r python_requirements.txt"]
  },
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
  }
}
```

### Hugging Face Spaces
Create a `requirements.txt` file (copy from `python_requirements.txt`) and set the Space type to "Streamlit".

## 🔐 Security Features
- Environment variable management for API keys
- Input validation and sanitization
- Safe URL content fetching with timeouts
- Error handling without exposing internal details
- No hardcoded credentials or secrets

## 📱 Cross-Platform Compatibility
- **Windows**: Full compatibility with Python 3.8+
- **macOS**: Native support with all features
- **Linux**: Optimized for server deployments
- **Replit**: Pre-configured for instant deployment
- **Cloud Platforms**: Automatic port detection and binding

## 🎯 Performance Optimizations
- Lazy loading of heavy dependencies
- Efficient session state management
- Streamlined API calls with fallback mechanisms
- Minimal memory footprint
- Fast startup time

## 📚 Additional Resources
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Gemini AI Documentation](https://ai.google.dev/)
- [Original Project Repository](https://github.com/your-repo) (if applicable)

---

**Built with ❤️ using Python + Streamlit • Powered by Google Gemini AI**