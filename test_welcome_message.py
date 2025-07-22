#!/usr/bin/env python3
"""
Test the welcome message functionality
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add src to path  
sys.path.append('src')

from src.services.supabase_service import SupabaseService
from src.services.whatsapp_service import WhatsAppService

async def test_welcome_message():
    print("🎉 Testing Welcome Message Feature")
    print("=" * 50)
    
    try:
        # Initialize services
        db_service = SupabaseService()
        whatsapp_service = WhatsAppService(db_service)
        
        # Test with a fake phone number to see if new user detection works
        test_phone = "+1234567890"  # This should be a new user
        
        print(f"Testing with phone number: {test_phone}")
        
        # Test the user creation and welcome message logic
        user, is_new_user = await db_service.get_or_create_user(test_phone)
        
        print(f"User created: {user}")
        print(f"Is new user: {is_new_user}")
        
        if is_new_user:
            print("\n✅ New user detected - welcome message would be sent!")
            print("\n📱 Welcome Message Preview:")
            print("-" * 50)
            
            welcome_message = f"""🤖 **Welcome to GetCute!** 

Hi there! I'm your ADHD-friendly personal productivity assistant. I'm here to help you capture thoughts, set reminders, and stay organized without the overwhelm.

**Here's what I can help you with:**

📝 **Brain Dumps & Notes**
• Just send me any thought - I'll save it as a note
• Start a brain dump session: `/bd` (end with `/end`)
• I'll automatically organize everything for you

⏰ **Smart Reminders** 
• "Remind me to call John in 30 minutes"
• "Set reminder for doctor appointment tomorrow at 2pm"
• I understand natural language - no complex commands!

🎂 **Birthday Tracking**
• "Sarah's birthday is March 15th"
• "My mom's birthday is next Friday" 
• I'll remember and remind you when it's time

📱 **Media Support**
• Send voice notes - I'll transcribe and save them
• Share images - I'll store them safely
• Everything is searchable and organized

🏷️ **Tags & Organization**
• Add #tags to any message for easy finding
• I'll suggest relevant tags automatically
• Search your notes by tags anytime

**Getting Started:**
Just start chatting normally! Send me a thought, ask for a reminder, or share what's on your mind. I'll figure out how to help.

Type anything to begin - I'm ready when you are! ✨

_You can access your full dashboard at: http://localhost:8000/admin_"""
            
            print(welcome_message)
            print("-" * 50)
        else:
            print("⏭️  Existing user - no welcome message needed")
            
    except Exception as e:
        print(f"❌ Error testing welcome message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_welcome_message())
