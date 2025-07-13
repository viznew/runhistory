# RunHistory.log Generator

## Overview

The RunHistory.log Generator is an AI-powered web application that creates historical educational videos from user-provided topics. The system generates scripts, images, voiceovers, and assembles them into complete video content using multiple AI services.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI (Python) - chosen for its async capabilities and automatic API documentation
- **Architecture Pattern**: Service-oriented with clear separation of concerns
- **API Design**: RESTful endpoints with background task processing for long-running operations

### Frontend Architecture
- **Technology**: Vanilla JavaScript with Bootstrap 5 for UI components
- **Pattern**: Single-page application with real-time status updates
- **Communication**: Fetch API for HTTP requests with polling for status updates

### Processing Pipeline
The application follows a sequential pipeline:
1. Script generation (OpenAI GPT-4o)
2. Image generation (OpenAI DALL-E)
3. Voiceover generation (ElevenLabs with TTSMaker fallback)
4. Video assembly (FFmpeg)

## Key Components

### Core Services
- **OpenAIService**: Handles script generation and image creation using GPT-4o and DALL-E
- **ElevenLabsService**: Manages text-to-speech with automatic fallback to TTSMaker
- **VideoService**: Assembles final videos using FFmpeg
- **FileManager**: Handles file operations and session management

### Data Models
- **VideoRequest**: Input validation for user topics
- **GenerationStatus**: Real-time progress tracking
- **VideoResponse**: API response structure
- Supporting models for internal service communication

### Session Management
- UUID-based session tracking
- Temporary file storage in generated/ directory
- Background task processing for non-blocking operations

## Data Flow

1. **User Input**: Historical topic submitted via web form
2. **Session Creation**: Unique session ID generated, status tracking initialized
3. **Script Generation**: OpenAI creates educational script with image prompts
4. **Image Generation**: DALL-E creates visual content based on prompts
5. **Voiceover Creation**: ElevenLabs generates audio narration
6. **Video Assembly**: FFmpeg combines images and audio into final video
7. **Delivery**: User receives downloadable video file

### Status Tracking
Real-time progress updates through polling mechanism:
- `initializing` → `generating_script` → `generating_images` → `generating_voiceover` → `creating_video` → `completed`

## External Dependencies

### Required APIs
- **OpenAI API**: Script generation (GPT-4o) and image generation (DALL-E)
- **ElevenLabs API**: Primary text-to-speech service
- **TTSMaker API**: Fallback text-to-speech service

### System Dependencies
- **FFmpeg**: Video processing and assembly
- **aiohttp**: Async HTTP client for API calls
- **uvicorn**: ASGI server for FastAPI

### Environment Variables
- `OPENAI_API_KEY` (required)
- `ELEVENLABS_API_KEY` (optional, uses TTSMaker fallback)

## Deployment Strategy

### Local Development
- Direct Python execution with uvicorn
- Static file serving through FastAPI
- File-based session storage

### Production Considerations
- Requires FFmpeg installation
- Session cleanup for storage management
- API rate limiting considerations
- Potential database integration for session persistence

### File Management
- Session-based temporary storage
- Automatic cleanup mechanisms needed
- Generated assets stored in structured directories

### Deployment Configuration
- **Health Check**: Enhanced `/health` endpoint with robust error handling and system status checks
- **Port Configuration**: Environment variable support for production PORT with proper logging
- **Replit Configuration**: Updated replit.yaml with health check timeouts and intervals
- **Error Handling**: Added comprehensive logging and error handling for deployment debugging
- **Date**: January 2025 - Fixed deployment issues for cloud deployment
- **Date**: July 2025 - Enhanced health check robustness and deployment configuration
- **Date**: July 2025 - Added text overlay system and improved image prompts with contextual information
- **Date**: July 2025 - Deployment optimization: batch processing, memory management, rate limiting, reduced size to 240MB
- **Date**: July 2025 - Fixed deployment timeout issue: extended health check timeout to 300s, improved health endpoint

## Technical Decisions

### API Choice Rationale
- **OpenAI GPT-4o**: Latest model for high-quality script generation
- **ElevenLabs**: Professional voice synthesis with TTSMaker fallback for reliability
- **FFmpeg**: Industry standard for video processing

### Architecture Benefits
- **Async Processing**: Non-blocking operations for better user experience
- **Service Isolation**: Easy to maintain and test individual components
- **Fallback Systems**: Graceful degradation when services fail
- **Session Management**: Supports concurrent users without conflicts

### Scalability Considerations
- Background task processing prevents blocking
- Stateless design (except for session tracking)
- File-based storage can be replaced with cloud storage
- Service-oriented architecture allows for microservice migration