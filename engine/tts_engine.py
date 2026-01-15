import os
import io
import base64
from google.cloud import texttospeech

# Voice profiles for different personas using Google Cloud TTS
VOICE_PROFILES = {
    "Google_SRE": {"name": "en-US-Neural2-D", "gender": "MALE"},  # Professional
    "Amazon_LP": {"name": "en-US-Neural2-F", "gender": "FEMALE"},  # Authoritative
    "Meta_E5": {"name": "en-US-Neural2-A", "gender": "MALE"},  # Calm
    "Netflix_Architect": {"name": "en-US-Neural2-C", "gender": "FEMALE"},  # Confident
    "Apple_Design": {"name": "en-US-Neural2-E", "gender": "FEMALE"},  # Precise
    "Microsoft_Azure": {"name": "en-US-Neural2-J", "gender": "MALE"},  # Professional
    "Stripe_Infra": {"name": "en-US-Neural2-I", "gender": "MALE"},  # Calm
    "Uber_Backend": {"name": "en-US-Neural2-H", "gender": "FEMALE"},  # Energetic
    "Airbnb_Fullstack": {"name": "en-US-Neural2-G", "gender": "FEMALE"},  # Friendly
    "Startup_Founder": {"name": "en-US-Neural2-D", "gender": "MALE"},  # Dynamic
    "Hedge_Fund_Quant": {"name": "en-GB-Neural2-B", "gender": "MALE"},  # Serious British
    "FAANG_Behavioral": {"name": "en-US-Neural2-C", "gender": "FEMALE"},  # Warm
    "default": {"name": "en-US-Neural2-D", "gender": "MALE"}
}

class TTSEngine:
    def __init__(self):
        self.client = None
        self.current_persona = "default"
        
        try:
            # Try to find google_credentials.json in project root
            credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'google_credentials.json')
            
            if os.path.exists(credentials_path):
                # Set environment variable to use this file
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                print(f"✅ Found credentials at: {credentials_path}")
            
            # Initialize Google Cloud TTS client
            self.client = texttospeech.TextToSpeechClient()
            print("✅ TTS: Google Cloud Text-to-Speech Connected")
        except Exception as e:
            print(f"⚠️ TTS Error: {e}")
            print("ℹ️ Falling back to basic TTS. Place google_credentials.json in project root for better quality.")

    def set_persona(self, persona_key):
        """Set the voice based on the interviewer persona"""
        self.current_persona = persona_key

    def generate_audio(self, text):
        """
        Generates audio from text using Google Cloud TTS and returns a Base64 string.
        Falls back to gTTS if Google Cloud is not available.
        """
        try:
            if self.client:
                # Google Cloud TTS (High Quality)
                voice_profile = VOICE_PROFILES.get(self.current_persona, VOICE_PROFILES["default"])
                
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US" if "GB" not in voice_profile["name"] else "en-GB",
                    name=voice_profile["name"],
                    ssml_gender=getattr(texttospeech.SsmlVoiceGender, voice_profile["gender"])
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.0,
                    pitch=0.0
                )
                
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                return base64.b64encode(response.audio_content).decode('utf-8')
            
            else:
                # Fallback to gTTS (Basic Quality)
                from gtts import gTTS
                tts = gTTS(text=text, lang='en', slow=False)
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                return base64.b64encode(buffer.read()).decode('utf-8')

        except Exception as e:
            print(f"❌ TTS Generation Failed: {e}")
            # Last resort fallback
            try:
                from gtts import gTTS
                tts = gTTS(text=text, lang='en', slow=False)
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                return base64.b64encode(buffer.read()).decode('utf-8')
            except:
                return None