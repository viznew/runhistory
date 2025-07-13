# Manual Deployment Guide - Get Your Code

## How to Access Your Code

### Method 1: Download from Replit (Easiest)

1. **In your Replit workspace**:
   - Click the three dots menu (⋮) in the file explorer
   - Select "Download as ZIP"
   - Extract the ZIP file on your computer

2. **Your code is now on your computer** - you can deploy it anywhere!

### Method 2: Clone via Git

1. **Make your repl public** (if not already)
2. **Get the Git URL**:
   - In Replit, click "Version Control" 
   - Copy the Git URL (looks like: `https://github.com/replit/your-repl-name`)
3. **Clone locally**:
   ```bash
   git clone https://github.com/replit/your-repl-name
   cd your-repl-name
   ```

### Method 3: Copy Files Manually

Copy each file from your Replit workspace to your local machine:

**Main Files You Need:**
- `main.py` (main application)
- `pyproject.toml` (dependencies)
- `services/` folder (all Python files)
- `static/` folder (HTML, CSS, JS)
- `models/` folder (data models)
- `utils/` folder (utilities)

## Deploy to Different Platforms

### Option A: Deploy to Render.com

1. **Upload your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/your-repo
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Go to render.com
   - "New Web Service" → Connect GitHub
   - Select your repository
   - Build Command: `pip install -e .`
   - Start Command: `python main.py`
   - Add environment variable: `OPENAI_API_KEY=your_key_here`

### Option B: Deploy to Railway

1. **Push to GitHub** (same as above)
2. **Deploy on Railway**:
   - Go to railway.app
   - "Deploy from GitHub"
   - Select your repo
   - Add environment variable: `OPENAI_API_KEY`
   - Deploy automatically

### Option C: Deploy to Heroku

1. **Install Heroku CLI**
2. **Create Procfile**:
   ```
   web: python main.py
   ```
3. **Deploy**:
   ```bash
   heroku login
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=your_key_here
   git push heroku main
   ```

### Option D: Deploy to Your Own Server

1. **Upload files to your server**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # or
   pip install fastapi uvicorn openai aiohttp requests pillow pydantic edge-tts
   ```
3. **Set environment variable**:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```
4. **Run the app**:
   ```bash
   python main.py
   ```

## Required Environment Variables

For any deployment, you need:
- `OPENAI_API_KEY` (required for generating scripts and images)
- `ELEVENLABS_API_KEY` (optional, uses free TTS fallback)
- `PORT` (optional, defaults to 8000)

## Files You Need for Deployment

**Essential Files:**
```
main.py
pyproject.toml
services/
├── openai_service.py
├── elevenlabs_service.py
├── video_service.py
└── image_overlay_service.py
models/
└── models.py
utils/
└── file_manager.py
static/
├── index.html
├── script.js
├── style.css
└── og-image.png
```

**Optional Files:**
```
Dockerfile (for Docker deployment)
requirements.txt (alternative to pyproject.toml)
Procfile (for Heroku)
render.yaml (for Render.com)
```

## Quick Test Locally

After downloading your code:
1. `pip install -e .`
2. `export OPENAI_API_KEY=your_key`
3. `python main.py`
4. Visit `http://localhost:8000`

## Your Code is Production-Ready

Your app includes:
- ✅ Proper error handling
- ✅ Health check endpoint
- ✅ Environment variable configuration
- ✅ Static file serving
- ✅ Session management
- ✅ Background task processing
- ✅ Social sharing features

Just download it and deploy anywhere you want!