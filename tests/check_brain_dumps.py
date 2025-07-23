#!/usr/bin/env python3
"""
Quick script to check brain dump messages in the database.
"""
import sys
import os
sys.path.append('src')
import asyncio
from src.services.supabase_service import SupabaseService

async def check_brain_dumps():
    db = SupabaseService()
    
    print("=== Checking Brain Dump Messages ===")
    # Check for brain dump messages
    result = db.admin_client.table('messages').select('*').eq('type', 'brain_dump').execute()
    
    print(f'Total BRAIN_DUMP messages: {len(result.data) if result.data else 0}')
    
    if result.data:
        for msg in result.data:
            print(f'- Message ID: {msg.get("id")}')
            print(f'  User ID: {msg.get("user_id")}')
            print(f'  Content preview: {msg.get("content", "")[:100]}...')
            print(f'  Tags: {msg.get("tags", [])}')
            print(f'  Created: {msg.get("message_timestamp", "Unknown")}')
            print(f'  Session ID: {msg.get("session_id", "NO SESSION")}')
            print(f'  Type: {msg.get("type")}')
            if msg.get("id") == "b4eb8600-4b4d-492d-a611-20310e8f4498":
                print(f'  *** THIS IS THE TARGET MESSAGE ***')
                print(f'  Full content: {msg.get("content", "")}')
            print()
    else:
        print('No BRAIN_DUMP messages found.')
    
    print("\n=== Checking Sessions ===")
    # Check for active sessions
    sessions = db.admin_client.table('sessions').select('*').execute()
    print(f'Total sessions: {len(sessions.data) if sessions.data else 0}')
    
    if sessions.data:
        for session in sessions.data:
            metadata = session.get("metadata") or {}
            messages_in_metadata = metadata.get("messages", []) if metadata else []
            
            print(f'- Session ID: {session.get("id")}')
            print(f'  Status: {session.get("status")}')
            print(f'  Tags: {session.get("tags", [])}')
            print(f'  Messages in metadata: {len(messages_in_metadata)}')
            print(f'  Start time: {session.get("start_time", "Unknown")}')
            print(f'  End time: {session.get("end_time", "Active")}')
            print()
    
    print("\n=== Checking All Message Types ===")
    # Check message types
    all_messages = db.admin_client.table('messages').select('type').execute()
    type_counts = {}
    if all_messages.data:
        for msg in all_messages.data:
            msg_type = msg.get('type', 'unknown')
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
    
    print("Message type distribution:")
    for msg_type, count in type_counts.items():
        print(f"  {msg_type}: {count}")

if __name__ == "__main__":
    asyncio.run(check_brain_dumps())
