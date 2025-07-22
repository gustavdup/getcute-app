"""
Simple test to verify the setup is working.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

try:
    import uvicorn
    print("✅ uvicorn imported successfully")
except ImportError as e:
    print(f"❌ uvicorn import failed: {e}")

try:
    import fastapi
    print("✅ fastapi imported successfully")
except ImportError as e:
    print(f"❌ fastapi import failed: {e}")

try:
    import supabase
    print("✅ supabase imported successfully")
except ImportError as e:
    print(f"❌ supabase import failed: {e}")

try:
    import openai
    print("✅ openai imported successfully")
except ImportError as e:
    print(f"❌ openai import failed: {e}")

try:
    from config.settings import settings
    print("✅ settings imported successfully")
    print(f"   Debug mode: {settings.debug}")
    print(f"   API host: {settings.api_host}")
    print(f"   API port: {settings.api_port}")
except ImportError as e:
    print(f"❌ settings import failed: {e}")

print("\n🎉 Basic setup verification complete!")
print("\nNext steps:")
print("1. Edit .env file with your API keys")
print("2. Set up Supabase database")
print("3. Configure WhatsApp Business API")
print("4. Run the main application")
