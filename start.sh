#!/bin/bash
# Simple startup script for deployment

# Ensure directories exist
mkdir -p generated static logs

# Start the application
exec python main.py