# Voice Phone Backend API

Voice-first Android phone backend with Groq Whisper transcription.

## Features
- Audio transcription with Indian English support
- Automatic filler word removal
- Fast processing with Groq API

## API Endpoints
- `GET /` - Health check
- `POST /api/v1/transcribe` - Transcribe audio file
- `POST /api/v1/test-command` - Quick command test

## Deployment
Deployed on Render.com with automatic deployments from GitHub.