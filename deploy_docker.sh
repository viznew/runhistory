#!/bin/bash
# Docker deployment script for RunHistory.log Generator

set -e

echo "🚀 Starting Docker deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if API key is provided
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable is required."
    echo "Set it with: export OPENAI_API_KEY=your_key_here"
    exit 1
fi

# Build the Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.cloudrun -t runhistory-generator .

# Test the container
echo "🧪 Testing container..."
docker run -d --name runhistory-test -p 8000:8000 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" \
  runhistory-generator

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed. Check logs:"
    docker logs runhistory-test
    docker stop runhistory-test
    docker rm runhistory-test
    exit 1
fi

# Stop test container
docker stop runhistory-test
docker rm runhistory-test

echo "✅ Docker image built and tested successfully!"
echo "🌐 To run the application:"
echo "docker run -p 8000:8000 -e OPENAI_API_KEY=your_key runhistory-generator"
echo "Then visit: http://localhost:8000"

# Optional: Push to registry
read -p "Do you want to push to Docker Hub? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    docker tag runhistory-generator $DOCKER_USERNAME/runhistory-generator
    docker push $DOCKER_USERNAME/runhistory-generator
    echo "✅ Pushed to Docker Hub: $DOCKER_USERNAME/runhistory-generator"
fi

echo "🎉 Deployment complete!"