#!/usr/bin/env python3
"""
Test script to verify Google Cloud Audio setup
Run this before starting the app to ensure everything is configured correctly.
"""

import os
import sys

def test_credentials():
    """Check if credentials are set and LOAD them"""
    print("=" * 60)
    print("TESTING GOOGLE CLOUD CREDENTIALS")
    print("=" * 60)
    
    # 1. Check if environment variable is already set
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS is already set")
        print(f"   Path: {creds_path}")
        if os.path.exists(creds_path):
            return True
        else:
            print(f"❌ File not found at {creds_path}")
            return False

    # 2. If not set, look for the file in the project root
    credentials_file = "google_credentials.json"
    if os.path.exists(credentials_file):
        abs_path = os.path.abspath(credentials_file)
        print(f"✅ Found {credentials_file} in project root")
        print(f"   Path: {abs_path}")
        
        # --- CRITICAL FIX: TELL PYTHON TO USE THIS FILE ---
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path
        print("✅ Manually set GOOGLE_APPLICATION_CREDENTIALS for this session")
        return True
    
    # 3. Failure
    print("❌ No credentials found!")
    print("   Place google_credentials.json in project root")
    return False

def test_tts():
    """Test Text-to-Speech connection"""
    print("\n" + "=" * 60)
    print("TESTING TEXT-TO-SPEECH (TTS)")
    print("=" * 60)
    
    try:
        from google.cloud import texttospeech
        
        # Explicitly print what authentication method is being used
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
             print("⚠️  Warning: No credential env var set. Library will look for default credentials.")

        client = texttospeech.TextToSpeechClient()
        print("✅ Google Cloud Text-to-Speech: CONNECTED")
        
        # Test synthesis
        synthesis_input = texttospeech.SynthesisInput(text="Test")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-D", # Trying a premium voice
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        if response.audio_content:
            print("✅ TTS synthesis test: SUCCESS")
            print(f"   Generated {len(response.audio_content)} bytes of audio")
            return True
        else:
            print("❌ TTS synthesis test: FAILED (no audio generated)")
            return False
            
    except ImportError:
        print("❌ google-cloud-texttospeech not installed")
        print("   Run: pip install google-cloud-texttospeech")
        return False
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return False

def test_stt():
    """Test Speech-to-Text connection"""
    print("\n" + "=" * 60)
    print("TESTING SPEECH-TO-TEXT (STT)")
    print("=" * 60)
    
    try:
        from google.cloud import speech
        client = speech.SpeechClient()
        print("✅ Google Cloud Speech-to-Text: CONNECTED")
        
        # Just verify the client initializes
        print("✅ STT client initialization: SUCCESS")
        return True
            
    except ImportError:
        print("❌ google-cloud-speech not installed")
        print("   Run: pip install google-cloud-speech")
        return False
    except Exception as e:
        print(f"❌ STT Error: {e}")
        return False

def test_fallbacks():
    """Test fallback audio libraries"""
    print("\n" + "=" * 60)
    print("TESTING FALLBACK AUDIO LIBRARIES")
    print("=" * 60)
    
    try:
        from gtts import gTTS
        print("✅ gTTS (fallback TTS): Available")
    except ImportError:
        print("❌ gTTS not installed")
    
    try:
        import speech_recognition as sr
        print("✅ SpeechRecognition (fallback STT): Available")
    except ImportError:
        print("❌ SpeechRecognition not installed")

def main():
    print("\n🎤 INTERVIEW MIRROR - GOOGLE CLOUD AUDIO TEST\n")
    
    # Test credentials
    creds_ok = test_credentials()
    
    if creds_ok is False:
        print("\n❌ CRITICAL: No credentials found!")
        sys.exit(1)
    
    # Test Google Cloud services
    tts_ok = test_tts()
    stt_ok = test_stt()
    
    # Test fallbacks
    test_fallbacks()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if tts_ok and stt_ok:
        print("✅ ALL TESTS PASSED! High-quality audio is ready.")
    else:
        print("❌ TESTS FAILED. Check logs above.")

if __name__ == "__main__":
    main()