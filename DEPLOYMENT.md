# Universal Deployment Guide

This podcast script generator application is configured to run on any platform with automatic port detection.

## Port Configuration

The application automatically detects ports in this priority order:

1. `process.env.PORT` - Primary (used by Replit, Heroku, Railway, etc.)
2. `process.env.SERVER_PORT` - Alternative server port
3. `process.env.HTTP_PORT` - HTTP service port
4. `3000` - Default fallback port

## Platform Support

### ✅ Replit
- Automatic port: `5000` (via PORT environment variable)
- Run: `npm run dev`
- Host: `0.0.0.0` (required for Replit)

### ✅ Heroku
- Automatic port: Dynamic (via PORT environment variable)
- Build: `npm run build`
- Start: `npm start`

### ✅ Railway
- Automatic port: Dynamic (via PORT environment variable)
- Deploy: Connect GitHub repository

### ✅ Vercel
- Serverless deployment with automatic configuration
- Deploy: `vercel --prod`

### ✅ Local Development
- Default port: `3000`
- Override: `PORT=8080 npm run dev`
- Host: `localhost` or `0.0.0.0`

### ✅ Docker
- Configure port mapping: `-p 3000:3000`
- Or use environment: `-e PORT=8080`

## Environment Variables

### Required
- `GEMINI_API_KEY` - Google Gemini AI API key for script generation

### Optional
- `PORT` - Server port (auto-detected on most platforms)
- `NODE_ENV` - Environment mode (`development` or `production`)
- `DATABASE_URL` - PostgreSQL connection (for Neon DB)

## Quick Start Commands

```bash
# Development
npm run dev

# Production build
npm run build
npm start

# Custom port
PORT=8080 npm run dev

# Check types
npm run check

# Database setup
npm run db:push
```

## Features

- 🌐 Universal port detection
- 🚀 Auto-deployment ready
- 🔒 Environment-based secrets
- 📱 Responsive React frontend
- 🤖 AI-powered script generation
- 💾 PostgreSQL database integration
- 🎨 Modern UI with Tailwind CSS

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Express.js + Node.js
- **Database**: PostgreSQL + Drizzle ORM
- **AI**: Google Gemini API
- **Styling**: Tailwind CSS + shadcn/ui
- **Build**: Vite + ESBuild