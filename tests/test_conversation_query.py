import asyncio
import sys
import os
# Add the parent directory to sys.path to import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from datetime import datetime, timedelta
from src.services.supabase_service import SupabaseService
from src.config.settings import settings

async def test_conversation_query():
    """Test the conversation query logic directly."""
    db_service = SupabaseService()
    try:
        user_id = "3a73c5a0-c343-478f-9a37-838bd58c88b4"  # Real user ID from database
        
        # Test different days values
        for days in [0, 30, 365]:
            print(f"\n=== Testing days={days} ===")
            
            # Build query similar to API
            query = db_service.admin_client.table("messages").select(
                "id, user_id, content, message_timestamp, type, tags, file_id, media_url, metadata, source_type"
            ).eq("user_id", user_id)
            
            if days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                print(f"Cutoff date: {cutoff_date.isoformat()}")
                query = query.gte("message_timestamp", cutoff_date.isoformat())
            else:
                print("Getting all messages (no time limit)")
            
            # Execute query
            result = query.order("message_timestamp", desc=True).execute()
            messages = result.data if result.data else []
            
            print(f"Total messages: {len(messages)}")
            
            # Check for brain dumps
            brain_dumps = [m for m in messages if m.get('type') == 'brain_dump']
            print(f"Brain dump messages: {len(brain_dumps)}")
            
            # Look for the specific brain dump
            target_id = 'b4eb8600-4b4d-492d-a611-20310e8f4498'
            target_found = False
            
            for bd in brain_dumps:
                msg_id = bd.get('id')
                timestamp = bd.get('message_timestamp')
                content_len = len(bd.get('content', ''))
                
                print(f"  - ID: {msg_id}, Time: {timestamp}, Content: {content_len} chars")
                
                if msg_id == target_id:
                    target_found = True
                    print(f"    *** FOUND TARGET MESSAGE ***")
                    print(f"    Content preview: {bd.get('content', '')[:100]}...")
            
            if not target_found:
                print(f"  *** TARGET MESSAGE {target_id} NOT FOUND ***")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pass  # SupabaseService doesn't need explicit close

if __name__ == "__main__":
    asyncio.run(test_conversation_query())
