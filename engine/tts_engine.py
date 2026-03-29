"""
Neural TTS Engine using Kokoro-82M (StyleTTS2 architecture)

Replaces pyttsx3 with fast, high-quality neural TTS.
Generates audio in <0.3s, CPU-only (no VRAM competition with LLM).
"""
import base64
import io
import logging
import threading
import numpy as np


logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self):
        """Initialize Kokoro TTS engine with graceful fallback."""
        self.pipeline = None
        self.lock = threading.Lock()  # Thread-safe access
        self._load_model()
    
    def _load_model(self):
        """Attempt to load Kokoro with graceful fallback to pyttsx3."""
        try:
            from kokoro import KPipeline
            import soundfile as sf
            self.pipeline = KPipeline(lang_code='a')  # 'a' = American English
            self.soundfile = sf
            logger.info("Kokoro TTS initialized (82M params, <0.3s generation)")
        except ImportError:
            logger.warning("Kokoro not installed. Run: pip install kokoro soundfile")
            logger.info("Falling back to pyttsx3 (slower, lower quality)")
            try:
                import pyttsx3
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 160)
                self.engine.setProperty('volume', 0.9)
                voices = self.engine.getProperty('voices')
                if voices:
                    self.engine.setProperty('voice', voices[0].id)
                logger.info("pyttsx3 TTS initialized (fallback)")
            except Exception as e:
                logger.error("Failed to initialize any TTS engine: %s", e)
        except Exception as e:
            logger.error("Kokoro initialization failed: %s", e)
            logger.info("TTS will not be available")
    
    def set_persona(self, persona_key):
        """Set voice parameters based on persona."""
        # Kokoro voices: af_heart, am_adam, bf_emma, bf_isabella, bm_george, bm_lewis
        # Map personas to voices (simplified - Kokoro has fewer voice options)
        persona_voices = {
            "Google_SRE": "am_adam",
            "Amazon_LP": "bm_lewis",
            "Meta_E5": "am_adam",
            "Netflix_Architect": "bm_george",
            "default": "af_heart"
        }
        self.current_voice = persona_voices.get(persona_key, "af_heart")
        
        # If using pyttsx3 fallback, adjust rate
        if hasattr(self, 'engine') and self.pipeline is None:
            persona_rates = {
                "Google_SRE": 150,
                "Amazon_LP": 155,
                "Meta_E5": 145,
                "Netflix_Architect": 165,
                "default": 160
            }
            rate = persona_rates.get(persona_key, 160)
            self.engine.setProperty('rate', rate)
    
    def generate_audio(self, text: str) -> str | None:
        """
        Generate audio from text using Kokoro or pyttsx3 fallback.
        Returns base64-encoded WAV audio.
        
        Thread-safe: uses lock to prevent concurrent calls.
        """
        with self.lock:
            if self.pipeline is not None:
                return self._generate_kokoro(text)
            elif hasattr(self, 'engine'):
                return self._generate_pyttsx3(text)
            else:
                logger.error("No TTS engine available")
                return None
    
    def _generate_kokoro(self, text: str) -> str | None:
        """Generate audio using Kokoro pipeline."""
        try:
            voice = getattr(self, 'current_voice', 'af_heart')
            generator = self.pipeline(text, voice=voice, speed=1.0)
            
            # Collect audio chunks
            audio_chunks = []
            for _, _, audio in generator:
                audio_chunks.append(audio)
            
            # Combine and encode
            combined = np.concatenate(audio_chunks)
            buf = io.BytesIO()
            self.soundfile.write(buf, combined, 24000, format='WAV')
            buf.seek(0)
            return base64.b64encode(buf.getvalue()).decode('utf-8')
            
        except Exception as e:
            logger.error("Kokoro TTS generation failed: %s", e)
            return None
    
    def _generate_pyttsx3(self, text: str) -> str | None:
        """Generate audio using pyttsx3 fallback (legacy)."""
        try:
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
            logger.error("pyttsx3 TTS generation failed: %s", e)
            return None
