# Docker Deployment Guide

## Prerequisites

You'll need Docker installed on your system:
- **Windows/Mac**: Docker Desktop
- **Linux**: Docker Engine

## Step 1: Download Project Files

Download all project files to your local machine. The key files you need:

```
runhistory-generator/
├── main.py
├── pyproject.toml
├── Dockerfile.cloudrun
├── services/
├── models/
├── utils/
├── static/
└── generated/ (will be created)
```

## Step 2: Build Docker Image

Open terminal/command prompt in the project directory and run:

```bash
docker build -f Dockerfile.cloudrun -t runhistory-generator .
```

This will:
- Use Python 3.11 slim image
- Install FFmpeg for video processing
- Install Python dependencies
- Copy your application code
- Create necessary directories

## Step 3: Test Locally

Run the container locally to test:

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_openai_key_here \
  -e ELEVENLABS_API_KEY=your_elevenlabs_key_here \
  runhistory-generator
```

**Replace `your_openai_key_here` with your actual OpenAI API key.**

Test the application at: http://localhost:8000

## Step 4: Deploy to Cloud Run

### Option A: Using Google Cloud CLI

1. **Install Google Cloud SDK** from https://cloud.google.com/sdk

2. **Authenticate and set project:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

3. **Configure Docker for Google Cloud:**
```bash
gcloud auth configure-docker
```

4. **Tag and push image:**
```bash
docker tag runhistory-generator gcr.io/YOUR_PROJECT_ID/runhistory-generator
docker push gcr.io/YOUR_PROJECT_ID/runhistory-generator
```

5. **Deploy to Cloud Run:**
```bash
gcloud run deploy runhistory-generator \
  --image gcr.io/YOUR_PROJECT_ID/runhistory-generator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 900 \
  --set-env-vars OPENAI_API_KEY=your_key,ELEVENLABS_API_KEY=your_key
```

### Option B: Using Google Cloud Console

1. **Go to Cloud Run** in Google Cloud Console
2. **Click "Create Service"**
3. **Choose "Deploy one revision from an existing container image"**
4. **Enter image URL:** `gcr.io/YOUR_PROJECT_ID/runhistory-generator`
5. **Configure:**
   - Port: 8000
   - Memory: 2 GiB
   - CPU: 1
   - Timeout: 900 seconds
   - Allow unauthenticated invocations: Yes
6. **Add environment variables:**
   - `OPENAI_API_KEY`: your_key
   - `ELEVENLABS_API_KEY`: your_key (optional)
7. **Click "Create"**

## Step 5: Deploy to Other Platforms

### AWS ECS/Fargate

1. **Push to AWS ECR:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag runhistory-generator:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/runhistory-generator:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/runhistory-generator:latest
```

2. **Create ECS service** with the pushed image

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name runhistory-generator \
  --image runhistory-generator \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=your_key ELEVENLABS_API_KEY=your_key
```

### DigitalOcean App Platform

1. **Push to DigitalOcean Container Registry**
2. **Create app** from container image
3. **Configure environment variables**

## Troubleshooting

### Common Issues

1. **Build fails**: Check if all files are in the correct directory
2. **Container won't start**: Verify environment variables are set
3. **Health check fails**: Test `/health` endpoint locally first
4. **Memory issues**: Increase memory allocation to 2GB or more

### Testing Commands

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test main page
curl http://localhost:8000/

# Check container logs
docker logs runhistory-generator

# Connect to running container
docker exec -it runhistory-generator /bin/bash
```

## Production Considerations

1. **SSL/TLS**: Use HTTPS in production
2. **Scaling**: Configure auto-scaling based on CPU/memory
3. **Monitoring**: Set up logging and monitoring
4. **Security**: Use secrets management for API keys
5. **Backup**: Consider backup strategy for generated content

## Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: 8000 (set automatically by most platforms)

Optional:
- `ELEVENLABS_API_KEY`: For better voice quality
- `DEPLOYMENT_ENV`: production
- `PYTHONUNBUFFERED`: 1

Your Docker deployment is ready! The application is fully containerized and can be deployed to any Docker-compatible platform.