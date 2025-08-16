#!/usr/bin/env python3
"""
Local runner for PodcastAI Script Generator
Run this file to start the Streamlit app locally
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    requirements = [
        "streamlit==1.29.0",
        "google-generativeai==0.3.2", 
        "openai==1.6.1",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "python-dotenv==1.0.0"
    ]
    
    print("Installing required packages...")
    for req in requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", req])
    print("✅ All packages installed successfully!")

def main():
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Please create one based on .env.example")
        print("Add your API keys to the .env file:")
        print("GEMINI_API_KEY=your_actual_api_key")
        print("OPENAI_API_KEY=your_actual_api_key (optional)")
        print()
    
    # Install requirements
    try:
        install_requirements()
    except Exception as e:
        print(f"Failed to install requirements: {e}")
        return
    
    # Start Streamlit app
    print("🚀 Starting PodcastAI Script Generator...")
    print("🌐 Open your browser to: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

if __name__ == "__main__":
    main()