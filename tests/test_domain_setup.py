#!/usr/bin/env python3
"""
Test script to verify domain and webhook setup.
"""
import requests
import sys

def test_domain_setup(domain):
    """Test if domain is properly configured."""
    print(f"🧪 Testing domain setup for: {domain}")
    
    # Test basic connectivity
    webhook_url = f"https://webhook.{domain}/webhook"
    health_url = f"https://webhook.{domain}/health"
    
    print(f"\n1. Testing health endpoint: {health_url}")
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint is working")
        else:
            print(f"❌ Health endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    print(f"\n2. Testing webhook endpoint: {webhook_url}")
    try:
        # Test GET request (should return method not allowed or similar)
        response = requests.get(webhook_url, timeout=10)
        print(f"✅ Webhook endpoint accessible (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Webhook endpoint failed: {e}")
    
    print(f"\n3. Testing SSL certificate...")
    try:
        response = requests.get(f"https://{domain}", timeout=10)
        print("✅ SSL certificate is valid")
    except requests.exceptions.SSLError:
        print("❌ SSL certificate issue")
    except Exception as e:
        print(f"⚠️ SSL test inconclusive: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_domain_setup.py yourdomain.com")
        sys.exit(1)
    
    domain = sys.argv[1]
    test_domain_setup(domain)
