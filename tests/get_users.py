import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from services.supabase_service import SupabaseService

async def get_user_ids():
    """Get actual user IDs from the database."""
    db_service = SupabaseService()
    try:
        # Get all users
        result = db_service.admin_client.table("users").select("id, phone_number").execute()
        users = result.data if result.data else []
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  ID: {user.get('id')}, Phone: {user.get('phone_number')}")
        
        return users
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(get_user_ids())
