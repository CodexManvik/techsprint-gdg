"""
Local TTS Engine using pyttsx3 (offline text-to-speech)
NO GOOGLE CLOUD DEPENDENCIES
"""
import base64
import io
import logging
import pyttsx3
import threading


logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self):
        """Initialize local TTS engine with thread safety"""
        self.engine = pyttsx3.init()
        self.current_persona = "default"
        self.lock = threading.Lock()  # Phase 5: Thread-safe access to pyttsx3
        
        # Configure voice properties
        self.engine.setProperty('rate', 160)  # Speed
        self.engine.setProperty('volume', 0.9)  # Volume
        
        # Get available voices
        voices = self.engine.getProperty('voices')
        if voices:
            # Use first available voice (usually system default)
            self.engine.setProperty('voice', voices[0].id)
            logger.info("Local TTS initialized with voice: %s", voices[0].name)
        else:
            logger.warning("No voices found, using system default")
    
    def set_persona(self, persona_key):
        """Set voice parameters based on persona (simplified for local TTS)"""
        self.current_persona = persona_key
        
        # Adjust speaking rate based on persona
        persona_rates = {
            "Google_SRE": 150,
           "Amazon_LP": 155,
            "Meta_E5": 145,
            "Netflix_Architect": 165,
            "default": 160
        }
        rate = persona_rates.get(persona_key, 160)
        self.engine.setProperty('rate', rate)
    
    def generate_audio(self, text):
        """
        Generate audio from text using local TTS.
        Returns base64-encoded WAV audio.
        
        Thread-safe: pyttsx3 is not thread-safe, so we use a lock.
        """
        with self.lock:  # Phase 5: Prevent concurrent TTS calls from crashing
            try:
                # Create a BytesIO buffer
                buffer = io.BytesIO()
                
                # Save to buffer (pyttsx3 saves to file, so we use temp file)
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                    tmp_path = tmp.name
                
                # Generate speech to file
                self.engine.save_to_file(text, tmp_path)
                self.engine.runAndWait()
                
                # Read the file and convert to base64
                with open(tmp_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # Cleanup temp file
                os.remove(tmp_path)
                
                # Return base64 encoded audio
                return base64.b64encode(audio_data).decode('utf-8')
                
            except Exception as e:
                logger.error("Local TTS generation failed: %s", e)
                return None