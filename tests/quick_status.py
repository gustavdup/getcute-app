"""
Simple test to check current status
"""
import subprocess
import requests

print("🔍 Quick Status Check")
print("=" * 40)

# Check if cloudflared is running
try:
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe'], 
                          capture_output=True, text=True, timeout=5)
    if 'cloudflared.exe' in result.stdout:
        print("✅ Cloudflared is running")
    else:
        print("❌ Cloudflared is NOT running")
except:
    print("❌ Can't check cloudflared")

# Check if port 8000 is in use
try:
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
    if ':8000' in result.stdout:
        print("✅ Something is running on port 8000")
    else:
        print("❌ Nothing on port 8000")
except:
    print("❌ Can't check port 8000")

# Test localhost
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    print(f"✅ Localhost responds: {response.status_code}")
except:
    print("❌ Localhost not responding")

# Test dev.getcute.chat
try:
    response = requests.get('https://dev.getcute.chat/health', timeout=5)
    print(f"✅ dev.getcute.chat responds: {response.status_code}")
except Exception as e:
    print(f"❌ dev.getcute.chat error: {str(e)[:50]}...")

print("\n📝 WHAT TO DO:")
print("1. Start tunnel: start_named_tunnel.bat")
print("2. Start server: python run_server.py")
print("3. Test again: python setup_dev_subdomain.py")
