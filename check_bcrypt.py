from passlib.context import CryptContext
import traceback

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash = pwd_context.hash("secure_password_123")
    print(f"✅ Hash success: {hash}")
    verify = pwd_context.verify("secure_password_123", hash)
    print(f"✅ Verify success: {verify}")
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
