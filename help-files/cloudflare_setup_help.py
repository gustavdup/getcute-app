"""
Cloudflare Tunnel Setup Guide - Multiple Methods
"""

print("="*70)
print("🔧 CLOUDFLARE TUNNEL CONFIGURATION METHODS")
print("="*70)

print("\n📍 METHOD 1: Zero Trust Dashboard (Recommended)")
print("   1. Go to: https://one.dash.cloudflare.com/")
print("   2. Select your account")
print("   3. Go to: Zero Trust → Networks → Tunnels")
print("   4. Find your tunnel or create new one")
print("   5. Click 'Configure' → 'Public Hostnames' → 'Add a public hostname'")

print("\n📍 METHOD 2: Main Cloudflare Dashboard")
print("   1. Go to: https://dash.cloudflare.com/")
print("   2. Select 'getcute.chat' domain")
print("   3. Look for 'Tunnels' in left sidebar (under 'Network' or 'Cloudflare for Teams')")
print("   4. Or check 'DNS' section for existing tunnel records")

print("\n📍 METHOD 3: DNS Record Method (Fallback)")
print("   1. Go to: Cloudflare Dashboard → getcute.chat → DNS → Records")
print("   2. Add CNAME record:")
print("      - Name: dev")
print("      - Target: [your existing tunnel domain]")
print("      - Proxy: ON (orange cloud)")

print("\n📍 METHOD 4: Command Line (Advanced)")
print("   Run these commands in your terminal:")
print("   ```")
print("   cloudflared tunnel login")
print("   cloudflared tunnel list")
print("   cloudflared tunnel route dns [TUNNEL-ID] dev.getcute.chat")
print("   ```")

print("\n🔍 FINDING YOUR CURRENT SETUP:")
print("   1. Check what's currently working - what domain are you using now?")
print("   2. Look in Cloudflare Dashboard → getcute.chat → DNS")
print("   3. Check for existing CNAME or A records pointing to tunnel")
print("   4. Check Zero Trust dashboard: https://one.dash.cloudflare.com/")

print("\n❓ TROUBLESHOOTING:")
print("   • If no 'Tunnels' option: You might need to enable 'Cloudflare for Teams'")
print("   • Check different tabs: Network, Access, Zero Trust")
print("   • Try the direct URL: https://one.dash.cloudflare.com/[ACCOUNT-ID]/networks/tunnels")

print("\n💡 QUICK ALTERNATIVE:")
print("   Tell me what domain is currently working for your bot,")
print("   and I'll help you clone that setup for dev.getcute.chat")

print("="*70)
