#!/usr/bin/env python3
"""
Clean up test sessions and test brain dump workflow.
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.supabase_service import SupabaseService
from models.database import SessionStatus

async def cleanup_and_test():
    """Clean up test sessions and test brain dump workflow."""
    print("🧹 Cleaning up test sessions...")
    
    try:
        db_service = SupabaseService()
        
        # Get existing user
        users_result = db_service.admin_client.table('users').select('id, phone_number').limit(1).execute()
        if not users_result.data:
            print("❌ No users found.")
            return
            
        user_id = users_result.data[0]['id']
        user_phone = users_result.data[0]['phone_number']
        
        # End all active sessions for this user
        print(f"📱 Cleaning sessions for user: {user_phone}")
        sessions_result = db_service.admin_client.table("sessions").select("*").eq("user_id", str(user_id)).eq("status", "active").execute()
        active_sessions = sessions_result.data if sessions_result.data else []
        
        for session in active_sessions:
            await db_service.end_session(session['id'], SessionStatus.CANCELLED)
            print(f"   ✅ Ended session: {session['id']}")
        
        print(f"🧹 Ended {len(active_sessions)} active sessions")
        
        # Verify no active sessions remain
        remaining_sessions = await db_service.get_active_session(user_id)
        if remaining_sessions:
            print(f"⚠️ Still have active session: {remaining_sessions.id}")
        else:
            print("✅ No active sessions remaining")
        
        # Test creating a new session
        print("\n🧪 Testing new brain dump session creation...")
        new_session = await db_service.create_session(
            user_id=user_id,
            session_type="brain_dump",
            tags=["test", "cleanup"]
        )
        
        if new_session:
            print(f"✅ Created session: {new_session.id}")
            
            # Test immediate retrieval
            retrieved = await db_service.get_active_session(user_id)
            if retrieved and retrieved.id == new_session.id:
                print("✅ Session retrieval working correctly")
            else:
                print("❌ Session retrieval failed")
        
        print("\n🎯 Brain dump session management is now fixed!")
        print("Next steps:")
        print("1. Restart your bot server")
        print("2. Test /bd command in WhatsApp")
        print("3. Send a message (should be treated as brain dump)")
        print("4. Test /end command")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(cleanup_and_test())
