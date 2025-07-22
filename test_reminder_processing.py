#!/usr/bin/env python3
"""
Test reminder processing with your specific message
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from src.ai.message_classifier import MessageClassifier
from src.handlers.message_handlers.reminder_handler import ReminderHandler

async def test_reminder_processing():
    print("🔍 Testing Reminder Processing")
    print("=" * 50)
    
    # Test message
    test_message = "Remind me to go pee in 5 minutes"
    print(f"Test message: '{test_message}'")
    print()
    
    try:
        # Initialize classifier
        classifier = MessageClassifier()
        
        # Test classification
        print("Step 1: Testing AI classification...")
        classification = await classifier.classify_message(test_message, user_context={})
        print(f"Classification result: {classification}")
        print()
        
        if classification.message_type == "reminder":
            print("✅ Message correctly classified as reminder")
            
            # Test reminder extraction
            print("Step 2: Testing reminder extraction...")
            
            # Create a mock reminder handler (without full services)
            class MockHandler:
                def __init__(self):
                    self.classifier = classifier
                    
                async def test_extraction(self, content):
                    try:
                        system_prompt = '''You are an expert at extracting reminder information from text messages.
Extract the reminder details from the user's message.

Return a JSON object with:
- "title": The main reminder text (what to be reminded about)
- "trigger_time": ISO datetime string when the reminder should trigger
- "repeat_type": one of "none", "daily", "weekly", "monthly", "yearly"

For relative times like "in 5 minutes", calculate the exact future time.'''
                        
                        current_time = datetime.now()
                        user_prompt = f"Current date/time: {current_time.isoformat()}\n\nExtract reminder from: '{content}'"
                        
                        response = await self.classifier.generate_completion(
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            max_tokens=300,
                            temperature=0.1
                        )
                        
                        print(f"AI Response: {response}")
                        return response
                        
                    except Exception as e:
                        print(f"❌ Error in extraction: {e}")
                        return None
            
            handler = MockHandler()
            result = await handler.test_extraction(test_message)
            
            if result:
                print("✅ AI extraction completed")
            else:
                print("❌ AI extraction failed")
        else:
            print(f"❌ Message classified as '{classification.message_type}', not 'reminder'")
            print("This could be why the reminder isn't processing!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_reminder_processing())
