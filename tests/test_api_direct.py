#!/usr/bin/env python3
"""
Simple test to check API response.
"""
import sys
sys.path.append('src')
import requests
import json

# Test the actual API endpoint
user_id = "3a73c5a0-c343-478f-9a37-838bd58c88b4"
response = requests.get(f"http://localhost:8000/admin/api/conversation/{user_id}?days=30")

if response.status_code == 200:
    data = response.json()
    messages = data.get('conversation', [])
    
    print(f"API returned {len(messages)} messages")
    
    brain_dumps = [msg for msg in messages if msg.get('type') == 'brain_dump']
    print(f"Brain dump messages in API response: {len(brain_dumps)}")
    
    for i, bd in enumerate(brain_dumps[:3]):  # Show first 3
        print(f"Brain dump {i+1}:")
        print(f"  ID: {bd.get('id')}")
        print(f"  Type: {bd.get('type')}")
        print(f"  Content preview: {bd.get('content', '')[:60]}...")
        print(f"  Tags: {bd.get('tags')}")
        print(f"  Timestamp: {bd.get('message_timestamp')}")
        print()
else:
    print(f"API call failed: {response.status_code}")
    print(response.text)
