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
            birthday_info = await self._extract_birthday_with_ai(message.content, message, user)
            
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
    
    async def _extract_birthday_with_ai(self, content: str, message: ProcessedMessage, user=None) -> Optional[Dict[str, Any]]:
        """Use OpenAI to extract birthday information from any format."""
        
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
                
                # Log extraction failure for analysis
                message_data = create_log_message_data()
                
                self.msg_logger.log_ai_extraction_failure(
                    extraction_type="birthday",
                    user_message=content,
                    ai_response="Empty response from OpenAI API",
                    message_data=message_data,
                    failure_reason="AI returned empty response",
                    extra_info={"classification_context": "birthday_extraction"}
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
                
                # Validate required fields
                if not result.get("person_name") or not result.get("birthdate"):
                    self.msg_logger.logger.warning(f"AI extraction missing required fields: {result}")
                    
                    # Log extraction failure for analysis
                    message_data = create_log_message_data()
                    
                    missing_fields = []
                    if not result.get("person_name"):
                        missing_fields.append("person_name")
                    if not result.get("birthdate"):
                        missing_fields.append("birthdate")
                    
                    self.msg_logger.log_ai_extraction_failure(
                        extraction_type="birthday",
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
                
                # Parse the date
                try:
                    birthdate = datetime.fromisoformat(result["birthdate"])
                except (ValueError, TypeError) as e:
                    self.msg_logger.logger.warning(f"Could not parse birthdate '{result['birthdate']}': {e}")
                    
                    # Log extraction failure for analysis
                    message_data = create_log_message_data()
                    
                    self.msg_logger.log_ai_extraction_failure(
                        extraction_type="birthday",
                        user_message=content,
                        ai_response=json.dumps(result, indent=2),
                        message_data=message_data,
                        failure_reason=f"Invalid birthdate format: {result['birthdate']} - {str(e)}",
                        extra_info={
                            "birthdate_value": result['birthdate'],
                            "parse_error": str(e),
                            "ai_result": result
                        }
                    )
                    
                    return None
                
                return {
                    "person_name": result["person_name"].strip(),
                    "birthdate": birthdate,
                    "year_known": result.get("year_known", True)
                }
                
            except json.JSONDecodeError as e:
                self.msg_logger.logger.warning(f"Could not parse AI response as JSON: {response_text[:200]}...")
                self.msg_logger.logger.warning(f"Full JSON decode error: {e}")
                
                # Log extraction failure for analysis
                message_data = create_log_message_data()
                
                self.msg_logger.log_ai_extraction_failure(
                    extraction_type="birthday",
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
            self.msg_logger.logger.error(f"Error in AI birthday extraction: {e}")
            
            # Log extraction failure for analysis
            message_data = create_log_message_data()
            
            self.msg_logger.log_ai_extraction_failure(
                extraction_type="birthday",
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
