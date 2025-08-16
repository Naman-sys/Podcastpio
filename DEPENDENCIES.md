# Project Dependencies

## Current Setup: Node.js/React (JSON format)

### Core AI & API Dependencies
```json
"@google/genai": "^1.14.0",              // Google Gemini AI (equivalent to google-generativeai)
"@google/generative-ai": "^0.21.0",      // Alternative Google AI package
"cheerio": "^1.1.2",                     // Web scraping (equivalent to requests + BeautifulSoup)
```

### Frontend Framework
```json
"react": "^18.3.1",                      // UI framework (instead of Streamlit)
"react-dom": "^18.3.1",
"wouter": "^3.3.5",                      // Routing
```

### Backend Framework
```json
"express": "^4.21.2",                    // Server framework
"@types/express": "4.17.21",
```

### Database
```json
"drizzle-orm": "^0.39.1",                // Database ORM
"@neondatabase/serverless": "^0.10.4",   // PostgreSQL provider
```

### UI Components
```json
"@radix-ui/react-*": "^1.x.x",          // UI components
"tailwindcss": "^3.4.17",               // Styling
"lucide-react": "^0.453.0",             // Icons
```

## If You Want Python Equivalent

If you prefer Python instead of the current React/Node.js setup, here would be the equivalent:

### requirements.txt
```
streamlit==1.29.0
google-generativeai==0.8.1
openai==1.6.1
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
pandas==2.1.4
numpy==1.24.3
```

### Python Feature Comparison
| Feature | Current (Node.js) | Python Equivalent |
|---------|-------------------|-------------------|
| AI API | @google/genai | google-generativeai |
| Web Scraping | cheerio | requests + beautifulsoup4 |
| Frontend | React + shadcn/ui | streamlit |
| HTTP Server | Express.js | streamlit server |
| Environment | .env support | python-dotenv |

## Your Current Working Setup

Your podcast generator is fully functional with:
- React frontend with modern UI
- Express.js backend API
- Google Gemini AI integration
- Web content scraping
- Universal port configuration
- Netlify deployment ready

All dependencies are already installed and working. The equivalent of your requested Python packages are:
- `google-generativeai` → `@google/genai` 
- `streamlit` → `react` + `express`
- `requests` → `cheerio` + `fetch API`
- `openai` → Available but using Gemini as primary

No additional installation needed - your app is production ready!