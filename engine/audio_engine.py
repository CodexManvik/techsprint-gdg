"""
Local Audio Engine using SpeechRecognition (offline STT)
NO GOOGLE CLOUD DEPENDENCIES
"""
import io
import logging
import speech_recognition as sr


logger = logging.getLogger(__name__)

class AudioEngine:
    def __init__(self):
        """Initialize local speech recognizer"""
        self.recognizer = sr.Recognizer()
        logger.info("Local STT initialized (SpeechRecognition)")
    
    def process_audio(self, audio_bytes):
        """
        Process audio bytes and return transcription using local speech recognition.
        
        Returns:
            dict: {"text": str, "wpm": int|None, "duration_seconds": float, "error": str|None}
        """
        duration_seconds = len(audio_bytes) / float(16000 * 2) if audio_bytes else 0.0

        def _with_metrics(text: str, error: str | None):
            words = len(text.split()) if text else 0
            if words > 0 and duration_seconds > 0:
                wpm = int(round((words / duration_seconds) * 60.0))
                # Keep obvious outliers from skewing analytics on tiny/invalid clips.
                wpm = max(0, min(wpm, 300))
            else:
                wpm = None
            return {
                "text": text,
                "wpm": wpm,
                "duration_seconds": round(duration_seconds, 3),
                "error": error,
            }

        try:
            # Convert bytes to AudioData
            audio_data = sr.AudioData(audio_bytes, sample_rate=16000, sample_width=2)
            
            # Use Sphinx (offline) for speech recognition
            # Falls back to local Whisper if Sphinx not available
            try:
                # Try offline recognition first (requires pocketsphinx)
                text = self.recognizer.recognize_sphinx(audio_data)
                return _with_metrics(text, None)
            except sr.UnknownValueError:
                return _with_metrics("", "Could not understand audio")
            except sr.RequestError:
                # Sphinx not available, try Whisper or fallback
                try:
                    # Try using recognize_whisper if available
                    text = self.recognizer.recognize_whisper(audio_data, model="base")
                    return _with_metrics(text, None)
                except Exception:
                    return _with_metrics("", "Speech recognition not available")
        
        except Exception as e:
            logger.error("Audio processing error: %s", e)
            return _with_metrics("", str(e))
    
    def analyze_audio_quality(self, audio_bytes):
        """Analyze audio quality metrics (placeholder)"""
        return {
            "volume": 0.7,
            "clarity": 0.8,
            "background_noise": 0.2
        }