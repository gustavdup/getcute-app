"""
Birthday handler for processing birthday-related messages.
Uses AI to extract birthday information from various message formats.
"""
from typing import Any, Dict, Optional
from datetime import datetime
import json
from src.models.database import Birthday
from src.models.message_types import ProcessedMessage, BirthdayExtraction
from src.utils.logger import MessageProcessingLogger
from .base_handler import BaseHandler


class BirthdayHandler(BaseHandler):
    """Handler for birthday-related messages."""
    
    def __init__(self, db_service, whatsapp_service, classifier):
        """Initialize with services and classifier for AI completions."""
        self.db_service = db_service
        self.whatsapp_service = whatsapp_service
        self.classifier = classifier  # Use classifier for AI completions
        self.msg_logger = MessageProcessingLogger()
    
    async def can_handle(self, message: ProcessedMessage, user, classification: Dict[str, Any]) -> bool:
        """Check if this message contains birthday information."""
        return classification.get("message_type") == "birthday"
    
    async def handle(self, message: ProcessedMessage, user, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Process birthday messages using AI extraction."""
        message_data = self._create_message_data(message)
        
        try:
            self.msg_logger.log_message_stage("BIRTHDAY_PROCESSING", message_data)
            
            # Use AI to extract birthday information
            birthday_info = await self._extract_birthday_with_ai(message.content)
            
            if birthday_info:
                self.msg_logger.log_message_stage("BIRTHDAY_PARSED", message_data, 
                                                {
                                                    "person_name": birthday_info["person_name"],
                                                    "birthdate": birthday_info["birthdate"].isoformat(),
                                                    "year_known": birthday_info.get("year_known", True)
                                                })
                
                # Save birthday to database
                if not user.id:
                    raise Exception("User ID is None when creating birthday")
                
                birthday = Birthday(
                    user_id=user.id,
                    person_name=birthday_info["person_name"],
                    birthdate=birthday_info["birthdate"],
                    created_at=datetime.now()
                )
                
                saved_birthday = await self.db_service.save_birthday(birthday)
                self.msg_logger.log_database_operation("INSERT", "birthdays", str(saved_birthday.id), success=True)
                
                # Send confirmation message
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    f"🎂 I've saved {birthday_info['person_name']}'s birthday on {birthday_info['birthdate'].strftime('%B %d')}!"
                )
                
                self.msg_logger.log_success_stage("BIRTHDAY_COMPLETE", message_data, 
                                               f"Birthday saved for {birthday_info['person_name']}")
                
                return {
                    "success": True,
                    "type": "birthday",
                    "birthday_id": str(saved_birthday.id),
                    "person_name": birthday_info["person_name"]
                }
            else:
                # Could not extract birthday info, log failure
                self.msg_logger.log_message_stage("BIRTHDAY_PARSE_FAILED", message_data)
                
                # Still send a helpful message to the user
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "I detected this might be a birthday, but I couldn't extract the details. "
                    "Could you try rephrasing? Examples:\n"
                    "• 'John's birthday is March 15th'\n"
                    "• 'My wife's birthday is 3 November'\n" 
                    "• 'Dad's bday = 12 July 1965'\n"
                    "• 'Brother birthday is Feb 22'"
                )
                
                return {
                    "success": False,
                    "type": "birthday_parse_failed",
                    "reason": "Could not extract birthday information"
                }
                
        except Exception as e:
            self.msg_logger.log_error_stage("BIRTHDAY_ERROR", e, message_data)
            
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "I had trouble processing that birthday. Could you try again?"
            )
            
            return {
                "success": False,
                "type": "birthday_error",
                "error": str(e)
            }
    
    async def _extract_birthday_with_ai(self, content: str) -> Optional[Dict[str, Any]]:
        """Use OpenAI to extract birthday information from any format."""
        try:
            system_prompt = """You are an expert at extracting birthday information from text messages. 
Extract the person's name/relationship and birthday from the user's message.

The "person_name" can be:
- Actual names: "John", "Sarah", "Mike"
- Relationships: "wife", "husband", "mom", "dad", "brother", "sister", "partner", "boyfriend", "girlfriend"
- Nicknames: "babe", "honey", "bestie", "buddy"
- Possessive forms: "John's" becomes "John", "mom's" becomes "mom", "my wife's" becomes "wife"

Return a JSON object with:
- "person_name": The name/relationship (clean up possessives and remove "my")
- "birthdate": ISO date string (YYYY-MM-DD) 
- "year_known": boolean - true if year was provided, false if only month/day

Examples:
- "John's birthday is March 15th, 1990" → {"person_name": "John", "birthdate": "1990-03-15", "year_known": true}
- "My wife's birthday is on 3 November" → {"person_name": "wife", "birthdate": "2000-11-03", "year_known": false}  
- "Dad's birthday = 12 July 1965" → {"person_name": "dad", "birthdate": "1965-07-12", "year_known": true}
- "Brother birthday is Feb 22" → {"person_name": "brother", "birthdate": "2000-02-22", "year_known": false}
- "My partner's bday is 14th Dec" → {"person_name": "partner", "birthdate": "2000-12-14", "year_known": false}

If no year is given, use 2000 as placeholder. Extract dates in various formats (March 15, 3/15, 15 Mar, etc).
Only return valid JSON. If you cannot extract both name/relationship AND date, return null.
- "Sarah was born on 25 Dec 1985"

If no year is provided, use 1900 as a placeholder and set year_known to false.
Clean up names (remove possessive 's, handle "my wife/husband/etc").
"""
            
            user_prompt = f"Extract birthday information from: '{content}'"
            
            response = await self.classifier.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            if not response:
                self.msg_logger.logger.warning("No response from AI for birthday extraction")
                return None
            
            # Parse the JSON response
            try:
                result = json.loads(response.strip())
                
                # Validate required fields
                if not result.get("person_name") or not result.get("birthdate"):
                    self.msg_logger.logger.warning(f"AI extraction missing required fields: {result}")
                    return None
                
                # Parse the date
                try:
                    birthdate = datetime.fromisoformat(result["birthdate"])
                except (ValueError, TypeError) as e:
                    self.msg_logger.logger.warning(f"Could not parse birthdate '{result['birthdate']}': {e}")
                    return None
                
                return {
                    "person_name": result["person_name"].strip(),
                    "birthdate": birthdate,
                    "year_known": result.get("year_known", True)
                }
                
            except json.JSONDecodeError as e:
                self.msg_logger.logger.warning(f"Could not parse AI response as JSON: {response}")
                return None
                
        except Exception as e:
            self.msg_logger.logger.error(f"Error in AI birthday extraction: {e}")
            return None
