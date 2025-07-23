"""
Test script to demonstrate brain dump session with mixed media and text messages.
Shows how images, voice notes, documents, and text are all accumulated and consolidated.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.handlers.message_router import MessageRouter
from src.models.message_types import ProcessedMessage

async def test_brain_dump_with_media():
    """Test brain dump session with mixed media and text messages."""
    
    print("=== Testing Brain Dump Session with Mixed Media ===")
    
    # Initialize message router
    router = MessageRouter()
    
    # Test phone number
    test_phone = "+1234567890"
    
    try:
        # 1. Start brain dump session
        print("\n1. Starting brain dump session with '/bd #work #productivity'")
        start_message = ProcessedMessage(
            message_id="test_001",
            user_phone=test_phone,
            content="/bd #work #productivity",
            message_type="text",
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(start_message)
        
        # 2. Send a text message
        print("\n2. Sending text message: 'Need to prepare for Monday's presentation'")
        text_message = ProcessedMessage(
            message_id="test_002",
            user_phone=test_phone,
            content="Need to prepare for Monday's presentation",
            message_type="text",
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(text_message)
        
        # 3. Send an image with caption
        print("\n3. Sending image with caption: 'Whiteboard sketch of ideas'")
        image_message = ProcessedMessage(
            message_id="test_003",
            user_phone=test_phone,
            content="Whiteboard sketch of ideas #design",
            message_type="image",
            media_id="fake_image_123",  # In real scenario, this would be actual WhatsApp media ID
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(image_message)
        
        # 4. Send a voice note (simulated)
        print("\n4. Sending voice note (simulated)")
        audio_message = ProcessedMessage(
            message_id="test_004",
            user_phone=test_phone,
            content="",  # No caption for voice note
            message_type="audio",
            media_id="fake_audio_456",
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(audio_message)
        
        # 5. Send another text message
        print("\n5. Sending another text: 'Also need to review budget numbers #finance'")
        text_message2 = ProcessedMessage(
            message_id="test_005",
            user_phone=test_phone,
            content="Also need to review budget numbers #finance",
            message_type="text",
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(text_message2)
        
        # 6. Send a document
        print("\n6. Sending document: 'Contract draft for review'")
        doc_message = ProcessedMessage(
            message_id="test_006",
            user_phone=test_phone,
            content="Contract draft for review",
            message_type="document",
            media_id="fake_doc_789",
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(doc_message)
        
        # 7. End the session
        print("\n7. Ending brain dump session with '/end'")
        end_message = ProcessedMessage(
            message_id="test_007",
            user_phone=test_phone,
            content="/end",
            message_type="text",
            timestamp=datetime.now(timezone.utc)
        )
        await router.route_message(end_message)
        
        print("\n=== Expected Behavior ===")
        print("• All messages (text, image caption, voice transcription, document description) should be accumulated")
        print("• Tags from all messages should be combined: #work, #productivity, #design, #finance")
        print("• One consolidated note should be created with all content in bullet points")
        print("• Each media item should be described with appropriate emoji and content")
        print("• Voice note should include transcription if available")
        print("• No individual responses during accumulation, only final confirmation")
        
        print("\n=== What Happens with Different Media Types ===")
        print("🎤 Voice Notes:")
        print("   - Downloaded and transcribed using OpenAI Whisper")
        print("   - Transcription text becomes part of consolidated note")
        print("   - Format: '🎤 Voice note: [transcription text]'")
        
        print("\n🖼️ Images:")
        print("   - Saved to user's folder in Supabase storage")  
        print("   - Caption (if provided) becomes part of note")
        print("   - Format: '🖼️ Image: [caption or filename]'")
        print("   - TODO: OCR could be added to extract text from images")
        
        print("\n📄 Documents:")
        print("   - Saved to user's folder in Supabase storage")
        print("   - Caption or filename becomes part of note")
        print("   - Format: '📄 Document: [caption or filename]'")
        print("   - TODO: Text extraction could be added for supported formats")
        
        print("\n📎 Multiple Media:")
        print("   - Each media item gets its own bullet point in the consolidated note")
        print("   - All files are saved separately but content is combined")
        print("   - Tags from all messages (including hashtags in captions) are merged")
        
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()

def print_media_handling_scenarios():
    """Print detailed scenarios of how different media combinations are handled."""
    
    print("\n" + "="*60)
    print("BRAIN DUMP MEDIA HANDLING SCENARIOS")
    print("="*60)
    
    print("\n📱 SCENARIO 1: Voice Notes Only")
    print("   User sends: /bd")
    print("   User sends: Voice note 1 (transcribed to 'Meeting with client went well')")
    print("   User sends: Voice note 2 (transcribed to 'Need to follow up on proposal')")
    print("   User sends: /end")
    print("   ")
    print("   Result in consolidated note:")
    print("   • 🎤 Voice note: Meeting with client went well")
    print("   • 🎤 Voice note: Need to follow up on proposal")
    
    print("\n📱 SCENARIO 2: Images with Text")
    print("   User sends: /bd #ideas")
    print("   User sends: Image with caption 'Rough sketch of new feature'")
    print("   User sends: Text message 'This could solve the user workflow issue'")
    print("   User sends: Image with caption 'Alternative design approach #design'")
    print("   User sends: /end")
    print("   ")
    print("   Result in consolidated note:")
    print("   • 🖼️ Image: Rough sketch of new feature")
    print("   • This could solve the user workflow issue")
    print("   • 🖼️ Image: Alternative design approach")
    print("   Tags: #ideas, #design")
    
    print("\n📱 SCENARIO 3: Mixed Media Brainstorm")
    print("   User sends: /bd #project-planning")
    print("   User sends: Voice note (transcribed to 'Team capacity looks tight for Q2')")
    print("   User sends: Image of calendar with caption 'Current timeline #schedule'")
    print("   User sends: Text 'Maybe we should push launch to Q3 #timeline'")
    print("   User sends: Document 'project_timeline.pdf' with caption 'Original plan'")
    print("   User sends: Voice note (transcribed to 'Will discuss with Sarah tomorrow')")
    print("   User sends: /end")
    print("   ")
    print("   Result in consolidated note:")
    print("   • 🎤 Voice note: Team capacity looks tight for Q2")
    print("   • 🖼️ Image: Current timeline")
    print("   • Maybe we should push launch to Q3")
    print("   • 📄 Document: Original plan")
    print("   • 🎤 Voice note: Will discuss with Sarah tomorrow")
    print("   Tags: #project-planning, #schedule, #timeline")
    
    print("\n📱 SCENARIO 4: Images with OCR (Future Enhancement)")
    print("   User sends: /bd #notes")
    print("   User sends: Photo of handwritten notes")
    print("   ")
    print("   Current behavior:")
    print("   • 🖼️ Image: [filename or generic description]")
    print("   ")
    print("   With OCR enhancement:")
    print("   • 🖼️ Image: [extracted text from handwritten notes]")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   • Media files are saved separately in user's folder")
    print("   • Only content/descriptions are accumulated in the brain dump note")
    print("   • Voice transcriptions become searchable text")
    print("   • All hashtags from any message are combined")
    print("   • No individual confirmations during accumulation (silent mode)")
    print("   • One final confirmation with total message count")

if __name__ == "__main__":
    print("This test simulates brain dump sessions with media.")
    print("Note: Media processing will fail with fake media IDs, but shows the workflow.")
    print("\nRun with: python test_brain_dump_media.py")
    
    # Run the scenarios explanation
    print_media_handling_scenarios()
    
    # Uncomment to run the actual test (will fail with fake media IDs)
    # asyncio.run(test_brain_dump_with_media())
