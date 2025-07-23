@echo off
echo 🌟 Cloudflare Named Tunnel Setup
echo This will create a permanent tunnel URL for your bot
echo.

REM First, authenticate with Cloudflare
echo 1. Authenticating with Cloudflare...
.\cloudflared.exe tunnel login

echo.
echo 2. Creating a named tunnel...
.\cloudflared.exe tunnel create cute-whatsapp-bot

echo.
echo 3. Setting up DNS record...
echo You need to add a DNS record in your Cloudflare dashboard:
echo   Type: CNAME
echo   Name: bot (or whatever subdomain you want)
echo   Target: [tunnel-id].cfargotunnel.com
echo.

echo 4. Create config file...
echo You'll need to create a config.yml file with your tunnel settings
echo.

pause
