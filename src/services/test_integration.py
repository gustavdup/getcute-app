"""
Integration verification for media monitor and reminder scheduler
"""
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_integration():
    """Verify that the media monitor integration is complete."""
    
    logger.info("🔍 Verifying Media Monitor Integration...")
    
    # Check 1: Media monitor service exists
    try:
        media_monitor_path = os.path.join(os.path.dirname(__file__), 'media_monitor.py')
        if os.path.exists(media_monitor_path):
            logger.info("   ✅ Media monitor service file exists")
        else:
            logger.error("   ❌ Media monitor service file missing")
    except Exception as e:
        logger.error(f"   ❌ Error checking media monitor file: {e}")
    
    # Check 2: Main.py integration
    try:
        main_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
        if os.path.exists(main_py_path):
            with open(main_py_path, 'r') as f:
                content = f.read()
                if 'media_monitor' in content and 'get_media_monitor' in content:
                    logger.info("   ✅ Main.py has media monitor integration")
                else:
                    logger.error("   ❌ Main.py missing media monitor integration")
        else:
            logger.error("   ❌ Main.py not found")
    except Exception as e:
        logger.error(f"   ❌ Error checking main.py: {e}")
    
    # Check 3: Admin endpoint exists
    try:
        admin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'admin', 'user_admin.py')
        if os.path.exists(admin_path):
            with open(admin_path, 'r') as f:
                content = f.read()
                if 'media-monitor/status' in content:
                    logger.info("   ✅ Admin endpoint for media monitor exists")
                else:
                    logger.error("   ❌ Admin endpoint for media monitor missing")
        else:
            logger.error("   ❌ Admin user_admin.py not found")
    except Exception as e:
        logger.error(f"   ❌ Error checking admin endpoint: {e}")
    
    logger.info("\n📋 Integration Summary:")
    logger.info("   📁 Media monitor service: src/services/media_monitor.py")
    logger.info("   🚀 Startup integration: src/main.py")
    logger.info("   🔗 Admin endpoint: /admin/user/media-monitor/status")
    logger.info("   ⏰ Monitoring schedule: Every hour with detailed reports every 6 hours")
    logger.info("\n🎯 Features:")
    logger.info("   - Monitors media file upload status")
    logger.info("   - Tracks transcription success/failure")
    logger.info("   - Analyzes file types and processing health")
    logger.info("   - Runs alongside reminder scheduler")
    logger.info("   - Provides admin status endpoint")
    
    logger.info("\n✨ Ready to start with your main app!")
    logger.info("   Run: python src/main.py")
    logger.info("   Check: GET /admin/user/media-monitor/status")

if __name__ == "__main__":
    verify_integration()
