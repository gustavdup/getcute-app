"""
Media Processing Monitor Service
Runs as a background task to monitor media processing health
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class MediaProcessingMonitor:
    """Background service to monitor media processing health."""
    
    def __init__(self, db_service: Optional[SupabaseService] = None):
        self.db_service = db_service or SupabaseService()
        self.scheduler = AsyncIOScheduler()
        self.last_check_time: Optional[datetime] = None
        self.is_running = False
        
    async def start(self):
        """Start the media processing monitor."""
        if self.is_running:
            logger.warning("Media processing monitor is already running")
            return
            
        try:
            # Schedule media processing health check every hour
            self.scheduler.add_job(
                self._check_media_processing_health,
                trigger=IntervalTrigger(hours=1),  # Check every hour
                id="media_processing_health_check",
                name="Media Processing Health Check",
                max_instances=1,
                coalesce=True
            )
            
            # Schedule detailed report every 6 hours
            self.scheduler.add_job(
                self._generate_detailed_report,
                trigger=IntervalTrigger(hours=6),  # Detailed report every 6 hours
                id="media_processing_detailed_report",
                name="Media Processing Detailed Report",
                max_instances=1,
                coalesce=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Media Processing Monitor started - checking every hour")
            
        except Exception as e:
            logger.error(f"Failed to start Media Processing Monitor: {e}")
            raise
    
    async def stop(self):
        """Stop the media processing monitor."""
        if not self.is_running:
            return
            
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Media Processing Monitor stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Media Processing Monitor: {e}")
    
    async def _check_media_processing_health(self):
        """Quick health check for media processing."""
        try:
            logger.info("Running media processing health check...")
            
            # Check last 2 hours for recent activity
            since_time = datetime.now(timezone.utc) - timedelta(hours=2)
            since_iso = since_time.isoformat()
            
            # Query recent media files
            result = self.db_service.admin_client.table('files').select(
                'filename, file_type, upload_status, transcription_status'
            ).gte('created_at', since_iso).execute()
            
            recent_files = result.data or []
            
            if not recent_files:
                logger.info("No media files processed in last 2 hours")
                return
            
            # Analyze health
            issues = []
            audio_files = [f for f in recent_files if f.get('file_type') == 'audio']
            failed_uploads = [f for f in recent_files if f.get('upload_status') == 'failed']
            failed_transcriptions = [f for f in recent_files if f.get('transcription_status') == 'failed']
            
            if failed_uploads:
                issues.append(f"{len(failed_uploads)} failed uploads")
                logger.warning(f"WARNING: {len(failed_uploads)} media files failed to upload")
            
            if failed_transcriptions:
                issues.append(f"{len(failed_transcriptions)} failed transcriptions")
                logger.warning(f"WARNING: {len(failed_transcriptions)} audio files failed transcription")
            
            if not issues:
                logger.info(f"Media processing healthy - {len(recent_files)} files processed successfully")
            else:
                logger.error(f"Media processing issues detected: {', '.join(issues)}")
                
        except Exception as e:
            logger.error(f"Error in media processing health check: {e}")
    
    async def _generate_detailed_report(self):
        """Generate detailed media processing report."""
        try:
            logger.info("Generating detailed media processing report...")
            
            # Check last 24 hours
            since_time = datetime.now(timezone.utc) - timedelta(hours=24)
            since_iso = since_time.isoformat()
            
            # Query recent files
            result = self.db_service.admin_client.table('files').select(
                'filename, file_type, mime_type, file_size, upload_status, transcription_status, created_at'
            ).gte('created_at', since_iso).order('created_at', desc=True).limit(100).execute()
            
            recent_files = result.data or []
            
            if not recent_files:
                logger.info("No media files found in last 24 hours")
                return
            
            # Analyze files
            stats = self._analyze_files(recent_files)
            
            # Log summary
            logger.info(f"Media Processing Report (24h):")
            logger.info(f"   Total files: {stats['total_files']}")
            logger.info(f"   Audio files: {stats['audio_count']} ({stats['transcribed_count']} transcribed)")
            logger.info(f"   Image files: {stats['image_count']}")
            logger.info(f"   Document files: {stats['document_count']}")
            logger.info(f"   Successful uploads: {stats['successful_uploads']}")
            logger.info(f"   Failed uploads: {stats['failed_uploads']}")
            
            if stats['failed_uploads'] > 0 or stats['failed_transcriptions'] > 0:
                logger.warning(f"Issues detected - failed uploads: {stats['failed_uploads']}, failed transcriptions: {stats['failed_transcriptions']}")
            else:
                logger.info("All media processing working perfectly!")
                
        except Exception as e:
            logger.error(f"Error generating detailed report: {e}")
    
    def _analyze_files(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze file statistics."""
        stats = {
            'total_files': len(files),
            'audio_count': 0,
            'image_count': 0,
            'document_count': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'transcribed_count': 0,
            'failed_transcriptions': 0
        }
        
        for file_data in files:
            file_type = file_data.get('file_type', 'unknown')
            upload_status = file_data.get('upload_status', 'unknown')
            transcription_status = file_data.get('transcription_status', 'none')
            
            # Count by type
            if file_type == 'audio':
                stats['audio_count'] += 1
                if transcription_status == 'completed':
                    stats['transcribed_count'] += 1
                elif transcription_status == 'failed':
                    stats['failed_transcriptions'] += 1
            elif file_type == 'image':
                stats['image_count'] += 1
            elif file_type == 'document':
                stats['document_count'] += 1
            
            # Count by status
            if upload_status == 'completed':
                stats['successful_uploads'] += 1
            elif upload_status == 'failed':
                stats['failed_uploads'] += 1
        
        return stats
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        return {
            "is_running": self.is_running,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "scheduler_running": self.scheduler.running if self.scheduler else False,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ] if self.scheduler else []
        }

# Global instance
_media_monitor: Optional[MediaProcessingMonitor] = None

async def get_media_monitor() -> MediaProcessingMonitor:
    """Get the global media processing monitor instance."""
    global _media_monitor
    if _media_monitor is None:
        _media_monitor = MediaProcessingMonitor()
    return _media_monitor
