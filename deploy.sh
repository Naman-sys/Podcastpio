#!/bin/bash

# Streamlit Cloud Deployment Script for PodcastAI
echo "🚀 Preparing PodcastAI for Streamlit Cloud deployment..."

# Create .streamlit directory if it doesn't exist
mkdir -p .streamlit

# Copy config file to .streamlit directory
cp config.toml .streamlit/config.toml

echo "✅ Configuration files ready for deployment"
echo ""
echo "📋 Deployment checklist:"
echo "1. Push your code to GitHub repository"
echo "2. Go to https://share.streamlit.io"
echo "3. Connect your GitHub repository"
echo "4. Set the main file path to: streamlit_app.py"
echo "5. Add your environment variables:"
echo "   - GEMINI_API_KEY"
echo "   - OPENAI_API_KEY (optional)"
echo "6. Click Deploy!"
echo ""
echo "🌐 Your app will be available at: https://your-app-name.streamlit.app"