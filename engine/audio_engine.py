"""
GPU-accelerated Audio Engine using faster-whisper for STT

Replaces legacy SpeechRecognition with CTranslate2-optimized Whisper inference.
Provides accurate WPM from word-level timestamps and speech_ratio from VAD filtering.
"""
import logging
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AudioEngine:
    def __init__(self, model_size: str = "base", device: str = "cuda", compute_type: str = "float16"):
        """
        Initialize faster-whisper audio engine with graceful degradation.
        
        Args:
            model_size: Model size - "tiny" (~1GB VRAM), "base" (~1.5GB, recommended), 
                        "small" (~2.5GB), "medium" (~5GB)
            device: "cuda" for GPU, "cpu" for fallback
            compute_type: "float16" for GPU, "int8" for CPU
        """
        self.model = None
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._load_model()

    def _load_model(self):
        """Attempt to load faster-whisper with graceful fallback."""
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(self._model_size, device=self._device, compute_type=self._compute_type)
            logger.info("faster-whisper initialized: model=%s device=%s compute=%s", 
                       self._model_size, self._device, self._compute_type)
        except ImportError:
            logger.error("faster-whisper not installed. Run: pip install faster-whisper")
            logger.warning("Audio transcription will not be available until package is installed")
        except Exception as e:
            logger.warning("GPU init failed (%s), falling back to CPU", e)
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
                logger.info("faster-whisper initialized on CPU (fallback)")
            except Exception as e2:
                logger.error("Failed to initialize faster-whisper: %s", e2)
                logger.warning("Audio transcription will not be available")

    def process_audio(self, audio_bytes: bytes) -> Dict[str, any]:
        """
        Transcribe audio bytes to text with accurate metrics.
        
        Expects 16kHz, mono, 16-bit PCM audio.
        
        Returns:
            dict: {
                "text": str - Transcribed text
                "wpm": int | None - Words per minute (from actual speech duration)
                "duration_seconds": float - Total audio clip duration
                "speech_ratio": float - Fraction of audio that was actual speech (0.0-1.0)
                "error": str | None - Error message if transcription failed
            }
        """
        if self.model is None:
            return {
                "text": "",
                "wpm": None,
                "duration_seconds": 0.0,
                "speech_ratio": 0.0,
                "error": "Audio engine not initialized. Install faster-whisper: pip install faster-whisper"
            }

        if not audio_bytes:
            return {
                "text": "",
                "wpm": None,
                "duration_seconds": 0.0,
                "speech_ratio": 0.0,
                "error": "No audio data"
            }

        try:
            # Convert raw PCM bytes to float32 numpy array (16kHz, 16-bit signed)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            duration_seconds = len(audio_np) / 16000.0

            # Transcribe with VAD filtering and word timestamps
            segments, info = self.model.transcribe(
                audio_np,
                beam_size=5,
                language="en",
                vad_filter=True,  # Remove silence automatically
                vad_parameters={"min_silence_duration_ms": 300},
                word_timestamps=True,
            )

            segments = list(segments)  # Materialize the generator
            full_text = " ".join(s.text.strip() for s in segments).strip()

            # Compute WPM from actual speech duration (VAD-filtered), not total clip length
            speech_duration = sum(s.end - s.start for s in segments)
            speech_ratio = (speech_duration / duration_seconds) if duration_seconds > 0 else 0.0

            word_count = len(full_text.split()) if full_text else 0
            if word_count > 0 and speech_duration > 0:
                wpm = int(round((word_count / speech_duration) * 60.0))
                wpm = max(0, min(wpm, 350))  # Cap outliers (normal speech is 100-200 WPM)
            else:
                wpm = None

            return {
                "text": full_text,
                "wpm": wpm,
                "duration_seconds": round(duration_seconds, 3),
                "speech_ratio": round(speech_ratio, 3),
                "error": None,
            }

        except Exception as e:
            logger.exception("faster-whisper transcription failed")
            return {
                "text": "",
                "wpm": None,
                "duration_seconds": 0.0,
                "speech_ratio": 0.0,
                "error": str(e)
            }

    def analyze_audio_quality(self, audio_bytes: bytes) -> Dict[str, float]:
        """Analyze audio quality metrics (placeholder for backward compatibility)"""
        return {
            "volume": 0.7,
            "clarity": 0.8,
            "background_noise": 0.2
        }
