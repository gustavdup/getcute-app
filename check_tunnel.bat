@echo off
echo 🔍 Checking Cloudflare Tunnel Status...
echo.

REM Check if cloudflared is running
tasklist | findstr cloudflared >nul
if %ERRORLEVEL%==0 (
    echo ✅ Cloudflare tunnel process is running!
    echo.
    echo 📋 To see the current tunnel URL:
    echo    1. Check the terminal where you ran start_tunnel.bat
    echo    2. Look for a line like: "Visit it at: https://your-url.trycloudflare.com"
    echo.
    echo 🔗 Your previous tunnel URL was:
    echo    https://wound-amateur-auction-webmasters.trycloudflare.com
    echo.
    echo ⚠️  Note: Tunnel URLs change each time you restart the tunnel!
) else (
    echo ❌ Cloudflare tunnel is NOT running!
    echo.
    echo 🚀 To start the tunnel:
    echo    1. Open a new terminal
    echo    2. Run: .\start_tunnel.bat
    echo    3. Copy the new URL to your WhatsApp webhook
)

echo.
pause
