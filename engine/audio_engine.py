import speech_recognition as sr
import numpy as np
import io
from pydub import AudioSegment

class AudioEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Calibrate energy threshold to detect softer voices
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True

    def calculate_volume(self, audio_chunk):
        """Calculates volume from pydub AudioSegment"""
        return float(round(audio_chunk.dBFS, 2))

    def process_audio(self, audio_bytes):
        """
        Takes raw bytes (WebM/WAV), converts to PCM WAV, then Transcribes.
        """
        try:
            # 1. CONVERT AUDIO: Browser -> Clean WAV
            # We explicitly tell pydub to read 'webm' (common browser format)
            # or let it auto-detect if the browser sent wav headers.
            try:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            except Exception:
                # Fallback: try raw reading if header is missing
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
            
            # Normalize audio (make it louder if user whispered)
            audio_segment = audio_segment.normalize()
            
            # Export to the format SpeechRecognition loves (Mono, 16kHz, PCM)
            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav", parameters=["-ac", "1", "-ar", "16000"])
            wav_buffer.seek(0) # Reset pointer to start of file

            # 2. LOAD INTO RECOGNIZER
            with sr.AudioFile(wav_buffer) as source:
                # Optional: Adjust for noise in this specific clip
                # self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)

            # 3. GET VOLUME (dB)
            # dBFS is usually negative (0 is max volume, -20 is quiet)
            # We map it to a 0-100 scale for the frontend
            volume_db = audio_segment.dBFS
            volume_score = max(0, min(100, (volume_db + 60) * 2)) # Approx mapping

            # 4. TRANSCRIBE
            text = self.recognizer.recognize_google(audio_data)
            
            # 5. ESTIMATE WPM (Words Per Minute)
            duration_sec = len(audio_segment) / 1000.0
            word_count = len(text.split())
            wpm = int((word_count / duration_sec) * 60) if duration_sec > 0 else 0

            return {
                "text": text,
                "volume": int(volume_score),
                "wpm": wpm,
                "error": None
            }

        except sr.UnknownValueError:
            return {"text": "", "volume": 0, "wpm": 0, "error": "Unclear speech"}
        except Exception as e:
            print(f"Audio Processing Error: {e}")
            return {"text": "", "volume": 0, "wpm": 0, "error": str(e)}