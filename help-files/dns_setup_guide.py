"""
DNS Check Script - What to add to Cloudflare DNS
"""

print("="*60)
print("🔧 CLOUDFLARE DNS SETUP FOR dev.getcute.chat")
print("="*60)

print("\n📋 WHAT TO ADD TO CLOUDFLARE DNS:")
print("\n1. Go to: Cloudflare Dashboard → getcute.chat → DNS → Records")
print("2. Click 'Add record'")
print("3. Enter these details:")
print()
print("   📝 Record Details:")
print("   ┌─────────────────────────────────────────────┐")
print("   │ Type:          CNAME                        │")
print("   │ Name:          dev                          │")
print("   │ Target:        998407d4-5a6a-43df-a647-    │")
print("   │                8b1fec059bf1.cfargotunnel.com│")
print("   │ Proxy status:  🧡 Proxied (ON)             │")
print("   │ TTL:           Auto                         │")
print("   └─────────────────────────────────────────────┘")

print("\n⚠️  ALTERNATIVE TARGET (if first doesn't work):")
print("   Target: cute-whatsapp-bot.cfargotunnel.com")

print("\n✅ VERIFICATION:")
print("   After adding the record:")
print("   • Wait 1-2 minutes for DNS propagation")
print("   • Test: https://dev.getcute.chat")
print("   • Should work immediately once DNS propagates")

print("\n🎯 YOUR TUNNEL INFO:")
print("   • Tunnel ID: 998407d4-5a6a-43df-a647-8b1fec059bf1")
print("   • Tunnel Name: cute-whatsapp-bot")
print("   • Target Domain: dev.getcute.chat")
print("   • Local Service: http://localhost:8000")

print("\n🔍 TROUBLESHOOTING:")
print("   • If record already exists: Edit it instead of adding new")
print("   • Make sure Proxy is ON (orange cloud)")
print("   • Wait a few minutes for DNS to propagate")
print("   • Test with: nslookup dev.getcute.chat")

print("="*60)
