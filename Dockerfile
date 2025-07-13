# Dockerfile for cloud deployment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install -r <(grep -E "^[a-zA-Z0-9_-]+=" pyproject.toml | sed 's/.*"\(.*\)".*/\1/')

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p generated static

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]