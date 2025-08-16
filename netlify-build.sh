#!/bin/bash

# Netlify Build Script for Podcast Generator
# This ensures all dependencies are properly installed before building

echo "Installing dependencies..."
npm ci --legacy-peer-deps

echo "Building frontend with Vite..."
npx vite build --config vite.config.ts

echo "Building backend with ESBuild..."
npx esbuild server/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist

echo "Copying redirects file..."
cp netlify/_redirects dist/public/_redirects

echo "Build complete! Files:"
ls -la dist/public/