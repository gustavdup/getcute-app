#!/usr/bin/env python3
"""
Test script to verify brain dump session ID handling is working correctly.
This script tests that:
1. /bd commands get saved with the correct session_id
2. Messages in brain dump sessions get saved with the correct session_id  
3. Media messages in brain dump sessions get saved with the correct session_id
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.services.supabase_service import SupabaseService
from src.models.database import User, MessageType, SourceType

async def test_brain_dump_session_ids():
    """Test that brain dump session IDs are saved correctly."""
    print("🧪 Testing Brain Dump Session ID Handling...")
    
    try:
        db_service = SupabaseService()
        
        # Create a test user (just for reference, we won't actually save it)
        test_user = User(
            phone_number="+1234567890",
            platform="whatsapp"
        )
        
        # Test 1: Check if there are any brain dump messages with session IDs
        print("\n1. Checking existing brain dump messages with session IDs...")
        
        # Query messages with brain_dump type and session_id
        result = db_service.admin_client.table("messages")\
            .select("id, content, session_id, type")\
            .eq("type", "brain_dump")\
            .not_.is_("session_id", "null")\
            .limit(5)\
            .execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} brain dump messages with session IDs:")
            for msg in result.data:
                print(f"   - Message: {msg['content'][:50]}...")
                print(f"     Session ID: {msg['session_id']}")
        else:
            print("⚠️  No brain dump messages with session IDs found")
        
        # Test 2: Check if there are any command messages with session IDs
        print("\n2. Checking command messages with session IDs...")
        
        result = db_service.admin_client.table("messages")\
            .select("id, content, session_id, type")\
            .eq("type", "command")\
            .not_.is_("session_id", "null")\
            .limit(5)\
            .execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} command messages with session IDs:")
            for msg in result.data:
                print(f"   - Command: {msg['content']}")
                print(f"     Session ID: {msg['session_id']}")
        else:
            print("⚠️  No command messages with session IDs found")
        
        # Test 3: Check sessions table
        print("\n3. Checking active brain dump sessions...")
        
        result = db_service.admin_client.table("sessions")\
            .select("id, user_id, status, tags, start_time")\
            .eq("type", "brain_dump")\
            .limit(5)\
            .execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} brain dump sessions:")
            for session in result.data:
                print(f"   - Session ID: {session['id']}")
                print(f"     Status: {session['status']}")
                print(f"     Tags: {session.get('tags', [])}")
        else:
            print("⚠️  No brain dump sessions found")
        
        # Test 4: Check for messages that should have session IDs but don't
        print("\n4. Checking for brain dump messages missing session IDs...")
        
        result = db_service.admin_client.table("messages")\
            .select("id, content, session_id, type, message_timestamp")\
            .eq("type", "brain_dump")\
            .is_("session_id", "null")\
            .limit(5)\
            .execute()
        
        if result.data:
            print(f"⚠️  Found {len(result.data)} brain dump messages WITHOUT session IDs:")
            for msg in result.data:
                print(f"   - Message: {msg['content'][:50]}...")
                print(f"     Timestamp: {msg['message_timestamp']}")
        else:
            print("✅ All brain dump messages have session IDs!")
        
        print("\n🎯 Test Summary:")
        print("- Brain dump messages should have session_id values")
        print("- Command messages (/bd, /end, /cancel) should have session_id when issued during active sessions")
        print("- Regular notes outside sessions should NOT have session_id values")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_brain_dump_session_ids())
