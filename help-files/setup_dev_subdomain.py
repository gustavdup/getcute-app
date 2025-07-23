#!/usr/bin/env python3
"""
Quick setup verification script for dev.getcute.chat subdomain
"""
import subprocess
import requests
import sys
import os
from urllib.parse import urlparse

def check_existing_tunnel():
    """Check if cloudflared is running and find tunnel info"""
    print("🔍 Checking for existing Cloudflare tunnel...")
    
    # Check if cloudflared process is running
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe'], 
                              capture_output=True, text=True, timeout=10)
        if 'cloudflared.exe' in result.stdout:
            print("✅ Cloudflared process is running")
            
            # Try to find config file
            config_paths = [
                'config.yml',
                '.cloudflared/config.yml',
                'cloudflared/config.yml'
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    print(f"📄 Found config file: {config_path}")
                    try:
                        with open(config_path, 'r') as f:
                            content = f.read()
                            print("Current tunnel configuration:")
                            print("─" * 40)
                            print(content)
                            print("─" * 40)
                    except Exception as e:
                        print(f"Could not read config: {e}")
                    break
            
            return True
        else:
            print("❌ Cloudflared is not running")
            return False
    except Exception as e:
        print(f"❌ Error checking tunnel: {e}")
        return False

def test_dns_resolution():
    """Test if dev.getcute.chat resolves"""
    print("🔍 Testing DNS resolution for dev.getcute.chat...")
    try:
        result = subprocess.run(['nslookup', 'dev.getcute.chat'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'Non-authoritative answer' in result.stdout:
            print("✅ DNS resolution successful")
            return True
        else:
            print("❌ DNS resolution failed")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ DNS test error: {e}")
        return False

def test_https_connectivity():
    """Test if dev.getcute.chat responds over HTTPS"""
    print("🔍 Testing HTTPS connectivity to dev.getcute.chat...")
    try:
        response = requests.get('https://dev.getcute.chat/', timeout=10)
        if response.status_code in [200, 404, 301, 302]:  # Any valid HTTP response
            print("✅ HTTPS connectivity successful")
            return True
        else:
            print(f"⚠️  Got HTTP {response.status_code}")
            return True  # Still connected
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTPS test error: {e}")
        return False

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    print("🔍 Testing webhook endpoint...")
    try:
        response = requests.get('https://dev.getcute.chat/webhook', timeout=10)
        if response.status_code == 200:
            print("✅ Webhook endpoint accessible")
            return True
        elif response.status_code == 405:  # Method not allowed (GET vs POST)
            print("✅ Webhook endpoint exists (responds to POST only)")
            return True
        else:
            print(f"⚠️  Webhook returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook test error: {e}")
        return False

def test_health_endpoint():
    """Test if health endpoint is accessible"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get('https://dev.getcute.chat/health', timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint accessible")
            print(f"   Response: {response.text[:100]}...")
            return True
        else:
            print(f"⚠️  Health endpoint returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint test error: {e}")
        return False

def test_admin_panel():
    """Test if admin panel is accessible"""
    print("🔍 Testing admin panel...")
    try:
        response = requests.get('https://dev.getcute.chat/admin', timeout=10)
        if response.status_code in [200, 401, 403]:  # Accessible but may need auth
            print("✅ Admin panel accessible")
            return True
        else:
            print(f"⚠️  Admin panel returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin panel test error: {e}")
        return False

def main():
    print("="*60)
    print("🚀 DEV.GETCUTE.CHAT SETUP VERIFICATION")
    print("="*60)
    
    # First check existing tunnel
    print("\n📋 Checking Current Tunnel Setup")
    tunnel_running = check_existing_tunnel()
    print()
    
    if not tunnel_running:
        print("⚠️  No tunnel detected. You need to:")
        print("   1. Start your Cloudflare tunnel")
        print("   2. Configure it in Cloudflare Dashboard")
        print("   3. Then run this script again")
        return
    
    tests = [
        ("DNS Resolution", test_dns_resolution),
        ("HTTPS Connectivity", test_https_connectivity),  
        ("Health Endpoint", test_health_endpoint),
        ("Webhook Endpoint", test_webhook_endpoint),
        ("Admin Panel", test_admin_panel),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
        print()
    
    print("="*60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your dev.getcute.chat subdomain is ready!")
        print("\n🔗 Your URLs:")
        print("   • Webhook: https://dev.getcute.chat/webhook")
        print("   • Admin Panel: https://dev.getcute.chat/admin")
        print("   • Health Check: https://dev.getcute.chat/health")
        print("\n✅ Next steps:")
        print("   1. Update WhatsApp webhook URL in Meta Developer Console")
        print("   2. Update WEBHOOK_URL in your .env file")
        print("   3. Test by sending a WhatsApp message")
    else:
        print("⚠️  Some tests failed. Check Cloudflare tunnel configuration.")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Go to Cloudflare Dashboard → Zero Trust → Networks → Tunnels")
        print("   2. Find your tunnel and click 'Configure'")
        print("   3. Add Public Hostname:")
        print("      - Subdomain: dev")
        print("      - Domain: getcute.chat") 
        print("      - Service: HTTP localhost:8000")
        print("   4. Ensure SSL/TLS mode is 'Full' or 'Full (strict)'")
        print("   5. Make sure your local server is running on port 8000")

if __name__ == "__main__":
    main()
