"""
Reminder handler for processing reminder-related messages.
"""
from typing import Any, Dict, Optional
from datetime import datetime
import json
from src.models.database import Reminder, RepeatType
from src.models.message_types import ProcessedMessage
from src.utils.logger import MessageProcessingLogger
from .base_handler import BaseHandler


class ReminderHandler(BaseHandler):
    """Handler for reminder messages."""
    
    def __init__(self, db_service, whatsapp_service, classifier):
        """Initialize with services and classifier for AI completions."""
        self.db_service = db_service
        self.whatsapp_service = whatsapp_service
        self.classifier = classifier  # Use classifier for AI completions
        self.msg_logger = MessageProcessingLogger()
    
    async def can_handle(self, message: ProcessedMessage, user, classification: Dict[str, Any]) -> bool:
        """Check if this message is a reminder."""
        return classification.get("message_type") == "reminder"
    
    async def handle(self, message: ProcessedMessage, user, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Process reminder messages using AI extraction."""
        message_data = self._create_message_data(message)
        
        try:
            self.msg_logger.log_message_stage("REMINDER_PROCESSING", message_data)
            
            # Use AI to extract reminder information
            reminder_info = await self._extract_reminder_with_ai(message.content)
            
            if reminder_info:
                self.msg_logger.log_message_stage("REMINDER_PARSED", message_data, 
                                                {
                                                    "title": reminder_info["title"],
                                                    "trigger_time": reminder_info["trigger_time"].isoformat(),
                                                    "repeat_type": reminder_info.get("repeat_type", "none")
                                                })
                
                # Save reminder to database
                if not user.id:
                    raise Exception("User ID is None when creating reminder")
                
                # Map repeat type string to enum
                repeat_type_map = {
                    "none": RepeatType.NONE,
                    "daily": RepeatType.DAILY,
                    "weekly": RepeatType.WEEKLY,
                    "monthly": RepeatType.MONTHLY,
                    "yearly": RepeatType.YEARLY
                }
                repeat_type = repeat_type_map.get(reminder_info.get("repeat_type", "none"), RepeatType.NONE)
                
                reminder = Reminder(
                    user_id=user.id,
                    title=reminder_info["title"],
                    description=reminder_info.get("description"),
                    trigger_time=reminder_info["trigger_time"],
                    repeat_type=repeat_type,
                    repeat_interval=reminder_info.get("repeat_interval"),
                    tags=reminder_info.get("extracted_tags", []),
                    is_active=True,
                    created_at=datetime.now()
                )
                
                saved_reminder = await self.db_service.save_reminder(reminder)
                self.msg_logger.log_database_operation("INSERT", "reminders", str(saved_reminder.id), success=True)
                
                # Send confirmation message
                time_str = reminder_info["trigger_time"].strftime("%B %d, %Y at %I:%M %p")
                repeat_str = ""
                if repeat_type != RepeatType.NONE:
                    repeat_str = f" (repeating {repeat_type.value})"
                
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    f"⏰ Reminder set: '{reminder_info['title']}' on {time_str}{repeat_str}"
                )
                
                self.msg_logger.log_success_stage("REMINDER_COMPLETE", message_data, 
                                               f"Reminder saved: {reminder_info['title']}")
                
                return {
                    "success": True,
                    "type": "reminder",
                    "reminder_id": str(saved_reminder.id),
                    "title": reminder_info["title"]
                }
            else:
                # Could not extract reminder info
                self.msg_logger.log_message_stage("REMINDER_PARSE_FAILED", message_data)
                
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "I detected this might be a reminder, but I couldn't extract the details. "
                    "Could you try rephrasing? For example: 'Remind me to call John tomorrow at 2pm'"
                )
                
                return {
                    "success": False,
                    "type": "reminder_parse_failed",
                    "reason": "Could not extract reminder information"
                }
                
        except Exception as e:
            self.msg_logger.log_error_stage("REMINDER_ERROR", e, message_data)
            
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "I had trouble setting that reminder. Could you try again?"
            )
            
            return {
                "success": False,
                "type": "reminder_error",
                "error": str(e)
            }
    
    async def _extract_reminder_with_ai(self, content: str) -> Optional[Dict[str, Any]]:
        """Use OpenAI to extract reminder information."""
        try:
            system_prompt = """You are an expert at extracting reminder information from text messages.
Extract the reminder details from the user's message.

Return a JSON object with:
- "title": The main reminder text (what to be reminded about)
- "description": Optional longer description
- "trigger_time": ISO datetime string when the reminder should trigger
- "repeat_type": one of "none", "daily", "weekly", "monthly", "yearly"
- "repeat_interval": Optional number for custom intervals
- "extracted_tags": Array of relevant tags

Handle various formats like:
- "Remind me to call John tomorrow at 2pm"
- "Set reminder for doctor appointment on Friday at 9am"
- "Daily reminder to take medicine at 8am"
- "Remind me every week to check emails"
- "Remind me to take a break in 15 minutes"

For relative times like "tomorrow", "next week", use the current date/time as reference.
For times without dates, assume today if it's a future time, otherwise tomorrow.
"""
            
            # Get current time for context
            current_time = datetime.now()
            user_prompt = f"Current date/time: {current_time.isoformat()}\n\nExtract reminder from: '{content}'"
            
            response = await self.classifier.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            if not response:
                self.msg_logger.logger.warning("No response from AI for reminder extraction")
                return None
            
            # Parse the JSON response
            try:
                result = json.loads(response.strip())
                
                # Validate required fields
                if not result.get("title") or not result.get("trigger_time"):
                    self.msg_logger.logger.warning(f"AI extraction missing required fields: {result}")
                    return None
                
                # Parse the trigger time
                try:
                    trigger_time = datetime.fromisoformat(result["trigger_time"])
                    
                    # Make sure it's in the future
                    if trigger_time <= current_time:
                        # If the time has passed today, assume tomorrow
                        from datetime import timedelta
                        trigger_time = trigger_time + timedelta(days=1)
                        
                except (ValueError, TypeError) as e:
                    self.msg_logger.logger.warning(f"Could not parse trigger_time '{result['trigger_time']}': {e}")
                    return None
                
                return {
                    "title": result["title"].strip(),
                    "description": result.get("description"),
                    "trigger_time": trigger_time,
                    "repeat_type": result.get("repeat_type", "none"),
                    "repeat_interval": result.get("repeat_interval"),
                    "extracted_tags": result.get("extracted_tags", [])
                }
                
            except json.JSONDecodeError as e:
                self.msg_logger.logger.warning(f"Could not parse AI response as JSON: {response}")
                return None
                
        except Exception as e:
            self.msg_logger.logger.error(f"Error in AI reminder extraction: {e}")
            return None
