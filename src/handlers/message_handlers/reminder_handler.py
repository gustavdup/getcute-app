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
            reminder_info = await self._extract_reminder_with_ai(message.content, message, user)
            
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
                    repeat_until=reminder_info.get("repeat_until"),
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
                    repeat_str = f" (repeating {repeat_type.value}"
                    if reminder_info.get("repeat_until"):
                        until_str = reminder_info["repeat_until"].strftime("%B %d, %Y")
                        repeat_str += f" until {until_str}"
                    repeat_str += ")"
                
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
    
    async def _extract_reminder_with_ai(self, content: str, message: ProcessedMessage, user=None) -> Optional[Dict[str, Any]]:
        """Use OpenAI to extract reminder information."""
        
        def create_log_message_data():
            """Helper to create enhanced message_data for logging."""
            return {
                "message_id": message.message_id,
                "user_phone": message.user_phone,
                "user_id": getattr(user, 'id', None) if user else None,
                "timestamp": message.timestamp.isoformat() if hasattr(message, 'timestamp') and message.timestamp else None,
                "content": content,
                "message_type": message.message_type
            }
        
        try:
            system_prompt = """You are an expert at extracting reminder information from text messages.
Extract the reminder details from the user's message and handle complex time calculations.

IMPORTANT: For reminders like "Remind me about X at Y time Z minutes/hours before":
1. Calculate the actual trigger_time by subtracting the "before" time from the event time
2. Set title to the main event name (e.g., "Vet visit")
3. Set description to include the original event time (e.g., "You have a vet visit at 4PM")

Return a JSON object with:
- "title": The main reminder text (what to be reminded about) - keep it concise
- "description": Detailed description including original event time when applicable
- "trigger_time": ISO datetime string when the reminder should ACTUALLY trigger (after calculations)
- "original_event_time": ISO datetime string of the original event time (if different from trigger_time)
- "repeat_type": one of "none", "daily", "weekly", "monthly", "yearly" ONLY (NO hourly, minutely, or custom intervals)
- "repeat_interval": Optional number for custom intervals
- "repeat_until": ISO datetime string when recurring reminders should stop (if specified)
- "extracted_tags": Array of relevant tags
- "calculation_error": If time calculation is impossible/illogical, explain why
- "suggested_clarification": If there's an error, suggest how user can clarify

Handle various complex formats:
- "Remind me about my vet visit at 4PM an hour before" → trigger: 3PM, title: "Vet visit", description: "You have a vet visit at 4PM"
- "Remind me 30 minutes before my meeting at 3PM" → trigger: 2:30PM, title: "Meeting", description: "You have a meeting at 3PM"  
- "Remind me about dinner reservation at 7PM, 15 minutes early" → trigger: 6:45PM, title: "Dinner reservation", description: "You have a dinner reservation at 7PM"
- "Remind me to call John at 5PM" → trigger: 5PM, title: "Call John", description: null
- "Daily reminder to take medicine at 8am" → trigger: 8AM daily, title: "Take medicine", repeat_type: "daily"
- "Remind me every day to drink my pills at 9AM" → trigger: 9AM daily, title: "Drink pills", repeat_type: "daily"
- "For the next 7 days, remind me to take my antibiotics at 9AM" → trigger: 9AM daily, title: "Take antibiotics", repeat_type: "daily", repeat_until: [7 days from now]
- "Remind me every day for the next week to take vitamins at 8am" → trigger: 8AM daily, title: "Take vitamins", repeat_type: "daily", repeat_until: [1 week from now]
- "Remind me every wednesday morning 15 minutes before 8PM that I need to take the trash out" → trigger: 7:45PM weekly (Wednesday), title: "Take trash out", repeat_type: "weekly", description: "You need to take the trash out at 8PM"
- "Weekly reminder to check emails on Monday at 10am for the next month" → trigger: 10AM weekly (Monday), title: "Check emails", repeat_type: "weekly", repeat_until: [1 month from now]
- "Remind me every month to pay rent on the 1st at noon" → trigger: 12PM monthly, title: "Pay rent", repeat_type: "monthly"

RECURRING REMINDER RULES:
- "every day/daily" → repeat_type: "daily"
- "every week/weekly" → repeat_type: "weekly" 
- "every month/monthly" → repeat_type: "monthly"
- "every year/yearly/annually" → repeat_type: "yearly"
- For weekly reminders, calculate the next occurrence of the specified day (e.g., "every Wednesday" = next Wednesday)
- For "X minutes/hours before Y on Z day" → calculate trigger_time and set appropriate repeat_type

REPEAT UNTIL RULES:
- "for the next X days/weeks/months" → calculate repeat_until date
- "until [date]" → set repeat_until to that date
- "for X times" → calculate repeat_until based on frequency and count
- If no end date specified, leave repeat_until as null for indefinite recurring

VALIDATION RULES:
- ONLY daily, weekly, monthly, or yearly repeat_type allowed (NO hourly, minutely, or custom intervals)
- If user requests hourly, every minute, every 4 hours, etc. → set "calculation_error" with helpful message
- If calculated trigger_time is in the past and it's clearly not intended for next day, set "calculation_error"
- If the "before" time is longer than reasonable (e.g., "remind me 5 hours before lunch at 1PM" when it's already 3PM), set "calculation_error"
- If times are ambiguous or conflicting, set "calculation_error"
- If repeat_until is before trigger_time, set "calculation_error"

For relative times like "tomorrow", "next week", use the current date/time as reference.
For times without dates, assume today if it's a future time, otherwise tomorrow."""
            
            # Get current time for context
            current_time = datetime.now()
            user_prompt = f"Current date/time: {current_time.isoformat()}\n\nExtract reminder from: '{content}'"
            
            response = await self.classifier.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            if not response:
                self.msg_logger.logger.warning("No response from AI for reminder extraction")
                
                # Log extraction failure for analysis
                message_data = create_log_message_data()
                
                self.msg_logger.log_ai_extraction_failure(
                    extraction_type="reminder",
                    user_message=content,
                    ai_response="Empty response from OpenAI API",
                    message_data=message_data,
                    failure_reason="AI returned empty response",
                    extra_info={"classification_context": "reminder_extraction"}
                )
                
                return None
            
            # Clean up the response text - sometimes OpenAI adds markdown formatting
            response_text = response.strip()
            
            # Handle markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove opening ```
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()
            
            # Try to find JSON in the response if it has extra text
            if not response_text.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
            
            # Parse the JSON response
            try:
                result = json.loads(response_text)
                
                # Check if there's a calculation error
                if result.get("calculation_error"):
                    self.msg_logger.logger.info(f"AI found calculation error: {result['calculation_error']}")
                    
                    # Log extraction failure for analysis
                    message_data = create_log_message_data()
                    
                    self.msg_logger.log_ai_extraction_failure(
                        extraction_type="reminder",
                        user_message=content,
                        ai_response=json.dumps(result, indent=2),
                        message_data=message_data,
                        failure_reason=f"AI calculation error: {result['calculation_error']}",
                        extra_info={
                            "suggested_clarification": result.get('suggested_clarification'),
                            "ai_result": result
                        }
                    )
                    
                    # Send helpful error message to user
                    error_message = f"⚠️ I couldn't set that reminder: {result['calculation_error']}"
                    
                    if result.get("suggested_clarification"):
                        error_message += f"\n\n💡 {result['suggested_clarification']}"
                    
                    error_message += "\n\n📝 Please send a new message to create a reminder."
                    
                    await self.whatsapp_service.send_text_message(
                        message.user_phone,
                        error_message
                    )
                    
                    return {
                        "success": False,
                        "type": "reminder_calculation_error",
                        "reason": result['calculation_error']
                    }
                
                # Validate required fields
                if not result.get("title") or not result.get("trigger_time"):
                    self.msg_logger.logger.warning(f"AI extraction missing required fields: {result}")
                    
                    # Log extraction failure for analysis
                    message_data = create_log_message_data()
                    
                    missing_fields = []
                    if not result.get("title"):
                        missing_fields.append("title")
                    if not result.get("trigger_time"):
                        missing_fields.append("trigger_time")
                    
                    self.msg_logger.log_ai_extraction_failure(
                        extraction_type="reminder",
                        user_message=content,
                        ai_response=json.dumps(result, indent=2),
                        message_data=message_data,
                        failure_reason=f"Missing required fields: {', '.join(missing_fields)}",
                        extra_info={
                            "missing_fields": missing_fields,
                            "ai_result": result
                        }
                    )
                    
                    return None
                
                # Validate repeat type - only allow daily, weekly, monthly, yearly, or none
                allowed_repeat_types = ["none", "daily", "weekly", "monthly", "yearly"]
                requested_repeat_type = result.get("repeat_type", "none").lower()
                
                if requested_repeat_type not in allowed_repeat_types:
                    self.msg_logger.logger.warning(f"Invalid repeat_type requested: {requested_repeat_type}")
                    
                    # Log extraction failure for analysis
                    message_data = create_log_message_data()
                    
                    self.msg_logger.log_ai_extraction_failure(
                        extraction_type="reminder",
                        user_message=content,
                        ai_response=json.dumps(result, indent=2),
                        message_data=message_data,
                        failure_reason=f"Invalid repeat_type '{requested_repeat_type}' - Only daily, weekly, monthly, or yearly allowed",
                        extra_info={
                            "requested_repeat_type": requested_repeat_type,
                            "allowed_types": allowed_repeat_types,
                            "ai_result": result
                        }
                    )
                    
                    return None
                
                # Parse the trigger time
                try:
                    trigger_time = datetime.fromisoformat(result["trigger_time"])
                    
                    # Only adjust to tomorrow if it's clearly meant for today but time has passed
                    # and there's no explicit date calculation involved
                    if trigger_time <= current_time and not result.get("original_event_time"):
                        from datetime import timedelta
                        trigger_time = trigger_time + timedelta(days=1)
                        
                except (ValueError, TypeError) as e:
                    self.msg_logger.logger.warning(f"Could not parse trigger_time '{result['trigger_time']}': {e}")
                    
                    # Log extraction failure for analysis
                    message_data = create_log_message_data()
                    
                    self.msg_logger.log_ai_extraction_failure(
                        extraction_type="reminder",
                        user_message=content,
                        ai_response=json.dumps(result, indent=2),
                        message_data=message_data,
                        failure_reason=f"Invalid trigger_time format: {result['trigger_time']} - {str(e)}",
                        extra_info={
                            "trigger_time_value": result['trigger_time'],
                            "parse_error": str(e),
                            "ai_result": result
                        }
                    )
                    
                    return None
                
                # Parse repeat_until if provided
                repeat_until = None
                if result.get("repeat_until"):
                    try:
                        repeat_until = datetime.fromisoformat(result["repeat_until"])
                        
                        # Validate that repeat_until is after trigger_time
                        if repeat_until <= trigger_time:
                            self.msg_logger.logger.warning(f"repeat_until ({repeat_until}) is not after trigger_time ({trigger_time})")
                            return {
                                "success": False,
                                "type": "reminder_calculation_error",
                                "reason": "End date must be after the start time"
                            }
                            
                    except (ValueError, TypeError) as e:
                        self.msg_logger.logger.warning(f"Could not parse repeat_until '{result['repeat_until']}': {e}")
                        # Don't fail the whole extraction for invalid repeat_until, just ignore it
                        repeat_until = None
                
                return {
                    "title": result["title"].strip(),
                    "description": result.get("description"),
                    "trigger_time": trigger_time,
                    "repeat_type": result.get("repeat_type", "none"),
                    "repeat_interval": result.get("repeat_interval"),
                    "repeat_until": repeat_until,
                    "extracted_tags": result.get("extracted_tags", [])
                }
                
            except json.JSONDecodeError as e:
                self.msg_logger.logger.warning(f"Could not parse AI response as JSON: {response_text[:200]}...")
                self.msg_logger.logger.warning(f"Full JSON decode error: {e}")
                
                # Log extraction failure for analysis
                message_data = create_log_message_data()
                
                self.msg_logger.log_ai_extraction_failure(
                    extraction_type="reminder",
                    user_message=content,
                    ai_response=response_text,
                    message_data=message_data,
                    failure_reason=f"JSON decode error: {str(e)}",
                    extra_info={
                        "response_preview": response_text[:500],
                        "json_error": str(e)
                    }
                )
                
                return None
                
        except Exception as e:
            self.msg_logger.logger.error(f"Error in AI reminder extraction: {e}")
            
            # Log extraction failure for analysis
            message_data = create_log_message_data()
            
            self.msg_logger.log_ai_extraction_failure(
                extraction_type="reminder",
                user_message=content,
                ai_response=f"Exception occurred: {str(e)}",
                message_data=message_data,
                failure_reason=f"Unexpected error: {type(e).__name__}: {str(e)}",
                extra_info={
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            )
            
            return None
