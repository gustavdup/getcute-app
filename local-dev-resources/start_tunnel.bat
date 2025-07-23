@echo off
echo Starting Cloudflare Tunnel for WhatsApp Bot...
echo.
echo Your server should be running on http://localhost:8000
echo.
echo Starting tunnel...
.\cloudflared.exe tunnel --url http://localhost:8000
