"""
Message router for directing different types of messages to appropriate handlers.
Now uses simplified workflow with /bd brain dump sessions and no tag prompting.
"""
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from src.models.message_types import ProcessedMessage, ClassificationResult
from src.models.database import User, Message, MessageType, SourceType, SessionStatus
from src.services.supabase_service import SupabaseService
from src.services.whatsapp_service import WhatsAppService
from src.ai.message_classifier import MessageClassifier
from src.workflows.brain_dump import BrainDumpWorkflow
from src.workflows.tagging import TaggingWorkflow
from src.handlers.slash_commands import SlashCommandHandler
from src.handlers.message_handlers import BaseHandler, BirthdayHandler, NoteHandler, ReminderHandler
from src.utils.logger import MessageProcessingLogger
from src.services.media_processing_service import MediaProcessingService
from src.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes messages to appropriate handlers based on content and context."""
    
    def __init__(self, whatsapp_service=None):
        self.db_service = SupabaseService()
        self.msg_logger = MessageProcessingLogger()
        
        # Use provided WhatsApp service or create new one with database connection
        if whatsapp_service:
            self.whatsapp_service = whatsapp_service
        else:
            self.whatsapp_service = WhatsAppService(self.db_service)
            
        self.classifier = MessageClassifier()
        
        # Initialize message handlers directly (pass classifier for OpenAI access)
        self.handlers: List[BaseHandler] = [
            BirthdayHandler(self.db_service, self.whatsapp_service, self.classifier),
            ReminderHandler(self.db_service, self.whatsapp_service, self.classifier),
            NoteHandler(self.db_service, self.whatsapp_service, self.classifier),  # Note handler should be last as fallback
        ]
        
        # Initialize media processing services
        self.media_processor = MediaProcessingService()
        self.file_storage = FileStorageService()
        
        # Initialize legacy workflows for backwards compatibility
        self.brain_dump = BrainDumpWorkflow()
        self.tagging = TaggingWorkflow()
        self.slash_handler = SlashCommandHandler()
        
        # Replace their WhatsApp services with our database-enabled one
        self.brain_dump.whatsapp_service = self.whatsapp_service
        self.tagging.whatsapp_service = self.whatsapp_service
        self.slash_handler.whatsapp_service = self.whatsapp_service

    async def route_message(self, message: ProcessedMessage):
        """Simplified routing logic - no tag prompting, just process messages."""
        
        # Create message data for logging
        message_data = {
            "message_id": message.message_id,
            "user_phone": message.user_phone,
            "content": message.content,
            "message_type": message.message_type,
            "media_id": message.media_id
        }
        
        try:
            self.msg_logger.log_message_stage("MESSAGE_RECEIVED", message_data)
            
            # Get or create user
            self.msg_logger.log_message_stage("USER_LOOKUP", message_data)
            user, is_new_user = await self.db_service.get_or_create_user(message.user_phone)
            
            if user and user.id:
                self.msg_logger.log_success_stage("USER_LOOKUP", message_data, f"User ID: {user.id}")
                
                # Send welcome message for new users and exit early (don't process their first message)
                if is_new_user:
                    await self._send_welcome_message(message.user_phone, user)
                    return  # Exit early - don't process the first message as a note
                    
            else:
                self.msg_logger.log_error_stage("USER_VALIDATION", Exception("User ID is None"), message_data)
                return
            
            # Check for slash commands first
            if message.content and message.content.startswith('/'):
                await self._handle_slash_commands(message, user)
                return
            
            # Check for active brain dump session
            self.msg_logger.log_message_stage("SESSION_CHECK", message_data)
            active_session = await self.db_service.get_active_session(user.id)
            
            # Handle media messages (images, voice notes, documents)
            if message.media_id and message.message_type in ['image', 'audio', 'document']:
                self.msg_logger.log_message_stage("MEDIA_PROCESSING", message_data)
                
                # If in brain dump session, handle media as part of the session
                if active_session:
                    await self._handle_brain_dump_media_message(message, user, active_session)
                else:
                    await self._handle_media_message(message, user, active_session)
                return

            if active_session:
                self.msg_logger.log_message_stage("BRAIN_DUMP_CONTINUATION", message_data,
                                                {"session_id": str(active_session.id)})
                await self._handle_brain_dump_message(message, user, active_session)
                return            # For regular messages, classify and process with handlers
            self.msg_logger.log_message_stage("AI_CLASSIFICATION", message_data)
            user_context = await self._get_user_context(user)
            classification = await self.classifier.classify_message(message.content or "", user_context)
            
            classification_data = {
                "message_type": classification.message_type,
                "confidence": classification.confidence,
                "suggested_tags": classification.suggested_tags,
                "requires_followup": classification.requires_followup
            }
            self.msg_logger.log_classification_result(message_data, classification_data)
            
            # Route to appropriate handler using the new system
            self.msg_logger.log_message_stage("WORKFLOW_ROUTING", message_data,
                                            {"classified_as": classification.message_type})
            
            # Use the new handler system
            result = await self._process_with_handlers(message, user, classification_data)
            
            # If no handler processed it, save as a regular note without prompting for tags
            if not result.get("success"):
                suggested_tags = classification.suggested_tags or []
                await self._save_as_regular_note(message, user, suggested_tags)
            
            self.msg_logger.log_success_stage("MESSAGE_COMPLETE", message_data, "Message processing completed successfully")
            
        except Exception as e:
            self.msg_logger.log_error_stage("MESSAGE_ROUTING", e, message_data)
            logger.error(f"Error routing message: {e}", exc_info=True)
    
    async def _process_with_handlers(self, message: ProcessedMessage, user: User, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Process message using the new handler system."""
        # Find the first handler that can process this message
        for handler in self.handlers:
            if await handler.can_handle(message, user, classification):
                return await handler.handle(message, user, classification)
        
        # If no handler can process the message, return an error
        return {
            "success": False,
            "type": "no_handler_found",
            "error": f"No handler found for message type: {classification.get('message_type', 'unknown')}"
        }
    
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
    
    async def _handle_slash_commands(self, message: ProcessedMessage, user: User):
        """Handle slash commands with simplified brain dump logic."""
        command = message.content.lower().strip()
        
        # Save the command as a message record first
        await self._save_command_message(message, user)
        
        if command.startswith('/bd'):
            await self._start_brain_dump_session(message, user)
        elif command in ['/cancel', '/end']:
            await self._end_active_session(message, user)
        else:
            # Handle other slash commands with the existing handler
            dummy_classification = ClassificationResult(
                message_type="slash_command",
                confidence=1.0,
                suggested_tags=[],
                requires_followup=False,
                extracted_data={}
            )
            await self.slash_handler.handle_command(user, message, dummy_classification)
    
    async def _start_brain_dump_session(self, message: ProcessedMessage, user: User):
        """Start a new brain dump session with /bd command."""
        try:
            if not user.id:
                logger.error("User ID is None - cannot start brain dump session")
                return
                
            # End any existing active session first
            existing_session = await self.db_service.get_active_session(user.id)
            if existing_session and existing_session.id:
                await self.db_service.end_session(existing_session.id, SessionStatus.CANCELLED)
            
            # Extract tags from the /bd command (e.g., "/bd #work #ideas")
            tags = []
            if len(message.content.strip()) > 3:  # More than just "/bd"
                import re
                hashtag_pattern = r'#(\w+)'
                tags = re.findall(hashtag_pattern, message.content)
            
            # Create new brain dump session
            session = await self.db_service.create_session(
                user_id=user.id,
                session_type="brain_dump",
                tags=tags
            )
            
            if session:
                response = "🧠 Brain dump session started!"
                if tags:
                    response += f" Tags: {', '.join(['#' + tag for tag in tags])}"
                response += "\n\nSend your thoughts and I'll collect them silently. Type /end when done, or I'll auto-save after 5 minutes."
                
                await self.whatsapp_service.send_text_message(message.user_phone, response)
                self.msg_logger.log_success_stage("BRAIN_DUMP_STARTED", 
                                                {"message_id": message.message_id, "user_phone": message.user_phone},
                                                f"Session ID: {session.id}")
            else:
                await self.whatsapp_service.send_text_message(
                    message.user_phone, 
                    "Sorry, I couldn't start the brain dump session. Please try again."
                )
                
        except Exception as e:
            self.msg_logger.log_error_stage("BRAIN_DUMP_START_ERROR", e, 
                                          {"message_id": message.message_id, "user_phone": message.user_phone})
            await self.whatsapp_service.send_text_message(
                message.user_phone, 
                "Sorry, there was an error starting your brain dump session."
            )
    
    async def _end_active_session(self, message: ProcessedMessage, user: User):
        """End active brain dump session and process all messages."""
        try:
            if not user.id:
                logger.error("User ID is None - cannot end brain dump session")
                return
                
            active_session = await self.db_service.get_active_session(user.id)
            if active_session and active_session.id:
                await self._process_and_end_brain_dump_session(user, active_session, message.user_phone, "manual")
            else:
                await self.whatsapp_service.send_text_message(
                    message.user_phone, 
                    "No active brain dump session to end."
                )
        except Exception as e:
            self.msg_logger.log_error_stage("BRAIN_DUMP_END_ERROR", e,
                                          {"message_id": message.message_id, "user_phone": message.user_phone})
    
    async def _process_and_end_brain_dump_session(self, user: User, session, user_phone: str, reason: str):
        """End the brain dump session and provide summary."""
        try:
            if not user.id or not session.id:
                logger.error("Missing user ID or session ID")
                return
                
            # Get all messages from this session for counting
            session_messages = await self.db_service.get_user_messages(
                user_id=user.id,
                limit=100,
                since=session.start_time
            )
            brain_dump_messages = [m for m in session_messages if m.session_id == session.id and m.type == MessageType.BRAIN_DUMP]
            
            # End the session
            await self.db_service.end_session(session.id, SessionStatus.COMPLETED)
            
            # Send confirmation with correct count
            message_count = len(brain_dump_messages)
            reason_text = "timed out" if reason == "timeout" else "ended"
            tags_text = " ".join([f"#{tag}" for tag in (session.tags or [])])
            
            if message_count > 0:
                feedback = f"✅ Brain dump session {reason_text}! Saved {message_count} thought{'s' if message_count != 1 else ''} as individual notes."
                if tags_text:
                    feedback += f"\nTags: {tags_text}"
            else:
                feedback = f"✅ Brain dump session {reason_text}, but no messages were saved."
            
            await self.whatsapp_service.send_text_message(user_phone, feedback)
            
            self.msg_logger.log_success_stage("BRAIN_DUMP_SESSION_ENDED",
                                            {"user_phone": user_phone},
                                            f"Session ID: {session.id}, Messages: {message_count}, Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error ending brain dump session: {e}")
            await self.whatsapp_service.send_text_message(
                user_phone, 
                "Sorry, there was an error ending your brain dump session."
            )
    
    async def _handle_brain_dump_message(self, message: ProcessedMessage, user: User, session):
        """Handle messages within an active brain dump session - save each message individually."""
        try:
            if not user.id:
                logger.error("User ID is None - cannot save brain dump message")
                return
                
            # Check if session has timed out (5 minutes)
            session_timeout_minutes = 5
            if session.start_time:
                timeout_delta = timedelta(minutes=session_timeout_minutes)
                if datetime.now(timezone.utc) - session.start_time > timeout_delta:
                    # Session timed out - process all messages and end session
                    await self._process_and_end_brain_dump_session(user, session, message.user_phone, "timeout")
                    return
                
            # Extract any hashtags from the message and add to session tags
            import re
            hashtag_pattern = r'#(\w+)'
            new_tags = re.findall(hashtag_pattern, message.content or "")
            
            # Remove hashtags from the message content for cleaner storage
            clean_content = re.sub(hashtag_pattern, '', message.content or "").strip()
            
            # Combine session tags with any new tags found in this message
            all_tags = list(set((session.tags or []) + new_tags))
            
            # Create individual brain dump message (not consolidated)
            brain_dump_message = Message(
                user_id=user.id,
                message_timestamp=datetime.now(timezone.utc),
                type=MessageType.BRAIN_DUMP,
                content=clean_content,
                tags=all_tags,
                source_type=SourceType.TEXT,
                origin_message_id=message.message_id,
                session_id=session.id,  # Link to session
                # Don't generate vector embedding yet - do it at the end when consolidating
            )
            
            # Save the individual message immediately
            saved_message = await self.db_service.save_message(brain_dump_message)
            
            # Update session tags if we found new ones
            if new_tags:
                await self.db_service.update_session_tags(session.id, all_tags)
            
            # DON'T send any response during the session - just collect messages silently
            
            self.msg_logger.log_success_stage("BRAIN_DUMP_MESSAGE_COLLECTED",
                                            {"message_id": message.message_id, "user_phone": message.user_phone},
                                            f"Session: {session.id}, Tags: {all_tags}, New tags: {new_tags}")
            
        except Exception as e:
            self.msg_logger.log_error_stage("BRAIN_DUMP_MESSAGE_ERROR", e,
                                          {"message_id": message.message_id, "user_phone": message.user_phone})

    async def _handle_brain_dump_media_message(self, message: ProcessedMessage, user: User, session):
        """Handle media messages within an active brain dump session - save each media message individually."""
        try:
            if not user.id:
                logger.error("User ID is None - cannot handle brain dump media message")
                return
            
            # Get WhatsApp access token using the same triple-fallback method
            access_token = None
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            
            if not access_token:
                try:
                    from src.services.whatsapp_token_manager import WhatsAppTokenManager
                    token_manager = WhatsAppTokenManager()
                    token_status = await token_manager.validate_token()
                    if token_status.get("valid"):
                        access_token = token_manager.current_token
                except Exception as token_error:
                    logger.error(f"Token manager error: {token_error}")
            
            if not access_token:
                try:
                    from src.config.settings import settings
                    access_token = settings.whatsapp_access_token
                except Exception as settings_error:
                    logger.error(f"Settings access error: {settings_error}")
            
            if not access_token:
                self.msg_logger.log_error_stage("BRAIN_DUMP_MEDIA_TOKEN_ERROR", 
                                              Exception("No WhatsApp access token available"),
                                              {"message_id": message.message_id})
                return
            
            if not message.media_id:
                logger.error("No media ID found for brain dump media message")
                return
            
            # Download and process media using the correct method name
            filename = f"{message.message_type}_{message.message_id}"
            processed_message = await self.media_processor.process_media_message(
                user_id=user.id,
                media_id=message.media_id,
                filename=filename,
                access_token=access_token,
                caption=message.content  # Any caption/text with the media
            )
            
            if not processed_message:
                logger.error(f"Failed to process media for brain dump session: {message.media_id}")
                return
            
            # Extract meaningful content for the brain dump message
            media_content = ""
            media_type = message.message_type  # Use the message type directly
            
            if media_type == "audio" and processed_message.transcription:
                # Voice note transcription
                media_content = processed_message.transcription
            elif media_type == "image":
                # Image description
                if message.content:  # Caption provided
                    media_content = f"Image: {message.content}"
                else:
                    media_content = "Image shared"
            elif media_type == "document":
                # Document reference
                if message.content:  # Caption provided
                    media_content = f"Document: {message.content}"
                else:
                    media_content = "Document shared"
            else:
                # Fallback
                media_content = message.content or "Media file shared"
            
            # Extract tags from media content and caption
            import re
            hashtag_pattern = r'#(\w+)'
            new_tags = re.findall(hashtag_pattern, media_content)
            
            # Also extract tags from any caption
            if message.content:
                caption_tags = re.findall(hashtag_pattern, message.content)
                new_tags.extend(caption_tags)
            
            # Remove hashtags from content for cleaner storage
            clean_content = re.sub(hashtag_pattern, '', media_content).strip()
            
            # Remove duplicates and combine with session tags
            new_tags = list(set(new_tags))
            all_tags = list(set((session.tags or []) + new_tags))
            
            # Generate vector embedding for the content
            vector_embedding = await self.media_processor.generate_vector_embedding(clean_content)
            
            # Determine source type based on media type
            source_type_map = {
                "audio": SourceType.AUDIO,
                "image": SourceType.IMAGE, 
                "document": SourceType.DOCUMENT
            }
            source_type = source_type_map.get(media_type, SourceType.TEXT)
            
            # Create individual brain dump message
            brain_dump_message = Message(
                user_id=user.id,
                message_timestamp=datetime.now(timezone.utc),
                type=MessageType.BRAIN_DUMP,
                content=clean_content,
                tags=all_tags,
                source_type=source_type,
                origin_message_id=message.message_id,
                session_id=session.id,  # Link to session
                media_url=processed_message.media_url,
                vector_embedding=vector_embedding
            )
            
            # Save the individual media message immediately
            saved_message = await self.db_service.save_message(brain_dump_message)
            
            # Update session tags if we found new ones
            if new_tags:
                await self.db_service.update_session_tags(session.id, all_tags)
            
            # Send quick confirmation (emoji only to minimize interruption)
            await self.whatsapp_service.send_text_message(message.user_phone, "✅")
            
            self.msg_logger.log_success_stage("BRAIN_DUMP_MEDIA_SAVED",
                                            {"message_id": message.message_id, "user_phone": message.user_phone},
                                            f"Session: {session.id}, Media type: {media_type}, Tags: {all_tags}")
            
        except Exception as e:
            self.msg_logger.log_error_stage("BRAIN_DUMP_MEDIA_ERROR", e,
                                          {"message_id": message.message_id, "user_phone": message.user_phone})
    
    
    async def _handle_media_message(self, message: ProcessedMessage, user: User, active_session=None):
        """Handle media messages (images, voice notes, documents)."""
        error_sent = False  # Flag to prevent double error messages
        
        try:
            if not user.id:
                logger.error("User ID is None - cannot handle media message")
                return
            
            if not message.media_id:
                logger.error("Media ID is None - cannot process media message")
                await self.whatsapp_service.send_text_message(
                    message.user_phone, 
                    "Sorry, I couldn't process your media file - no media ID found."
                )
                error_sent = True
                return
            
            # Get WhatsApp access token - try multiple approaches to ensure we get it
            access_token = None
            
            # Method 1: Direct environment access (now with explicit .env loading)
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            
            # Method 2: If direct access fails, try token manager
            if not access_token:
                try:
                    from src.services.whatsapp_token_manager import WhatsAppTokenManager
                    token_manager = WhatsAppTokenManager()
                    token_status = await token_manager.validate_token()
                    if token_status.get("valid"):
                        access_token = token_manager.current_token
                except Exception as token_error:
                    logger.error(f"Token manager error: {token_error}")
            
            # Method 3: If still no token, try settings
            if not access_token:
                try:
                    from src.config.settings import settings
                    access_token = settings.whatsapp_access_token
                except Exception as settings_error:
                    logger.error(f"Settings access error: {settings_error}")
            
            if not access_token:
                logger.error("WhatsApp access token not available through any method")
                await self.whatsapp_service.send_text_message(
                    message.user_phone, 
                    "Sorry, I couldn't process your media file - service temporarily unavailable."
                )
                error_sent = True
                return
            
            # Process the media file with appropriate filename
            if message.message_type == "audio":
                # For voice notes, use a more descriptive filename
                filename = f"voice_note_{message.message_id}"
            elif message.message_type == "image":
                filename = f"image_{message.message_id}"
            elif message.message_type == "document":
                filename = f"document_{message.message_id}"
            else:
                filename = f"{message.message_type}_{message.message_id}"
                
            processed_message = await self.media_processor.process_media_message(
                user_id=user.id,
                media_id=message.media_id,
                filename=filename,
                access_token=access_token,
                caption=message.content
            )
            
            # Extract tags from caption if provided
            if message.content:
                import re
                hashtag_pattern = r'#(\w+)'
                tags = re.findall(hashtag_pattern, message.content)
                processed_message.tags = tags
            
            # If in brain dump session, associate with session
            if active_session:
                processed_message.session_id = active_session.id
                processed_message.type = MessageType.BRAIN_DUMP
                processed_message.origin_message_id = message.message_id
            
            # Save the processed message
            saved_message = await self.db_service.save_message(processed_message)
            
            # Associate the file with the saved message if we have a file_id
            if saved_message and saved_message.id:
                file_id = None
                if processed_message.metadata and isinstance(processed_message.metadata, dict):
                    file_id = processed_message.metadata.get("file_id")
                
                if file_id:
                    try:
                        from uuid import UUID
                        file_uuid = UUID(file_id)
                        await self.media_processor.update_file_message_association(file_uuid, saved_message.id)
                        logger.info(f"Associated file {file_id} with message {saved_message.id}")
                    except Exception as assoc_error:
                        logger.warning(f"Failed to associate file with message: {assoc_error}")
            
            # Send confirmation
            if saved_message:
                response = "✅ Media received"
                if processed_message.transcription:
                    response += f" and transcribed: {processed_message.transcription[:100]}..."
                if processed_message.tags:
                    response += f" | Tags: {', '.join(['#' + tag for tag in processed_message.tags])}"
                
                await self.whatsapp_service.send_text_message(message.user_phone, response)
                
                self.msg_logger.log_success_stage("MEDIA_PROCESSED",
                                                {"message_id": message.message_id, "user_phone": message.user_phone},
                                                f"Media type: {message.message_type}, File saved: {processed_message.media_url}")
            
        except Exception as e:
            self.msg_logger.log_error_stage("MEDIA_PROCESSING_ERROR", e,
                                          {"message_id": message.message_id, "user_phone": message.user_phone})
            
            # Only send error message if we haven't sent one already
            if not error_sent:
                error_msg = "Sorry, I couldn't process your media file."
                
                # Provide more specific error message for token issues
                if "token" in str(e).lower() or "403" in str(e) or "401" in str(e):
                    error_msg = "Sorry, I couldn't process your media file - authentication issue. The admin has been notified."
                elif "timeout" in str(e).lower():
                    error_msg = "Sorry, your media file took too long to process. Please try again with a smaller file."
                
                await self.whatsapp_service.send_text_message(message.user_phone, error_msg)

    async def _save_as_regular_note(self, message: ProcessedMessage, user: User, suggested_tags: List[str]):
        """Save a regular message as a note without prompting for tags."""
        try:
            if not user.id:
                logger.error("User ID is None - cannot save regular note")
                return
                
            # Extract any hashtags from the message
            import re
            hashtag_pattern = r'#(\w+)'
            message_tags = re.findall(hashtag_pattern, message.content or "")
            
            # Combine extracted tags with AI suggested tags
            all_tags = list(set(message_tags + suggested_tags))
            
            # Generate vector embedding for semantic search
            vector_embedding = await self.media_processor.generate_vector_embedding(message.content or "")
            
            # Create message object
            note_message = Message(
                user_id=user.id,
                message_timestamp=datetime.now(timezone.utc),
                type=MessageType.NOTE,
                content=message.content or "",
                tags=all_tags,
                source_type=SourceType.TEXT,
                origin_message_id=message.message_id,
                vector_embedding=vector_embedding
            )
            
            # Save the message as a regular note
            saved_message = await self.db_service.save_message(note_message)
            
            if saved_message:
                # Simple acknowledgment without tag prompting
                response = "✅"
                if all_tags:
                    response += f" Tagged: {', '.join(['#' + tag for tag in all_tags])}"
                
                await self.whatsapp_service.send_text_message(message.user_phone, response)
                
                self.msg_logger.log_success_stage("REGULAR_NOTE_SAVED",
                                                {"message_id": message.message_id, "user_phone": message.user_phone},
                                                f"Note ID: {saved_message.id}, Tags: {all_tags}")
                                                
        except Exception as e:
            self.msg_logger.log_error_stage("REGULAR_NOTE_ERROR", e,
                                          {"message_id": message.message_id, "user_phone": message.user_phone})

    async def _save_command_message(self, message: ProcessedMessage, user: User):
        """Save a user command as a message record for timeline visibility."""
        try:
            if not user.id:
                logger.error("User ID is None - cannot save command message")
                return
                
            # Check if there's an active session to link the command to
            active_session = await self.db_service.get_active_session(user.id)
            session_id = active_session.id if active_session else None
                
            # Create message object for the command
            command_message = Message(
                user_id=user.id,
                message_timestamp=datetime.now(timezone.utc),
                type=MessageType.COMMAND,
                content=message.content or "",
                tags=[],
                source_type=SourceType.TEXT,
                origin_message_id=message.message_id,
                session_id=session_id,  # Link to active session if exists
                vector_embedding=None
            )
            
            # Save the command message
            saved_message = await self.db_service.save_message(command_message)
            
            if saved_message:
                self.msg_logger.log_success_stage("COMMAND_SAVED",
                                                {"message_id": message.message_id, "user_phone": message.user_phone},
                                                f"Command saved: {message.content}")
                                                
        except Exception as e:
            self.msg_logger.log_error_stage("COMMAND_SAVE_ERROR", e,
                                          {"message_id": message.message_id, "user_phone": message.user_phone})

    async def _send_welcome_message(self, user_phone: str, user) -> None:
        """Send a welcome message to new users."""
        try:
            welcome_message = f"""🤖 **Welcome to GetCute!** 

Hi there! I'm your ADHD-friendly personal productivity assistant. I'm here to help you capture thoughts, set reminders, and stay organized without the overwhelm.
"""

            await self.whatsapp_service.send_text_message(user_phone, welcome_message)
            
            # Log the welcome message
            self.msg_logger.log_success_stage("WELCOME_MESSAGE_SENT", 
                                            {"user_phone": user_phone, "user_id": str(user.id)},
                                            "Welcome message sent to new user - first message not processed")
            
        except Exception as e:
            self.msg_logger.log_error_stage("WELCOME_MESSAGE_ERROR", e, 
                                          {"user_phone": user_phone, "user_id": str(user.id)})
        
    