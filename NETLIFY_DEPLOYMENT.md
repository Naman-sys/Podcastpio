# Netlify Deployment Guide

Your podcast script generator can be deployed on Netlify in two ways:

## Option 1: Static Frontend Only (Recommended for simplicity)

### Quick Setup
1. **Build frontend only:**
   ```bash
   npm run build:frontend
   ```

2. **Deploy to Netlify:**
   - Connect your GitHub repository to Netlify
   - Set build command: `npm run build:frontend`
   - Set publish directory: `dist/public`
   - Add environment variable: `GEMINI_API_KEY`

3. **Configure API endpoint:**
   - The frontend will need to call external API services
   - Consider using Netlify Functions or external backend

## Option 2: Full-Stack with Netlify Functions (Complete solution)

### Features
- ✅ Complete backend functionality
- ✅ Gemini AI integration
- ✅ Serverless functions
- ✅ Environment variables support

### Setup Steps

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Build for Netlify:**
   ```bash
   npm run build:netlify
   ```

3. **Local testing:**
   ```bash
   netlify dev
   ```

4. **Deploy:**
   ```bash
   netlify deploy --prod
   ```

### Environment Variables (Netlify Dashboard)
- `GEMINI_API_KEY` - Your Google Gemini API key
- `NODE_ENV` - Set to "production"

### Build Configuration
The `netlify.toml` file is already configured with:
- Build command: `npm run build:netlify`
- Publish directory: `dist/public`
- Function redirects for API routes
- Security headers
- SPA routing redirects

## File Structure for Netlify

```
├── netlify.toml                 # Netlify configuration
├── netlify/
│   └── functions/
│       └── api.ts              # Serverless API function
├── vite.config.netlify.ts      # Netlify-optimized Vite config
├── client/                     # React frontend
├── dist/
│   └── public/                 # Built frontend assets
└── package.json
```

## API Routes (Netlify Functions)

- `POST /.netlify/functions/api/scripts/generate` - Generate podcast script

## Deployment Commands

Add these to your `package.json` scripts:

```json
{
  "build:frontend": "vite build --config vite.config.netlify.ts",
  "build:netlify": "npm run build:frontend && netlify-lambda build netlify/functions",
  "dev:netlify": "netlify dev"
}
```

## Frontend Configuration

Update your React app to use Netlify API endpoints:

```typescript
// In your API calls
const API_BASE = process.env.NODE_ENV === 'production' 
  ? '/.netlify/functions/api'
  : 'http://localhost:8888/.netlify/functions/api';
```

## Advantages of Netlify Deployment

1. **Free tier available** - Great for testing and small projects
2. **Automatic deployments** - Deploy on git push
3. **Edge functions** - Fast global distribution
4. **Built-in CI/CD** - No additional setup needed
5. **Custom domains** - Easy SSL and domain management
6. **Preview deployments** - Test changes before going live

## Environment Setup

1. **Netlify Dashboard:**
   - Go to Site Settings > Environment Variables
   - Add `GEMINI_API_KEY` with your API key

2. **Local Development:**
   - Create `.env` file with `GEMINI_API_KEY=your_key_here`
   - Use `netlify dev` for local testing

## Troubleshooting

### Common Issues

1. **Build fails:**
   - Check Node.js version (use v20)
   - Verify all dependencies are installed
   - Check build logs for specific errors

2. **API functions not working:**
   - Verify `netlify.toml` redirects are correct
   - Check function logs in Netlify dashboard
   - Ensure environment variables are set

3. **Frontend routing issues:**
   - Verify `_redirects` file or `netlify.toml` redirects
   - Check SPA routing configuration

### Support
- Netlify docs: https://docs.netlify.com/
- Functions guide: https://docs.netlify.com/functions/overview/
- Build troubleshooting: https://docs.netlify.com/configure-builds/troubleshooting-tips/