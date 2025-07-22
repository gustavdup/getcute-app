"""
Message router for directing different types of messages to appropriate handlers.
"""
import logging
from typing import Dict, Any, Optional
from ..models.message_types import ProcessedMessage, ClassificationResult
from ..models.database import User, Message, MessageType, SourceType
from ..services.supabase_service import SupabaseService
from ..services.whatsapp_service import WhatsAppService
from ..ai.message_classifier import MessageClassifier
from ..workflows.brain_dump import BrainDumpWorkflow
from ..workflows.tagging import TaggingWorkflow
from .slash_commands import SlashCommandHandler

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes messages to appropriate handlers based on content and context."""
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.whatsapp_service = WhatsAppService()
        self.classifier = MessageClassifier()
        self.brain_dump = BrainDumpWorkflow()
        self.tagging = TaggingWorkflow()
        self.slash_handler = SlashCommandHandler()
    
    async def route_message(self, message: ProcessedMessage):
        """Main routing logic for incoming messages."""
        try:
            # Get or create user
            user = await self.db_service.get_or_create_user(message.user_phone)
            logger.info(f"Processing message from user {user.id}: {message.content[:50]}...")
            
            # Ensure user has an ID
            if not user.id:
                logger.error("User ID is None after creation")
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "Sorry, there was an issue with your account. Please try again."
                )
                return
            
            # Check for active brain dump session
            active_session = await self.db_service.get_active_session(user.id)
            if active_session and not message.content.startswith('/'):
                await self.brain_dump.handle_session_message(user, message, active_session)
                return
            
            # Classify the message
            classification = await self.classifier.classify_message(
                message.content,
                await self._get_user_context(user)
            )
            
            logger.info(f"Message classified as: {classification.message_type} (confidence: {classification.confidence})")
            
            # Route based on classification
            await self._route_by_classification(user, message, classification)
            
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            # Send error message to user
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "Sorry, I encountered an error processing your message. Please try again."
            )
    
    async def _route_by_classification(
        self, 
        user: User, 
        message: ProcessedMessage, 
        classification: ClassificationResult
    ):
        """Route message based on AI classification."""
        try:
            if classification.message_type == "slash_command":
                await self.slash_handler.handle_command(user, message, classification)
            
            elif classification.message_type == "brain_dump_start":
                await self.brain_dump.start_session(user, message, classification)
            
            elif classification.message_type == "note":
                await self._handle_note(user, message, classification)
            
            elif classification.message_type == "reminder":
                await self._handle_reminder(user, message, classification)
            
            elif classification.message_type == "birthday":
                await self._handle_birthday(user, message, classification)
            
            else:
                # Default to note
                await self._handle_note(user, message, classification)
                
        except Exception as e:
            logger.error(f"Error in classification routing: {e}")
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "I couldn't process that message. Try rephrasing or use /help for guidance."
            )
    
    async def _handle_note(self, user: User, message: ProcessedMessage, classification: ClassificationResult):
        """Handle note storage and tagging."""
        try:
            # Ensure user has an ID
            if not user.id:
                logger.error("User ID is None in _handle_note")
                return
            
            # Create message record
            note = Message(
                user_id=user.id,
                timestamp=message.timestamp,
                type=MessageType.NOTE,
                content=message.content,
                tags=classification.suggested_tags or [],
                source_type=SourceType(message.message_type),
                origin_message_id=message.message_id,
                media_url=message.media_url
            )
            
            # Save to database
            saved_note = await self.db_service.save_message(note)
            
            # Handle media processing if needed
            if message.media_id:
                await self._process_media(saved_note, message.media_id)
            
            # Handle tagging workflow
            if classification.requires_followup or not classification.suggested_tags:
                await self.tagging.prompt_for_tags(user, saved_note, classification.suggested_tags)
            else:
                # Confirm note saved with tags
                tags_text = " ".join([f"#{tag}" for tag in classification.suggested_tags])
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    f"✅ Note saved! {tags_text}"
                )
            
        except Exception as e:
            logger.error(f"Error handling note: {e}")
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "Failed to save note. Please try again."
            )
    
    async def _handle_reminder(self, user: User, message: ProcessedMessage, classification: ClassificationResult):
        """Handle reminder creation."""
        try:
            # This would involve the reminder parser
            # For now, send a confirmation
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "📝 I'll help you set up that reminder! Reminder functionality is being implemented."
            )
            
            # Save as note for now
            await self._handle_note(user, message, classification)
            
        except Exception as e:
            logger.error(f"Error handling reminder: {e}")
    
    async def _handle_birthday(self, user: User, message: ProcessedMessage, classification: ClassificationResult):
        """Handle birthday storage."""
        try:
            # This would involve the birthday parser
            # For now, send a confirmation
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "🎂 I'll help you save that birthday! Birthday functionality is being implemented."
            )
            
            # Save as note for now
            await self._handle_note(user, message, classification)
            
        except Exception as e:
            logger.error(f"Error handling birthday: {e}")
    
    async def _process_media(self, message: Message, media_id: str):
        """Process media files (transcription, image analysis, etc.)."""
        try:
            # Download media
            media_content = await self.whatsapp_service.download_media(media_id)
            if not media_content:
                return
            
            # This would involve:
            # 1. Upload to Supabase Storage
            # 2. Transcribe audio if applicable
            # 3. Generate image captions if applicable
            # 4. Update message with processed data
            
            logger.info(f"Media processing for message {message.id} - size: {len(media_content)} bytes")
            
        except Exception as e:
            logger.error(f"Error processing media: {e}")
    
    async def _get_user_context(self, user: User) -> Dict[str, Any]:
        """Get user context for AI classification."""
        try:
            # Ensure user has an ID
            if not user.id:
                logger.warning("User ID is None in _get_user_context")
                return {
                    "recent_tags": [],
                    "timezone": "UTC",
                    "user_id": "unknown"
                }
            
            # Get recent tags
            user_tags = await self.db_service.get_user_tags(user.id)
            recent_tags = list(user_tags.keys())[:10]  # Top 10 recent tags
            
            return {
                "recent_tags": recent_tags,
                "timezone": "UTC",  # Would get from user preferences
                "user_id": str(user.id)
            }
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {
                "recent_tags": [],
                "timezone": "UTC",
                "user_id": "unknown"
            }
