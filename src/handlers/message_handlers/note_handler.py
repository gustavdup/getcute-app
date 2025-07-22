"""
Note handler for processing general note messages.
"""
from typing import Any, Dict
from datetime import datetime
from src.models.database import Message as DBMessage, MessageType, SourceType
from src.models.message_types import ProcessedMessage
from src.utils.logger import MessageProcessingLogger
from .base_handler import BaseHandler


class NoteHandler(BaseHandler):
    """Handler for general note messages."""
    
    def __init__(self, db_service, whatsapp_service, classifier):
        """Initialize with services and classifier for AI completions."""
        self.db_service = db_service
        self.whatsapp_service = whatsapp_service
        self.classifier = classifier  # Use classifier for AI completions
        self.msg_logger = MessageProcessingLogger()
    
    async def can_handle(self, message: ProcessedMessage, user, classification: Dict[str, Any]) -> bool:
        """Check if this message should be saved as a note."""
        return classification.get("message_type") == "note"
    
    async def handle(self, message: ProcessedMessage, user, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Process note messages."""
        message_data = self._create_message_data(message)
        
        try:
            self.msg_logger.log_message_stage("NOTE_CREATION", message_data)
            
            # Create message record for storage
            self.msg_logger.log_message_stage("MESSAGE_RECORD_CREATION", message_data)
            
            # Ensure user has valid ID
            if not user.id:
                raise Exception("User ID is None when creating note")
            
            # Determine source type based on message type
            source_type_map = {
                "text": SourceType.TEXT,
                "image": SourceType.IMAGE,
                "audio": SourceType.AUDIO,
                "document": SourceType.DOCUMENT
            }
            source_type = source_type_map.get(message.message_type, SourceType.TEXT)
            
            # Create database message
            db_message = DBMessage(
                user_id=user.id,
                message_timestamp=message.timestamp,
                type=MessageType.NOTE,
                content=message.content,
                tags=classification.get("suggested_tags", []),
                source_type=source_type,
                origin_message_id=message.message_id,
                media_url=message.media_url,
                metadata={
                    "confidence": classification.get("confidence", 0.0),
                    "classification": classification.get("message_type"),
                    "ai_suggested_tags": classification.get("suggested_tags", [])
                }
            )
            
            # Save to database
            self.msg_logger.log_message_stage("DATABASE_SAVE", message_data)
            saved_message = await self.db_service.save_message(db_message)
            self.msg_logger.log_database_operation("INSERT", "messages", str(saved_message.id), success=True)
            
            # Handle media if present
            if message.media_id:
                await self._process_media(message, saved_message.id, user.id)
            
            # Handle tagging workflow
            await self._handle_tagging_workflow(message, saved_message, classification)
            
            self.msg_logger.log_success_stage("NOTE_COMPLETE", message_data, 
                                           f"Note saved with ID: {saved_message.id}")
            
            return {
                "success": True,
                "type": "note",
                "message_id": str(saved_message.id),
                "tags": saved_message.tags or []
            }
            
        except Exception as e:
            self.msg_logger.log_error_stage("NOTE_ERROR", e, message_data)
            
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "I had trouble saving that note. Could you try again?"
            )
            
            return {
                "success": False,
                "type": "note_error",
                "error": str(e)
            }
    
    async def _process_media(self, message: ProcessedMessage, message_db_id, user_id):
        """Process media attachments."""
        try:
            self.msg_logger.log_message_stage("MEDIA_PROCESSING_START", 
                                            self._create_message_data(message),
                                            {"media_id": message.media_id})
            
            # Download and process media
            media_result = await self.whatsapp_service.process_media(
                message.media_id, user_id, message_db_id
            )
            
            if not media_result.get("success"):
                self.msg_logger.logger.warning(f"Media processing failed for {message.media_id}")
            
        except Exception as e:
            self.msg_logger.logger.error(f"Error processing media {message.media_id}: {e}")
    
    async def _handle_tagging_workflow(self, message: ProcessedMessage, saved_message, classification: Dict[str, Any]):
        """Handle the tagging workflow for the message."""
        try:
            requires_followup = classification.get("requires_followup", False)
            suggested_tags = classification.get("suggested_tags", [])
            
            self.msg_logger.log_message_stage("TAGGING_WORKFLOW", 
                                            self._create_message_data(message),
                                            {
                                                "requires_followup": requires_followup,
                                                "suggested_tags": suggested_tags
                                            })
            
            # For now, we'll auto-apply suggested tags if confidence is high
            # In the future, this could prompt the user for tag confirmation
            if suggested_tags and classification.get("confidence", 0) > 0.8:
                # Update message with suggested tags
                saved_message.tags = suggested_tags
                await self.db_service.update_message(saved_message)
                
                # Send confirmation with tags
                tag_text = ", ".join(suggested_tags)
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    f"✅ Note saved with tags: {tag_text}"
                )
            else:
                # Send simple confirmation
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "✅ Note saved!"
                )
            
        except Exception as e:
            self.msg_logger.logger.error(f"Error in tagging workflow: {e}")
            # Still send a basic confirmation even if tagging fails
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "✅ Note saved!"
            )
