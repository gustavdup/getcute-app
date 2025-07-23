import asyncio
import httpx
import json

async def test_api():
    print("=== Testing API endpoint for latest brain dump ===")
    
    # Test the conversation API endpoint
    async with httpx.AsyncClient() as client:
        try:
            # Test with different days filters
            for days in [0, 30, 365]:
                print(f"\n--- Testing with days={days} ---")
                response = await client.get(f"http://localhost:8000/admin/api/conversation/3a73c5a0-c343-478f-9a37-838bd58c88b4?days={days}")
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get('conversation', data.get('messages', []))
                    
                    print(f"Total messages returned: {len(messages)}")
                    
                    # Filter brain dumps
                    brain_dumps = [msg for msg in messages if msg.get('type') == 'brain_dump']
                    print(f"Brain dump messages: {len(brain_dumps)}")
                    
                    # Check for the specific brain dump
                    target_id = 'b4eb8600-4b4d-492d-a611-20310e8f4498'
                    found_target = False
                    
                    for msg in brain_dumps:
                        msg_id = msg.get('id')
                        timestamp = msg.get('timestamp') or msg.get('message_timestamp') or msg.get('created_at')
                        content_preview = msg.get('content', '')[:50]
                        
                        print(f"  - ID: {msg_id}, Timestamp: {timestamp}")
                        print(f"    Content: {content_preview}...")
                        
                        if msg_id == target_id:
                            found_target = True
                            print(f"    *** FOUND TARGET MESSAGE ***")
                            print(f"    Full content length: {len(msg.get('content', ''))}")
                    
                    if not found_target and brain_dumps:
                        print(f"  *** TARGET MESSAGE NOT FOUND in {len(brain_dumps)} brain dumps ***")
                    
                    # Show most recent messages by timestamp
                    print(f"\n--- Most recent 3 messages (all types) ---")
                    all_messages = sorted(messages, key=lambda x: x.get('timestamp') or x.get('message_timestamp') or x.get('created_at', ''), reverse=True)
                    
                    for msg in all_messages[:3]:
                        msg_type = msg.get('type', 'unknown')
                        msg_id = msg.get('id')
                        timestamp = msg.get('timestamp') or msg.get('message_timestamp') or msg.get('created_at')
                        content_preview = msg.get('content', '')[:30]
                        
                        print(f"  - Type: {msg_type}, ID: {msg_id}")
                        print(f"    Timestamp: {timestamp}")
                        print(f"    Content: {content_preview}...")
                        
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"Error testing API: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
