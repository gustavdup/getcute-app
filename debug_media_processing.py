#!/usr/bin/env python3
"""
Media Processing Debug Script - Test media handling and fix common issues
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append('src')

async def test_media_processing():
    """Test media processing components."""
    
    print("🔍 Media Processing Debug Analysis")
    print("=" * 50)
    
    # 1. Check WhatsApp Token
    print("\n📱 WhatsApp Token Status:")
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if token:
        print(f"  ✅ Token present: {token[:20]}...")
        
        # Test token validity (simplified)
        try:
            import requests
            test_url = f"https://graph.facebook.com/v18.0/debug_token?input_token={token}&access_token={token}"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("is_valid"):
                    print("  ✅ Token is valid")
                else:
                    print("  ❌ Token is invalid or expired")
                    print(f"     Error: {data.get('data', {}).get('error', {})}")
            else:
                print(f"  ❌ Token validation failed: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Could not validate token: {e}")
    else:
        print("  ❌ No WhatsApp token found in environment")
    
    # 2. Check Storage Directory
    print("\n📁 Storage Directory Status:")
    storage_root = Path("storage")
    if storage_root.exists():
        print(f"  ✅ Storage root exists: {storage_root.resolve()}")
        
        # List user directories
        user_dirs = [d for d in storage_root.iterdir() if d.is_dir()]
        if user_dirs:
            print(f"  ✅ User directories found: {len(user_dirs)}")
            for user_dir in user_dirs[:3]:  # Show first 3
                print(f"     - {user_dir.name}")
        else:
            print("  ⚠️  No user directories found (this is expected if no media has been processed)")
    else:
        print(f"  ❌ Storage root does not exist: {storage_root.resolve()}")
        print("     Creating storage directory...")
        try:
            storage_root.mkdir(parents=True, exist_ok=True)
            print("  ✅ Storage directory created successfully")
        except Exception as e:
            print(f"  ❌ Failed to create storage directory: {e}")
    
    # 3. Check Required Services
    print("\n🔧 Service Dependencies:")
    
    # Check if file storage service can initialize
    try:
        from src.services.file_storage_service import FileStorageService
        file_storage = FileStorageService()
        print("  ✅ FileStorageService initializes successfully")
    except Exception as e:
        print(f"  ❌ FileStorageService error: {e}")
    
    # Check if media processing service can initialize
    try:
        from src.services.media_processing_service import MediaProcessingService
        media_processor = MediaProcessingService()
        print("  ✅ MediaProcessingService initializes successfully")
    except Exception as e:
        print(f"  ❌ MediaProcessingService error: {e}")
    
    # 4. Check Double Message Issue
    print("\n🔄 Double Message Analysis:")
    print("  Common causes:")
    print("  - WhatsApp webhook retries on errors")
    print("  - Exception handling sending response before main error handler")
    print("  - Token expiration causing multiple error responses")
    
    # 5. Provide fixes
    print("\n🛠️  Recommended Fixes:")
    print("  1. ⚠️  URGENT: Refresh WhatsApp access token")
    print("     - Go to Facebook Developer Console")
    print("     - Generate new temporary access token")
    print("     - Update WHATSAPP_ACCESS_TOKEN in .env")
    print("     - Restart server")
    
    print("  2. 📁 Storage folder structure will be auto-created on first media upload")
    
    print("  3. 🔄 Double message prevention:")
    print("     - Implement message deduplication using message IDs")
    print("     - Add webhook response timeout handling")
    print("     - Improve error handling to prevent multiple responses")

if __name__ == "__main__":
    asyncio.run(test_media_processing())
