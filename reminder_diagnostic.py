#!/usr/bin/env python3
"""
Quick diagnostic for reminder processing issues
"""

import os
from dotenv import load_dotenv

print("🔍 Reminder Processing Diagnostic")
print("=" * 40)

# Check environment variables
load_dotenv()

print("Environment Check:")
print(f"  WHATSAPP_ACCESS_TOKEN: {'✅ Present' if os.getenv('WHATSAPP_ACCESS_TOKEN') else '❌ Missing'}")
print(f"  WHATSAPP_PHONE_NUMBER_ID: {'✅ Present' if os.getenv('WHATSAPP_PHONE_NUMBER_ID') else '❌ Missing'}")
print(f"  OPENAI_API_KEY: {'✅ Present' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
print()

# Check if the required modules can be imported
try:
    import sys
    sys.path.append('src')
    
    from src.ai.message_classifier import MessageClassifier
    print("✅ MessageClassifier imports successfully")
    
    from src.handlers.message_handlers.reminder_handler import ReminderHandler
    print("✅ ReminderHandler imports successfully")
    
    from src.handlers.message_router import MessageRouter
    print("✅ MessageRouter imports successfully")
    
except Exception as e:
    print(f"❌ Import error: {e}")

print()

# Most common issues for reminder processing failures:
print("🔍 Common Issues:")
print("1. Server not restarted after .env changes")
print("2. OpenAI API quota exceeded or key invalid")
print("3. WhatsApp token expired")
print("4. Message not classified as 'reminder' type")
print("5. AI extraction returning malformed JSON")

print()
print("💡 Quick Fixes:")
print("1. Restart your bot server: python run_server.py")
print("2. Check if WhatsApp token is valid in admin dashboard")
print("3. Try a simpler reminder: 'Remind me to call John in 10 minutes'")
print("4. Check server console/logs for specific error messages")

print()
print("🚨 If you're getting 'couldn't be processed' errors:")
print("   → The server is likely not restarted with new WHATSAPP_PHONE_NUMBER_ID")
print("   → Or there's an exception in the reminder handler")
