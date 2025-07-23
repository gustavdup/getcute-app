#!/usr/bin/env python3
"""
Test the new brain dump workflow with message accumulation.
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.supabase_service import SupabaseService
from models.database import SessionStatus, MessageType

async def test_brain_dump_workflow():
    """Test the complete brain dump workflow."""
    print("🧪 Testing new brain dump workflow...")
    
    try:
        db_service = SupabaseService()
        
        # Get existing user
        users_result = db_service.admin_client.table('users').select('id, phone_number').limit(1).execute()
        if not users_result.data:
            print("❌ No users found.")
            return
            
        user_id = users_result.data[0]['id']
        user_phone = users_result.data[0]['phone_number']
        
        print(f"📱 Testing with user: {user_phone}")
        
        # Clean up any existing sessions
        await db_service.admin_client.table("sessions").update({
            "status": "completed"
        }).eq("user_id", str(user_id)).eq("status", "active").execute()
        
        print("\n1. Creating brain dump session...")
        session = await db_service.create_session(
            user_id=user_id,
            session_type="brain_dump",
            tags=["test", "workflow"]
        )
        
        if not session or not session.id:
            print("❌ Failed to create session")
            return
            
        print(f"✅ Created session: {session.id}")
        
        print("\n2. Simulating accumulated messages...")
        test_messages = [
            {"content": "First brain dump thought", "tags": ["idea"]},
            {"content": "Second important point about the project", "tags": ["work", "project"]},
            {"content": "Remember to follow up on this tomorrow", "tags": ["reminder"]},
            {"content": "Final thought with no tags", "tags": []}
        ]
        
        # Simulate message accumulation
        accumulated_messages = []
        all_tags = []
        
        for i, msg in enumerate(test_messages):
            accumulated_messages.append({
                "content": msg["content"],
                "timestamp": f"2025-07-22T21:3{i}:00Z",
                "tags": msg["tags"]
            })
            for tag in msg["tags"]:
                if tag not in all_tags:
                    all_tags.append(tag)
            print(f"   📝 Message {i+1}: {msg['content'][:30]}...")
        
        # Update session metadata
        metadata = {
            "messages": accumulated_messages,
            "accumulated_tags": all_tags,
            "last_message_time": "2025-07-22T21:34:00Z"
        }
        
        result = await db_service.update_session_metadata(session.id, metadata)
        if result:
            print(f"✅ Accumulated {len(accumulated_messages)} messages in session")
        else:
            print("❌ Failed to update session metadata")
            return
        
        print(f"📊 Session contains {len(accumulated_messages)} messages with tags: {all_tags}")
        
        print("\n3. Testing session ending and consolidation...")
        # End session (this should trigger consolidation)
        await db_service.end_session(session.id, SessionStatus.COMPLETED)
        
        # Check if a brain dump note was created
        messages_result = db_service.admin_client.table("messages").select(
            "*"
        ).eq("user_id", str(user_id)).eq("type", "brain_dump").order("message_timestamp", desc=True).limit(1).execute()
        
        if messages_result.data:
            brain_dump_note = messages_result.data[0]
            print(f"✅ Consolidated brain dump note created:")
            print(f"   ID: {brain_dump_note['id']}")
            print(f"   Content preview: {brain_dump_note['content'][:100]}...")
            print(f"   Tags: {brain_dump_note['tags']}")
            print(f"   Lines: {brain_dump_note['content'].count('•')} bullet points")
        else:
            print("❌ No brain dump note was created")
        
        print("\n🎯 Brain dump workflow test complete!")
        print("\n📋 Expected behavior:")
        print("- /bd starts session (responds once)")  
        print("- Messages during session: NO responses (silent accumulation)")
        print("- /end ends session: Creates one consolidated note + confirms")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_brain_dump_workflow())
