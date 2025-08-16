#!/bin/bash

# Netlify Deployment Script for Podcast Script Generator

echo "🚀 Starting Netlify deployment preparation..."

# Check if required tools are installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build frontend for Netlify
echo "🏗️ Building frontend..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Frontend assets: dist/public/"
    echo "🔧 Netlify functions: netlify/functions/"
    echo ""
    echo "🌐 Deployment options:"
    echo "1. Netlify CLI: netlify deploy --prod"
    echo "2. Connect GitHub repo to Netlify dashboard"
    echo "3. Drag & drop dist/public folder to Netlify"
    echo ""
    echo "📋 Required environment variables:"
    echo "- GEMINI_API_KEY (required for AI script generation)"
    echo ""
    echo "🎯 Build command for Netlify: npm run build"
    echo "📂 Publish directory: dist/public"
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi