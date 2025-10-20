from groq import Groq
import os
from typing import Dict, Optional
import re

class TranscriptionService:
    """
    Handles audio transcription using Groq's Whisper API
    with automatic filler word removal
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        
        # Filler words to remove (Indian English focused)
        self.filler_words = {
            'um', 'uh', 'ah', 'er', 'hmm', 'uhh', 'umm', 'ahh',
            'basically', 'actually', 'like', 'you know', 'i mean',
            'kind of', 'sort of', 'you see', 'right',
        }
    
    async def transcribe(
        self, 
        audio_file_path: str,
        remove_fillers: bool = True,
        language: str = "en"
    ) -> Dict[str, any]:
        """
        Transcribe audio file using Groq Whisper
        
        Args:
            audio_file_path: Path to audio file
            remove_fillers: Whether to remove filler words
            language: Language code (default: en for English)
        
        Returns:
            Dictionary with transcription results
        """
        try:
            # Read audio file
            with open(audio_file_path, "rb") as audio_file:
                # Call Groq Whisper API
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    language=language,
                    response_format="verbose_json",
                    temperature=0.0  # Deterministic output
                )
            
            raw_text = transcription.text
            
            # Remove fillers if requested
            clean_text = self._remove_fillers(raw_text) if remove_fillers else raw_text
            
            return {
                "success": True,
                "raw_text": raw_text,
                "clean_text": clean_text,
                "language": transcription.language,
                "duration": transcription.duration,
                "fillers_removed": len(raw_text.split()) - len(clean_text.split())
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _remove_fillers(self, text: str) -> str:
        """
        Remove filler words from text
        """
        # Convert to lowercase for matching
        cleaned = text.lower()
        
        # Remove filler words
        filler_pattern = r'\b(' + '|'.join(self.filler_words) + r')\b'
        cleaned = re.sub(filler_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove repeated words (stuttering)
        cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', cleaned)
        
        # Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Restore capitalization
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned