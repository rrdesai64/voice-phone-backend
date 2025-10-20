from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.services.transcription import TranscriptionService
import tempfile
import os
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Voice-first phone API with Groq Whisper transcription",
    version="1.0.0"
)

# CORS middleware for mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize transcription service
transcription_service = TranscriptionService(api_key=settings.GROQ_API_KEY)

@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """
    Detailed health check
    """
    return {
        "status": "healthy",
        "groq_api_configured": bool(settings.GROQ_API_KEY),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    remove_fillers: bool = True,
    language: str = "en"
):
    """
    Transcribe audio file with optional filler word removal
    
    - **audio**: Audio file (WAV, MP3, M4A, etc.)
    - **remove_fillers**: Remove filler words like 'um', 'uh', etc.
    - **language**: Language code (default: en)
    """
    # Validate file
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Check file type
    allowed_types = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']
    file_ext = os.path.splitext(audio.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Transcribe
        result = await transcription_service.transcribe(
            temp_path,
            remove_fillers=remove_fillers,
            language=language
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test-command")
async def test_command(audio: UploadFile = File(...)):
    """
    Quick test endpoint - transcribe and return clean command
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        result = await transcription_service.transcribe(temp_path, remove_fillers=True)
        os.unlink(temp_path)
        
        if result["success"]:
            return {
                "command": result["clean_text"],
                "raw": result["raw_text"],
                "confidence": "high" if result["fillers_removed"] < 3 else "medium"
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )