#!/usr/bin/env python3
"""
Fix relative imports in all Python files in the src directory.
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix relative imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace relative imports with absolute imports
        # Pattern: from ..module import something -> from module import something
        # Pattern: from ..submodule.module import something -> from submodule.module import something
        
        original_content = content
        
        # Fix ..config imports
        content = re.sub(r'from \.\.config\.', 'from config.', content)
        
        # Fix ..models imports  
        content = re.sub(r'from \.\.models\.', 'from models.', content)
        
        # Fix ..services imports
        content = re.sub(r'from \.\.services\.', 'from services.', content)
        
        # Fix ..handlers imports
        content = re.sub(r'from \.\.handlers\.', 'from handlers.', content)
        
        # Fix ..workflows imports
        content = re.sub(r'from \.\.workflows\.', 'from workflows.', content)
        
        # Fix ..ai imports
        content = re.sub(r'from \.\.ai\.', 'from ai.', content)
        
        # Fix ..utils imports
        content = re.sub(r'from \.\.utils\.', 'from utils.', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"🔍 No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix imports in all Python files in src directory."""
    src_dir = Path(__file__).parent / "src"
    
    if not src_dir.exists():
        print("❌ src directory not found")
        return
    
    print("🔧 Fixing relative imports in src directory...")
    
    fixed_count = 0
    total_count = 0
    
    # Process all .py files recursively
    for py_file in src_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Total files processed: {total_count}")
    print(f"   Files with fixes: {fixed_count}")
    print(f"   Files unchanged: {total_count - fixed_count}")

if __name__ == "__main__":
    main()
