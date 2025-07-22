"""
Brain dump workflow for managing focused note-taking sessions.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from models.message_types import ProcessedMessage, ClassificationResult
from models.database import User, Session, Message, MessageType, SourceType, SessionStatus
from services.supabase_service import SupabaseService
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class BrainDumpWorkflow:
    """Manages brain dump sessions where users can rapidly save notes with predefined tags."""
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.whatsapp_service = WhatsAppService()
        self.session_timeout_minutes = 3  # Default timeout
    
    async def start_session(self, user: User, message: ProcessedMessage, classification: ClassificationResult):
        """Start a new brain dump session."""
        try:
            if not user.id:
                logger.error("User ID is None, cannot start session")
                return
                
            # End any existing active session
            existing_session = await self.db_service.get_active_session(user.id)
            if existing_session and existing_session.id:
                await self.db_service.end_session(existing_session.id, SessionStatus.CANCELLED)
            
            # Extract tags from the message
            tags = classification.extracted_data.get("tags", [])
            
            if not tags:
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "To start a brain dump session, send your tags like: #work #ideas #project"
                )
                return
            
            # Create new session
            session = await self.db_service.create_session(
                user_id=user.id,
                session_type="brain_dump",
                tags=tags
            )
            
            # Send confirmation
            tags_text = " ".join([f"#{tag}" for tag in tags])
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                f"🧠 Brain dump session started!\n\n"
                f"Tags: {tags_text}\n\n"
                f"Send your thoughts and I'll save them with these tags. "
                f"Session ends automatically in {self.session_timeout_minutes} minutes or when you send /end"
            )
            
            logger.info(f"Started brain dump session {session.id} for user {user.id} with tags: {tags}")
            
        except Exception as e:
            logger.error(f"Error starting brain dump session: {e}")
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "Sorry, I couldn't start the brain dump session. Please try again."
            )
    
    async def handle_session_message(self, user: User, message: ProcessedMessage, session: Session):
        """Handle messages during an active brain dump session."""
        try:
            if not user.id or not session.id:
                logger.error("Missing user ID or session ID")
                return
                
            # Check if session has timed out
            if self._is_session_expired(session):
                await self.db_service.end_session(session.id, SessionStatus.TIMEOUT)
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "⏰ Brain dump session timed out. Your notes have been saved."
                )
                return
            
            # Save the message with session tags
            note = Message(
                user_id=user.id,
                message_timestamp=message.timestamp,
                type=MessageType.BRAIN_DUMP,
                content=message.content,
                tags=session.tags or [],
                session_id=session.id,
                source_type=SourceType(message.message_type),
                origin_message_id=message.message_id,
                media_url=message.media_url
            )
            
            await self.db_service.save_message(note)
            
            # Send quick confirmation (emoji only to minimize interruption)
            await self.whatsapp_service.send_text_message(message.user_phone, "✅")
            
            # Periodically check if user wants to continue (every 5th message or after 2 minutes)
            await self._maybe_send_continuation_prompt(user, session, message)
            
            logger.info(f"Saved brain dump message to session {session.id}")
            
        except Exception as e:
            logger.error(f"Error handling session message: {e}")
            # Don't send error to user during brain dump to avoid interruption
    
    async def _maybe_send_continuation_prompt(self, user: User, session: Session, message: ProcessedMessage):
        """Send continuation prompt if it's been a while or after several messages."""
        try:
            if not session.id:
                return
                
            # Get message count in this session
            session_messages = await self.db_service.get_user_messages(
                user_id=user.id,  # type: ignore
                limit=100,
                since=session.start_time
            )
            
            session_message_count = len([m for m in session_messages if m.session_id == session.id])
            
            # Send prompt every 5 messages or if it's been 2+ minutes since last prompt
            should_prompt = (
                session_message_count > 0 and 
                session_message_count % 5 == 0
            ) or self._should_send_time_prompt(session)
            
            if should_prompt:
                tags_text = " ".join([f"#{tag}" for tag in (session.tags or [])])
                await self.whatsapp_service.send_brain_dump_prompt(
                    message.user_phone,
                    session.tags or []
                )
                
        except Exception as e:
            logger.error(f"Error in continuation prompt: {e}")
    
    def _is_session_expired(self, session: Session) -> bool:
        """Check if a session has expired."""
        if not session.start_time:
            return True
            
        timeout_delta = timedelta(minutes=self.session_timeout_minutes)
        return datetime.now() - session.start_time > timeout_delta
    
    def _should_send_time_prompt(self, session: Session) -> bool:
        """Check if enough time has passed to send a continuation prompt."""
        if not session.start_time:
            return False
            
        # Send prompt after 2 minutes if no recent activity
        prompt_delta = timedelta(minutes=2)
        return datetime.now() - session.start_time > prompt_delta
    
    async def end_session(self, user: User, session_id: str, reason: SessionStatus = SessionStatus.COMPLETED):
        """End a brain dump session."""
        try:
            if not user.id:
                return
                
            # Get session info for confirmation message
            session = await self.db_service.get_active_session(user.id)
            
            if not session or not session.id:
                return
            
            # End the session
            await self.db_service.end_session(session.id, reason)
            
            # Get count of messages in this session
            session_messages = await self.db_service.get_user_messages(
                user_id=user.id,
                limit=100,
                since=session.start_time
            )
            
            message_count = len([m for m in session_messages if m.session_id == session.id])
            
            # Send confirmation
            tags_text = " ".join([f"#{tag}" for tag in (session.tags or [])])
            status_text = {
                SessionStatus.COMPLETED: "completed",
                SessionStatus.TIMEOUT: "timed out",
                SessionStatus.CANCELLED: "cancelled"
            }.get(reason, "ended")
            
            confirmation = (
                f"🧠 Brain dump session {status_text}!\n\n"
                f"Saved {message_count} notes with tags: {tags_text}\n\n"
                f"Use /notes to view them or /portal to access your dashboard."
            )
            
            # Note: We can't send this directly since we don't have user phone in this context
            # This would be called from the slash command handler
            
            logger.info(f"Ended brain dump session {session.id} with reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error ending brain dump session: {e}")
    
    async def get_session_summary(self, user: User, session_id: str) -> dict:
        """Get a summary of a brain dump session."""
        try:
            if not user.id:
                return {}
                
            # This would retrieve session statistics
            # For now, return placeholder
            return {
                "message_count": 0,
                "tags": [],
                "duration_minutes": 0,
                "status": "unknown"
            }
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return {}
