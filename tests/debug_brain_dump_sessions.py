#!/usr/bin/env python3
"""
Debug brain dump session management.
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.supabase_service import SupabaseService
from models.database import SessionStatus

async def debug_sessions():
    """Debug session creation and retrieval."""
    print("🔍 Debugging brain dump sessions...")
    
    try:
        db_service = SupabaseService()
        
        # Get an existing user
        users_result = db_service.admin_client.table('users').select('id, phone_number').limit(1).execute()
        if not users_result.data:
            print("❌ No users found in database.")
            return
            
        user_id = users_result.data[0]['id']
        user_phone = users_result.data[0]['phone_number']
        print(f"📱 Using user: {user_phone} (ID: {user_id})")
        
        # Check for existing active sessions
        print("\n1. Checking existing active sessions...")
        active_session = await db_service.get_active_session(user_id)
        if active_session:
            print(f"✅ Found active session: {active_session.id} (Status: {active_session.status})")
        else:
            print("❌ No active session found")
        
        # List all sessions for this user
        print("\n2. All sessions for this user:")
        sessions_result = db_service.admin_client.table("sessions").select("*").eq("user_id", str(user_id)).order("start_time", desc=True).execute()
        sessions = sessions_result.data if sessions_result.data else []
        
        for session in sessions:
            print(f"   - Session {session['id']}: Status={session['status']}, Type={session['type']}, Start={session['start_time']}")
        
        print(f"\n📊 Total sessions found: {len(sessions)}")
        
        # Test session creation
        print("\n3. Testing session creation...")
        try:
            new_session = await db_service.create_session(
                user_id=user_id,
                session_type="brain_dump",
                tags=["test", "debug"]
            )
            print(f"✅ Created new session: {new_session.id}")
            
            # Test retrieval immediately
            retrieved_session = await db_service.get_active_session(user_id)
            if retrieved_session:
                print(f"✅ Successfully retrieved session: {retrieved_session.id}")
            else:
                print("❌ Could not retrieve session immediately after creation")
                
        except Exception as e:
            print(f"❌ Error creating session: {e}")
        
        # Check the sessions table schema
        print("\n4. Checking sessions table structure...")
        try:
            # Get a sample record to see the structure
            sample_result = db_service.admin_client.table("sessions").select("*").limit(1).execute()
            if sample_result.data:
                print("✅ Sessions table structure:")
                for key, value in sample_result.data[0].items():
                    print(f"   {key}: {type(value)} = {value}")
            else:
                print("❌ No sessions in table to examine structure")
        except Exception as e:
            print(f"❌ Error examining sessions table: {e}")
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_sessions())
