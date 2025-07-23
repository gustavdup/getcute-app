#!/usr/bin/env python3
"""
Test script to check what the conversation API returns.
"""
import sys
sys.path.append('src')
import asyncio
from src.services.supabase_service import SupabaseService
from datetime import datetime, timedelta

async def test_conversation_api():
    db = SupabaseService()
    
    print("=== Testing Conversation API Logic ===")
    
    # Get a user with brain dumps
    brain_dump_messages = db.admin_client.table('messages').select('user_id').eq('type', 'brain_dump').limit(1).execute()
    
    if not brain_dump_messages.data:
        print('No brain dump messages found')
        return
    
    user_id = brain_dump_messages.data[0]['user_id']
    print(f'Testing conversation API for user: {user_id}')
    
    # Simulate the conversation API call
    cutoff_date = datetime.now() - timedelta(days=30)
    
    messages_result = db.admin_client.table('messages').select(
        'id, user_id, content, message_timestamp, type, tags, file_id, media_url, metadata, source_type'
    ).eq('user_id', user_id).gte('message_timestamp', cutoff_date.isoformat()).order('message_timestamp', desc=True).execute()
    
    messages = messages_result.data if messages_result.data else []
    
    print(f'Total messages returned: {len(messages)}')
    
    # Check message types
    type_counts = {}
    brain_dumps = []
    
    for msg in messages:
        msg_type = msg.get('type', 'unknown')
        type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        if msg_type == 'brain_dump':
            brain_dumps.append(msg)
    
    print(f'Message types found:')
    for msg_type, count in type_counts.items():
        print(f'  {msg_type}: {count}')
    
    print(f'\\nBrain dump messages that should appear in timeline:')
    for bd in brain_dumps:
        content_preview = bd.get('content', '')[:50] + '...' if len(bd.get('content', '')) > 50 else bd.get('content', '')
        print(f'  - ID: {bd.get("id")}')
        print(f'    Content: {content_preview}')
        print(f'    Tags: {bd.get("tags", [])}')
        print(f'    Timestamp: {bd.get("message_timestamp")}')
        print()

if __name__ == "__main__":
    asyncio.run(test_conversation_api())
