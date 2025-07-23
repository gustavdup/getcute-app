# Cloudflare Domain Setup Guide

## Current Tunnel Configuration
Your current tunnel is likely configured with a temporary domain. 

## Update Tunnel for Custom Domain

### Option 1: Via Cloudflare Dashboard (Recommended)
1. Go to Cloudflare Dashboard > Zero Trust > Access > Tunnels
2. Find your existing tunnel (or create new one)
3. Click "Configure"
4. Add new Public Hostname:
   - **Subdomain**: webhook (or api, bot, etc.)
   - **Domain**: yourdomain.com
   - **Path**: /webhook
   - **Service**: HTTP localhost:8000

### Option 2: Via Command Line
```bash
# Login to Cloudflare (if not already)
cloudflared tunnel login

# Create new tunnel (if needed)
cloudflared tunnel create whatsapp-bot

# Configure tunnel
cloudflared tunnel route dns whatsapp-bot webhook.yourdomain.com

# Update config.yml
```

## Updated config.yml Example
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/credentials.json

ingress:
  - hostname: webhook.yourdomain.com
    service: http://localhost:8000
  - hostname: admin.yourdomain.com  # Optional: separate admin access
    service: http://localhost:8000
  - service: http_status:404
```

## WhatsApp Webhook URL
After setup, your webhook URL will be:
`https://webhook.yourdomain.com/webhook`

## SSL/TLS Settings
- Set SSL/TLS mode to "Full" or "Full (strict)"
- Enable "Always Use HTTPS"
- Consider enabling "HSTS"

## Security Recommendations
- Use Cloudflare Access Rules to restrict admin access
- Enable Cloudflare firewall rules if needed
- Consider using Cloudflare Access for admin panel

## Verification Steps
1. Test domain resolution: `nslookup yourdomain.com`
2. Test tunnel: `curl https://webhook.yourdomain.com/health`
3. Update WhatsApp webhook URL in Meta Developer Console
4. Test webhook with WhatsApp
