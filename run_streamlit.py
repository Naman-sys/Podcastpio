#!/usr/bin/env python3
"""
Streamlit runner script for PodcastAI
Handles cross-platform deployment and port configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up environment variables and configuration"""
    
    # Set default port for Streamlit
    # Uses PORT environment variable if available (for cloud deployment)
    # Otherwise uses 8501 (Streamlit default)
    port = os.environ.get("PORT", "8501")
    
    # Ensure the port is properly configured
    os.environ["STREAMLIT_SERVER_PORT"] = port
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    return port

def run_streamlit():
    """Launch the Streamlit application"""
    
    port = setup_environment()
    
    print(f"🚀 Starting PodcastAI on port {port}")
    print(f"🌐 Access the app at: http://0.0.0.0:{port}")
    print("📝 Remember to set your GEMINI_API_KEY environment variable for full functionality!")
    
    # Build the streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        # Run the streamlit app
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down PodcastAI...")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_streamlit()