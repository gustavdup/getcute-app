@echo off
echo 🚀 Starting Named Cloudflare Tunnel for dev.getcute.chat
echo.
echo Make sure your server is running on http://localhost:8000
echo Your permanent URL is: https://dev.getcute.chat
echo.
echo Starting tunnel...
.\cloudflared.exe tunnel --config config.yml run cute-whatsapp-bot
