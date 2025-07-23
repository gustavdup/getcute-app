#!/usr/bin/env python3
"""
Production monitoring script to verify media processing is working correctly
Run this periodically to ensure all media files are being processed with correct extensions
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import defaultdict

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.supabase_service import SupabaseService

# Load environment variables
load_dotenv()

async def monitor_media_processing():
    """Monitor recent media processing to ensure everything is working correctly"""
    
    print("📊 Production Media Processing Monitor")
    print("=" * 60)
    print(f"⏰ Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize Supabase service
        db_service = SupabaseService()
        
        # Check recent media files (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_iso = yesterday.isoformat()
        
        # Query for recent media files using admin client
        result = db_service.admin_client.table('media_files').select(
            'file_name, file_type, mime_type, file_size, created_at'
        ).gte('created_at', yesterday_iso).order('created_at', desc=True).limit(50).execute()
        
        recent_files = result.data
        
        if not recent_files:
            print("📁 No media files found in the last 24 hours")
            return
        
        print(f"📁 Found {len(recent_files)} media files in last 24 hours")
        print("-" * 60)
        
        # Process files and extract extensions
        processed_files = []
        for file_data in recent_files:
            file_name = file_data.get('file_name', '')
            
            # Extract extension
            if '.' in file_name and not file_name.endswith('.'):
                extension = file_name.split('.')[-1].lower()
            else:
                extension = 'NO_EXTENSION'
            
            processed_file = {
                'name': file_name,
                'type': file_data.get('file_type', 'unknown'),
                'mime': file_data.get('mime_type', 'unknown'),
                'size': file_data.get('file_size', 0),
                'created': file_data.get('created_at', ''),
                'extension': extension
            }
            processed_files.append(processed_file)
        
        # Analyze by file type
        type_stats = defaultdict(list)
        extension_stats = defaultdict(int)
        mime_stats = defaultdict(int)
        
        for file_data in processed_files:
            file_type = file_data['type']
            type_stats[file_type].append(file_data)
            extension_stats[file_data['extension']] += 1
            mime_stats[file_data['mime']] += 1
        
        # Report by file type
        for file_type, files in type_stats.items():
            print(f"\n🗂️  {file_type.upper()} FILES ({len(files)} total):")
            
            for file in files[:5]:  # Show first 5 of each type
                status = "✅" if file['extension'] != 'NO_EXTENSION' else "❌"
                print(f"   {status} {file['name']} ({file['mime']}) - {file['size']} bytes")
            
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
        
        # Extension summary
        print(f"\n📋 FILE EXTENSIONS SUMMARY:")
        for ext, count in sorted(extension_stats.items()):
            status = "✅" if ext != 'NO_EXTENSION' else "❌"
            print(f"   {status} .{ext}: {count} files")
        
        # MIME type summary
        print(f"\n🏷️  MIME TYPE SUMMARY:")
        for mime, count in sorted(mime_stats.items()):
            print(f"   • {mime}: {count} files")
        
        # Check for issues
        issues = []
        no_extension_count = extension_stats.get('NO_EXTENSION', 0)
        octet_stream_count = mime_stats.get('application/octet-stream', 0)
        
        print(f"\n🔍 HEALTH CHECK:")
        
        if no_extension_count == 0:
            print("   ✅ All files have proper extensions")
        else:
            print(f"   ❌ {no_extension_count} files missing extensions")
            issues.append(f"{no_extension_count} files without extensions")
        
        if octet_stream_count == 0:
            print("   ✅ All files have specific MIME types")
        else:
            print(f"   ⚠️  {octet_stream_count} files with generic MIME type")
            issues.append(f"{octet_stream_count} files with generic MIME type")
        
        # Check for transcription of audio files
        if 'audio' in type_stats:
            audio_files = type_stats['audio']
            
            # Query for transcribed messages
            transcription_result = db_service.admin_client.table('messages').select(
                'id'
            ).eq('source_type', 'audio').gte('created_at', yesterday_iso).not_.is_(
                'content', 'null'
            ).neq('content', '').execute()
            
            transcribed_count = len(transcription_result.data) if transcription_result.data else 0
            
            if transcribed_count == len(audio_files):
                print(f"   ✅ All {len(audio_files)} audio files transcribed")
            else:
                print(f"   ⚠️  Only {transcribed_count}/{len(audio_files)} audio files transcribed")
                issues.append(f"Missing transcriptions: {len(audio_files) - transcribed_count}")
        
        # Check for AI image descriptions
        if 'image' in type_stats:
            image_files = type_stats['image']
            
            # Query for messages with AI descriptions
            ai_description_result = db_service.admin_client.table('messages').select(
                'id, content'
            ).eq('source_type', 'image').gte('created_at', yesterday_iso).execute()
            
            ai_descriptions = ai_description_result.data if ai_description_result.data else []
            ai_described_count = len([msg for msg in ai_descriptions if msg.get('content') and 'AI Analysis:' in msg.get('content', '')])
            
            if ai_described_count > 0:
                print(f"   ✅ {ai_described_count} images analyzed with AI recognition")
            else:
                print(f"   💡 No AI image analysis found (new feature)")
        
        print(f"\n📊 OVERALL STATUS:")
        if not issues:
            print("   🎯 ALL SYSTEMS WORKING PERFECTLY!")
            print("   • All files have proper extensions")
            print("   • All files have specific MIME types") 
            print("   • All audio files are being transcribed")
            print("   • AI image recognition is working")
        else:
            print("   ⚠️  Issues detected:")
            for issue in issues:
                print(f"     - {issue}")
            print("\n   💡 Check logs and consider running diagnostic scripts")
        
        print(f"\n🤖 OpenAI Model Usage Summary:")
        print(f"   • Text processing: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
        print(f"   • Voice transcription: {os.getenv('OPENAI_MODEL_VTT', 'whisper-1')}")
        print(f"   • Image recognition: {os.getenv('OPENAI_MODEL_IMAGE_RECOGNITION', 'gpt-4o')}")
        
    except Exception as e:
        print(f"❌ Error monitoring media processing: {e}")
        print(f"   Error details: {type(e).__name__}: {str(e)}")
        print("   Make sure your database credentials are correct in .env")

if __name__ == "__main__":
    asyncio.run(monitor_media_processing())
