#!/usr/bin/env python3
"""
Quick webhook test script
"""
import requests
import json

def test_webhook():
    """Test the webhook URL directly"""
    
    # Test basic connectivity
    print("🧪 Testing webhook connectivity...")
    
    base_url = "https://participated-pig-translated-donna.trycloudflare.com"
    
    try:
        # Test root endpoint
        print(f"Testing: {base_url}/")
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    try:
        # Test webhook verification
        print(f"\nTesting: {base_url}/webhook (verification)")
        params = {
            "hub.mode": "subscribe",
            "hub.challenge": "test123",
            "hub.verify_token": "cute_bot_verify_2025_secure_token_xyz789"
        }
        response = requests.get(f"{base_url}/webhook", params=params, timeout=10)
        print(f"✅ Webhook verification: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Webhook verification failed: {e}")
    
    try:
        # Test webhook POST (simulate WhatsApp message)
        print(f"\nTesting: {base_url}/webhook (POST)")
        test_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "id": "test_message_id",
                            "from": "1234567890",
                            "timestamp": "1234567890",
                            "text": {"body": "Test message"},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        response = requests.post(
            f"{base_url}/webhook", 
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"✅ Webhook POST: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Webhook POST failed: {e}")

if __name__ == "__main__":
    test_webhook()
    input("\nPress Enter to continue...")
