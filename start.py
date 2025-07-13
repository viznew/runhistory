#!/usr/bin/env python3
"""
Production startup script for RunHistory.log Generator
"""

import os
import sys
import uvicorn
from pathlib import Path
import logging

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup production environment"""
    # Ensure directories exist
    Path("generated").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Set environment variables for production
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("ENVIRONMENT", "production")
    
    logger.info("Environment setup completed")

def main():
    """Main startup function"""
    setup_environment()
    
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting RunHistory.log Generator")
    logger.info(f"Host: {host}, Port: {port}")
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    
    try:
        # Import the app after environment setup
        from main import app
        
        # Run the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()