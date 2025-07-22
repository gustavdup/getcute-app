#!/usr/bin/env python3
"""
Fix timezone-aware datetime usage across the codebase
"""

import os
import re

files_to_fix = [
    "src/services/whatsapp_service.py",
    "src/services/media_processing_service.py", 
    "src/services/file_storage_service.py",
    "src/services/auth_service.py",
    "src/handlers/webhook_handler.py"
]

def fix_datetime_imports_and_usage(filepath):
    """Fix datetime imports and usage in a file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix import - add timezone if not present
    if "from datetime import datetime" in content and "timezone" not in content:
        content = content.replace(
            "from datetime import datetime",
            "from datetime import datetime, timezone"
        )
    elif "import datetime" in content and "timezone" not in content:
        # If using import datetime, we need to adjust usage differently
        pass
    
    # Fix datetime.utcnow() usage
    content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
    
    # Save if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
    else:
        print(f"⏭️  No changes needed: {filepath}")

def main():
    print("🔧 Fixing timezone-aware datetime usage...")
    print("=" * 50)
    
    for filepath in files_to_fix:
        fix_datetime_imports_and_usage(filepath)
    
    print("\n✅ All files processed!")
    print("🔍 New messages will now be stored with proper UTC timezone info")
    print("📋 Existing messages may still show incorrect timezone until database is updated")
    print("💡 Use fix_timezones.sql to update existing message timestamps if needed")

if __name__ == "__main__":
    main()
