
# Quick Manual Deployment Steps

## Replit Manual Deployment (Recommended)

1. Go to Deploy tab → Create Deployment → Custom
2. Configure:
   - Run Command: python main.py
   - Port: 8000
   - Health Check: /health
   - Build Command: mkdir -p generated static logs

3. Add Environment Variables:
   - PORT: 8000
   - PYTHONUNBUFFERED: 1
   - DEPLOYMENT_ENV: production
   - OPENAI_API_KEY: [your key]
   - ELEVENLABS_API_KEY: [optional]

4. Click Deploy

## Alternative: Other Platforms

### Render.com
- render.yaml created ✓
- Connect GitHub repo
- Auto-deploys on push

### Railway.app  
- railway.toml created ✓
- Connect repo
- One-click deploy

### Heroku
- Procfile created ✓
- Use Git deployment
- Add buildpacks if needed

Your app is ready for manual deployment!
