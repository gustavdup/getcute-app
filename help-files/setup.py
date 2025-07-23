#!/usr/bin/env python3
"""
Setup script for the Cute WhatsApp Bot development environment.
"""
import sys
import subprocess
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def check_python_version():
    """Check if Python version is 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def main():
    """Main setup function."""
    print("🤖💚 Cute WhatsApp Bot - Development Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the correct directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Create virtual environment if it doesn't exist
    if not Path("venv").exists():
        if not run_command("python -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation command based on OS
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Upgrade pip
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        sys.exit(1)
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python packages"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            if os.name == 'nt':  # Windows
                run_command("copy .env.example .env", "Creating .env file from template")
            else:  # Unix/Linux/macOS
                run_command("cp .env.example .env", "Creating .env file from template")
            print("📝 Please edit .env file with your actual API keys and configuration")
        else:
            print("⚠️  .env.example not found, please create .env file manually")
    else:
        print("✅ .env file already exists")
    
    # Create necessary directories
    directories = [
        "logs",
        "uploads",
        "portal/static/css",
        "portal/static/js", 
        "portal/static/images",
        "admin/templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Created necessary directories")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your API keys:")
    print("   - SUPABASE_URL and SUPABASE_KEY")
    print("   - OPENAI_API_KEY") 
    print("   - WHATSAPP_ACCESS_TOKEN and related WhatsApp API settings")
    print("\n2. Set up your Supabase database:")
    print("   - Create a new Supabase project")
    print("   - Enable the pgvector extension")
    print("   - Run the database migrations (to be created)")
    print("\n3. Set up WhatsApp Business API:")
    print("   - Create a WhatsApp Business account")
    print("   - Get API credentials")
    print("   - Configure webhook URL")
    
    if os.name == 'nt':  # Windows
        print(f"\n4. Activate virtual environment: {activate_cmd}")
        print("5. Run the application: python src\\main.py")
    else:  # Unix/Linux/macOS
        print(f"\n4. Activate virtual environment: {activate_cmd}")
        print("5. Run the application: python src/main.py")
    
    print("\n6. Access the admin panel at: http://localhost:8000/admin")
    print("\n💡 For development, you can use the test webhook endpoint:")
    print("   POST http://localhost:8000/webhook/test")


if __name__ == "__main__":
    main()
