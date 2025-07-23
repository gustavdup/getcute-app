"""
Reminder scheduler service that checks for due reminders and sends notifications.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.services.supabase_service import SupabaseService
from src.services.whatsapp_service import WhatsAppService
from src.models.database import Reminder, User

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Manages reminder notifications using APScheduler."""
    
    def __init__(self, db_service: SupabaseService, whatsapp_service: WhatsAppService):
        """Initialize the reminder scheduler."""
        self.db_service = db_service
        self.whatsapp_service = whatsapp_service
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self._sent_reminders = set()  # Track recently sent reminders to prevent duplicates
        
    async def start(self):
        """Start the reminder scheduler."""
        if self.is_running:
            logger.warning("Reminder scheduler is already running")
            return
            
        try:
            # Add job to check reminders every minute
            self.scheduler.add_job(
                self._check_and_send_reminders,
                trigger=IntervalTrigger(minutes=1),
                id='reminder_checker',
                name='Check Due Reminders',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Reminder scheduler started - checking every minute")
            
        except Exception as e:
            logger.error(f"Failed to start reminder scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the reminder scheduler."""
        if not self.is_running:
            return
            
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Reminder scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping reminder scheduler: {e}")
    
    async def _check_and_send_reminders(self):
        """Check for due reminders and send WhatsApp notifications."""
        try:
            logger.debug("Checking for due reminders...")
            
            # First, check for missed recurring reminders (failsafe)
            await self._check_missed_recurring_reminders()
            
            # Get reminders due in the next 1 minute
            due_reminders = await self.db_service.get_due_reminders(time_window_minutes=1)
            
            if not due_reminders:
                logger.debug("No due reminders found")
                return
                
            logger.info(f"Found {len(due_reminders)} due reminders")
            
            for reminder in due_reminders:
                # Create unique key for this reminder occurrence
                reminder_key = f"{reminder.id}_{reminder.trigger_time.isoformat()}"
                
                # Skip if we've already sent this specific reminder occurrence
                if reminder_key in self._sent_reminders:
                    logger.debug(f"Skipping duplicate reminder {reminder_key}")
                    continue
                
                # Send the reminder
                success = await self._send_reminder_notification(reminder)
                
                # Track successful sends to prevent duplicates
                if success:
                    self._sent_reminders.add(reminder_key)
                    
                    # Clean up old entries (keep only last hour)
                    from datetime import timedelta
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    self._sent_reminders = {
                        key for key in self._sent_reminders 
                        if not any(key.endswith(old_time) for old_time in [
                            t.isoformat() for t in [cutoff_time - timedelta(minutes=i) for i in range(0, 60)]
                        ])
                    }
                
        except Exception as e:
            logger.error(f"Error checking due reminders: {e}")
    
    async def _check_missed_recurring_reminders(self):
        """Check for missed recurring reminders and create them (failsafe mechanism)."""
        try:
            # Only check for missed reminders every hour to avoid overhead
            if not hasattr(self, '_last_missed_check'):
                self._last_missed_check = datetime.now() - timedelta(hours=2)
            
            if datetime.now() - self._last_missed_check < timedelta(hours=1):
                return
            
            logger.debug("Checking for missed recurring reminders...")
            
            # Look back 32 days for missed recurring reminders (to catch monthly ones)
            missed_reminders = await self.db_service.get_missed_recurring_reminders(hours_back=768)  # 32 days
            
            if missed_reminders:
                logger.warning(f"Found {len(missed_reminders)} broken recurring chains - creating recovery reminders")
                
                # Save the recovery reminders to database
                for recovery_reminder in missed_reminders:
                    try:
                        await self.db_service.save_reminder(recovery_reminder)
                        logger.info(f"Created recovery reminder to continue chain: {recovery_reminder.title} scheduled for {recovery_reminder.trigger_time}")
                    except Exception as e:
                        logger.error(f"Failed to save recovery reminder {recovery_reminder.title}: {e}")
            
            # Update last check time
            self._last_missed_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking missed recurring reminders: {e}")
    
    async def _send_reminder_notification(self, reminder: Reminder) -> bool:
        """Send WhatsApp notification for a specific reminder."""
        try:
            # Get user information
            user = await self.db_service.get_user(reminder.user_id)
            if not user:
                logger.error(f"User not found for reminder {reminder.id}")
                return False
            
            # Format reminder message
            reminder_text = self._format_reminder_message(reminder)
            
            # Send WhatsApp message
            success = await self.whatsapp_service.send_text_message(
                to=user.phone_number,
                message=reminder_text
            )
            
            if success:
                # Mark reminder as completed (sent)
                await self._mark_reminder_as_sent(reminder)
                logger.info(f"Reminder notification sent to {user.phone_number}: {reminder.title}")
                return True
            else:
                logger.error(f"Failed to send reminder notification to {user.phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending reminder notification for {reminder.id}: {e}")
            return False
    
    def _format_reminder_message(self, reminder: Reminder) -> str:
        """Format the reminder message for WhatsApp."""
        message = f"⏰ *Reminder*\n\n"
        message += f"📝 {reminder.title}"
        
        if reminder.description:
            message += f"\n\n{reminder.description}"
        
        # Add current time info
        now = datetime.now()
        current_time_str = now.strftime("%I:%M %p")
        message += f"\n\n🕐 Reminder sent at: {current_time_str}"
        
        # Add original scheduled time if different from now
        scheduled_time_str = reminder.trigger_time.strftime("%I:%M %p")
        if scheduled_time_str != current_time_str:
            message += f"\n🎯 Originally scheduled for: {scheduled_time_str}"
        
        # Add tags if any
        if reminder.tags:
            tags_str = " ".join([f"#{tag}" for tag in reminder.tags])
            message += f"\n\n🏷️ {tags_str}"
        
        return message
    
    async def _mark_reminder_as_sent(self, reminder: Reminder):
        """Mark a reminder as sent and handle recurring reminders."""
        try:
            from datetime import timedelta
            from src.models.database import RepeatType
            
            # Handle recurring reminders FIRST (before marking as sent)
            if reminder.repeat_type != RepeatType.NONE:
                # Calculate next trigger time based on repeat type
                next_trigger = None
                
                if reminder.repeat_type == RepeatType.DAILY:
                    next_trigger = reminder.trigger_time + timedelta(days=1)
                elif reminder.repeat_type == RepeatType.WEEKLY:
                    next_trigger = reminder.trigger_time + timedelta(weeks=1)
                elif reminder.repeat_type == RepeatType.MONTHLY:
                    # Add 30 days for monthly (approximate)
                    next_trigger = reminder.trigger_time + timedelta(days=30)
                elif reminder.repeat_type == RepeatType.YEARLY:
                    next_trigger = reminder.trigger_time + timedelta(days=365)
                
                if next_trigger:
                    # Check if reminder has passed its repeat_until date
                    if reminder.repeat_until and next_trigger > reminder.repeat_until:
                        # Recurring reminder has reached its end date
                        reminder.is_active = False
                        reminder.completed_at = datetime.now()
                        logger.info(f"Recurring reminder {reminder.id} completed - reached repeat_until date: {reminder.repeat_until}")
                    else:
                        # Create new reminder entry for next occurrence instead of updating existing one
                        # This prevents race conditions and provides better audit trail
                        from src.models.database import Reminder
                        from uuid import uuid4
                        
                        next_reminder = Reminder(
                            id=uuid4(),
                            user_id=reminder.user_id,
                            title=reminder.title,
                            description=reminder.description,
                            trigger_time=next_trigger,
                            repeat_type=reminder.repeat_type,
                            repeat_interval=reminder.repeat_interval,
                            repeat_until=reminder.repeat_until,
                            tags=reminder.tags,
                            is_active=True,
                            created_at=datetime.now()
                        )
                        
                        # Save the next occurrence
                        await self.db_service.save_reminder(next_reminder)
                        
                        # Mark current occurrence as completed
                        reminder.is_active = False
                        reminder.completed_at = datetime.now()
                        
                        logger.info(f"Created next occurrence of recurring reminder {reminder.id} -> {next_reminder.id} scheduled for: {next_trigger}")
                else:
                    # If we couldn't calculate next occurrence, deactivate
                    reminder.is_active = False
                    reminder.completed_at = datetime.now()
            else:
                # Non-recurring reminder - mark as inactive and completed
                reminder.is_active = False
                reminder.completed_at = datetime.now()
            
            # Save current reminder to database
            await self.db_service.save_reminder(reminder)
            
            logger.debug(f"Marked reminder {reminder.id} as sent (recurring: {reminder.repeat_type != RepeatType.NONE})")
            
        except Exception as e:
            logger.error(f"Error marking reminder {reminder.id} as sent: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status information."""
        next_run = None
        if self.scheduler and self.scheduler.get_job('reminder_checker'):
            job = self.scheduler.get_job('reminder_checker')
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        
        return {
            "is_running": self.is_running,
            "jobs": len(self.scheduler.get_jobs()) if self.scheduler else 0,
            "next_run": next_run
        }


# Global scheduler instance
reminder_scheduler = None


async def get_reminder_scheduler() -> ReminderScheduler:
    """Get the global reminder scheduler instance."""
    global reminder_scheduler
    
    if reminder_scheduler is None:
        # Import here to avoid circular imports
        from src.services.supabase_service import SupabaseService
        from src.services.whatsapp_service import WhatsAppService
        
        db_service = SupabaseService()
        whatsapp_service = WhatsAppService()
        reminder_scheduler = ReminderScheduler(db_service, whatsapp_service)
    
    return reminder_scheduler
