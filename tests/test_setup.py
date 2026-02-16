"""
Test Script for Ollama + Redis Setup Validation

Run this to verify your local development environment is ready.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.config.settings import settings
from backend.core.llm.ollama import OllamaClient
from backend.core.cache import RedisCache


async def test_ollama():
    """Test Ollama connection and model availability"""
    print("\n🧪 Testing Ollama Connection...")
    print(f"   URL: {settings.OLLAMA_BASE_URL}")
    print(f"   Model: {settings.OLLAMA_MODEL}")
    
    client = OllamaClient()
    
    try:
        # Health check
        healthy = await client.health_check()
        if not healthy:
            print("   ❌ FAILED: Ollama server not responding")
            print(f"   💡 Fix: Run 'ollama serve' in a separate terminal")
            return False
        
        print("   ✅ Ollama server is running")
        
        # Test chat completion
        print("\n   Testing chat completion...")
        messages = [
            {"role": "user", "content": "Say 'Hello from Ollama!' in exactly 5 words."}
        ]
        
        response = await client.chat(messages, stream=False)
        print(f"   Response: {response}")
        print("   ✅ Chat completion works")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        print(f"   💡 Fix: Ensure Ollama is installed and model '{settings.OLLAMA_MODEL}' exists")
        print(f"          Run: ollama pull {settings.OLLAMA_MODEL}")
        await client.close()
        return False


async def test_redis():
    """Test Redis connection"""
    print("\n🧪 Testing Redis Connection...")
    print(f"   URL: {settings.REDIS_URL}")
    print(f"   Enabled: {settings.REDIS_ENABLED}")
    
    if not settings.REDIS_ENABLED:
        print("   ⚠️  Redis is disabled in settings")
        return True
    
    cache = RedisCache()
    
    try:
        await cache.connect()
        
        if not cache.redis:
            print("   ❌ FAILED: Redis connection failed")
            print("   💡 Fix: Start Redis server")
            print("          Windows: redis-server.exe")
            print("          Docker: docker run -d -p 6379:6379 redis")
            return False
        
        print("   ✅ Redis connected")
        
        # Test set/get
        print("\n   Testing cache operations...")
        test_data = {"test": "value", "session_id": "test-123"}
        
        await cache.set_session("test-session", test_data)
        retrieved = await cache.get_session("test-session")
        
        if retrieved == test_data:
            print("   ✅ Cache read/write works")
        else:
            print(f"   ❌ Cache data mismatch: {retrieved}")
            return False
        
        # Cleanup
        await cache.delete_session("test-session")
        await cache.close()
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        await cache.close()
        return False


async def test_interview_engine():
    """Test InterviewEngine integration"""
    print("\n🧪 Testing Interview Engine...")
    
    from backend.core.interview.engine import InterviewEngine
    
    engine = InterviewEngine()
    
    try:
        # Start a test session
        opening = await engine.start_session(
            session_id="test-session-001",
            persona="FAANG_Architect",
            difficulty="Intermediate",
            topic="Python Development"
        )
        
        if not opening:
            print("   ❌ FAILED: No opening question received")
            return False
        
        print(f"   Opening Question: {opening[:100]}...")
        print("   ✅ Interview engine works")
        
        # Test a conversational turn
        response = await engine.process_turn(
            session_id="test-session-001",
            user_input="I have 3 years of Python experience.",
            metrics={"eye_contact_score": 0.8, "fidget_score": 1.2}
        )
        
        if not response:
            print("   ❌ FAILED: No response received")
            return False
        
        print(f"   AI Response: {response[:100]}...")
        print("   ✅ Conversational flow works")
        
        await engine.close()
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        await engine.close()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Interview Mirror - Backend Setup Validation")
    print("=" * 60)
    
    results = {
        "Ollama": await test_ollama(),
        "Redis": await test_redis(),
        "Interview Engine": await test_interview_engine()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your backend is ready.")
        print("   Run: python -m uvicorn backend.main:app --reload")
    else:
        print("\n⚠️  Some tests failed. Fix the issues above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
