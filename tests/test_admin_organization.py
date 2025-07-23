#!/usr/bin/env python3
"""
Test script to check admin organization logic.
"""
import sys
import os
sys.path.append('src')
sys.path.append('admin')
import asyncio
from src.services.supabase_service import SupabaseService

# Import admin logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'admin'))
from user_admin import organize_user_data

async def test_admin_organization():
    db = SupabaseService()
    
    print("=== Testing Admin Organization Logic ===")
    
    # Get a user with brain dumps
    brain_dump_messages = db.admin_client.table('messages').select('user_id').eq('type', 'brain_dump').limit(1).execute()
    
    if not brain_dump_messages.data:
        print("No brain dump messages found to test with")
        return
    
    user_id = brain_dump_messages.data[0]['user_id']
    print(f"Testing with user ID: {user_id}")
    
    # Get all messages for this user
    messages_result = db.admin_client.table("messages").select("*").eq("user_id", user_id).order("message_timestamp", desc=False).execute()
    messages = messages_result.data if messages_result.data else []
    
    # Get other data
    reminders = []
    birthdays = []
    sessions = []
    
    print(f"Total messages for user: {len(messages)}")
    
    # Test organization
    organized = organize_user_data(messages, reminders, birthdays, sessions)
    
    print(f"Notes count: {len(organized['notes'])}")
    print(f"Brain dumps count: {len(organized['brain_dumps'])}")
    
    print("\nNotes tab will show:")
    for note in organized['notes']:
        msg_type = note.get('type', 'unknown')
        content_preview = note.get('content', '')[:50] + '...' if len(note.get('content', '')) > 50 else note.get('content', '')
        print(f"  - {msg_type}: {content_preview}")
    
    print("\nBrain dumps (separate list):")
    for bd in organized['brain_dumps']:
        content_preview = bd.get('content', '')[:50] + '...' if len(bd.get('content', '')) > 50 else bd.get('content', '')
        print(f"  - {content_preview}")

if __name__ == "__main__":
    asyncio.run(test_admin_organization())
