#!/usr/bin/env python3
"""
Enhanced server runner for the Cute WhatsApp Bot.
Handles Python path issues, runs the full-featured FastAPI server,
and manages Cloudflare tunnel when ENVIRONMENT=local.
"""
import sys
import os
import subprocess
import time
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Set environment for relative imports
os.environ['PYTHONPATH'] = str(src_path)

def start_cloudflare_tunnel():
    """Start Cloudflare tunnel in a separate process."""
    try:
        cloudflared_path = project_root / "cloudflared.exe"
        if not cloudflared_path.exists():
            print("❌ cloudflared.exe not found. Please download it first.")
            return False, None
        
        # Check if config.yml exists for static tunnel
        config_path = project_root / "config.yml"
        if config_path.exists():
            print("🔄 Starting Cloudflare tunnel with static URL (config.yml found)...")
            # Use static tunnel with config
            process = subprocess.Popen(
                [str(cloudflared_path), "tunnel", "--config", str(config_path), "run"],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            print("✅ Static tunnel started! Using URL from your config.yml")
            return True, process
        else:
            print("🔄 Starting Cloudflare tunnel with temporary URL...")
            # Use temporary tunnel
            process = subprocess.Popen(
                [str(cloudflared_path), "tunnel", "--url", "http://localhost:8000"],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            print("💡 For permanent URL, set up a named tunnel with config.yml")
            
        # Give it a moment to start
        time.sleep(3)
        
        # Check if the process started successfully
        if process.poll() is None:  # Process is still running
            print("✅ Tunnel process started successfully!")
            print("💡 Check the new console window for the tunnel URL")
            return True, process
        else:
            print("❌ Tunnel process failed to start")
            return False, None
        
    except Exception as e:
        print(f"❌ Failed to start tunnel: {e}")
        return False, None

def check_cloudflare_tunnel():
    """Check if Cloudflare tunnel is running."""
    try:
        # Check if cloudflared process is running
        result = subprocess.run(
            'tasklist | findstr cloudflared',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "cloudflared.exe" in result.stdout:
            return "🔗 Cloudflare tunnel is running!"
        else:
            return "❌ Cloudflare tunnel not detected."
    except:
        return "❓ Could not check tunnel status"

# Now import and run the server
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    # Get config
    try:
        from config.settings import settings
        host = settings.api_host
        port = settings.api_port
        debug = settings.debug
        log_level = settings.log_level.lower()
        environment = getattr(settings, 'environment', 'production').lower()
    except:
        # Fallback defaults
        host = "localhost"
        port = 8000
        debug = True
        log_level = "info"
        environment = os.getenv("ENVIRONMENT", "production").lower()
    
    print(f"🤖 Starting Cute WhatsApp Bot (Full Features)...")
    print(f"📡 Server: http://{host}:{port}")
    print(f"🌍 Environment: {environment}")
    print("=" * 50)
    
    # Handle Cloudflare tunnel for local development
    tunnel_started = False
    if environment == "local":
        print("🏠 Local environment detected - managing Cloudflare tunnel...")
        
        # Check if tunnel is already running
        tunnel_status = check_cloudflare_tunnel()
        
        if "not detected" in tunnel_status:
            print("🚀 Starting Cloudflare tunnel automatically...")
            tunnel_started, process = start_cloudflare_tunnel()
            
            if tunnel_started:
                print("✅ Tunnel started successfully!")
                print("💡 Check the new console window for the tunnel URL")
                print("📋 Copy the URL from the console and update your WhatsApp webhook")
            else:
                print("❌ Failed to start tunnel automatically")
                print("💡 Manual option: Run .\\start_tunnel.bat in another terminal")
        else:
            print(f"{tunnel_status}")
            print("💡 Check your tunnel terminal for the current URL")
        
        print(f"🔗 Local webhook URL: http://{host}:{port}/webhook")
        print(f"� Verify Token: {os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'cute_bot_verify_2025_secure_token_xyz789')}")
        print("=" * 50)
        
        if tunnel_started:
            print("📋 WhatsApp Webhook Configuration:")
            print("   Callback URL: [Copy from tunnel console]/webhook")
            print(f"   Verify Token: {os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'cute_bot_verify_2025_secure_token_xyz789')}")
            print("=" * 50)
        
        print("💡 Remember: Update your WhatsApp webhook with the tunnel URL!")
    else:
        print("🌐 Production environment - skipping tunnel management")
        print(f"�🔗 Webhook URL: http://{host}:{port}/webhook")
    
    print(f"🌐 Portal: http://{host}:{port}/portal")
    print(f"⚙️  Admin: http://{host}:{port}/admin")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level
    )
