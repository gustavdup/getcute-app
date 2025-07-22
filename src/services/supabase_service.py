"""
Supabase database service for CRUD operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from ..config.database import get_db_client, get_admin_client
from ..models.database import (
    User, Message, Reminder, Birthday, Session,
    MessageType, SourceType, SessionStatus, RepeatType
)

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service class for Supabase database operations."""
    
    def __init__(self):
        self.client = get_db_client()
        self.admin_client = get_admin_client()
    
    # User Operations
    async def get_or_create_user(self, phone_number: str, platform: str = "whatsapp") -> User:
        """Get existing user or create new one."""
        try:
            # Try to get existing user
            result = self.client.table("users").select("*").eq("phone_number", phone_number).execute()
            
            if result.data:
                user_data = result.data[0]
                user_data['last_seen'] = datetime.now()
                
                # Update last_seen
                self.client.table("users").update({"last_seen": user_data['last_seen'].isoformat()}).eq("id", user_data['id']).execute()
                
                return User(**user_data)
            else:
                # Create new user
                new_user = User(
                    id=uuid4(),
                    phone_number=phone_number,
                    platform=platform,
                    created_at=datetime.now(),
                    last_seen=datetime.now()
                )
                
                result = self.client.table("users").insert(new_user.dict()).execute()
                return User(**result.data[0])
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            raise
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        try:
            result = self.client.table("users").select("*").eq("id", str(user_id)).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    # Message Operations
    async def save_message(self, message: Message) -> Message:
        """Save a message to the database."""
        try:
            if not message.id:
                message.id = uuid4()
            
            result = self.client.table("messages").insert(message.dict()).execute()
            return Message(**result.data[0])
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise
    
    async def get_user_messages(
        self, 
        user_id: UUID, 
        limit: int = 50,
        message_type: Optional[MessageType] = None,
        tags: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Get user messages with optional filters."""
        try:
            query = self.client.table("messages").select("*").eq("user_id", str(user_id))
            
            if message_type:
                query = query.eq("type", message_type.value)
            
            if tags:
                # Supabase array contains query
                for tag in tags:
                    query = query.contains("tags", [tag])
            
            if since:
                query = query.gte("timestamp", since.isoformat())
            
            result = query.order("timestamp", desc=True).limit(limit).execute()
            return [Message(**msg) for msg in result.data]
        except Exception as e:
            logger.error(f"Error getting user messages: {e}")
            return []
    
    async def search_messages_vector(
        self, 
        user_id: UUID, 
        query_embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search messages using vector similarity."""
        try:
            # Use RPC call for vector search with pgvector
            result = self.client.rpc(
                'search_messages_by_vector',
                {
                    'user_id': str(user_id),
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit
                }
            ).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    # Reminder Operations
    async def save_reminder(self, reminder: Reminder) -> Reminder:
        """Save a reminder to the database."""
        try:
            if not reminder.id:
                reminder.id = uuid4()
                reminder.created_at = datetime.now()
            
            result = self.client.table("reminders").insert(reminder.dict()).execute()
            return Reminder(**result.data[0])
        except Exception as e:
            logger.error(f"Error saving reminder: {e}")
            raise
    
    async def get_user_reminders(
        self, 
        user_id: UUID,
        active_only: bool = True,
        upcoming_only: bool = False
    ) -> List[Reminder]:
        """Get user reminders."""
        try:
            query = self.client.table("reminders").select("*").eq("user_id", str(user_id))
            
            if active_only:
                query = query.eq("is_active", True)
            
            if upcoming_only:
                query = query.gte("trigger_time", datetime.now().isoformat())
            
            result = query.order("trigger_time", desc=False).execute()
            return [Reminder(**r) for r in result.data]
        except Exception as e:
            logger.error(f"Error getting user reminders: {e}")
            return []
    
    async def get_due_reminders(self, time_window_minutes: int = 5) -> List[Reminder]:
        """Get reminders that are due within the time window."""
        try:
            end_time = datetime.now() + timedelta(minutes=time_window_minutes)
            
            result = self.client.table("reminders").select("*").eq("is_active", True).gte("trigger_time", datetime.now().isoformat()).lte("trigger_time", end_time.isoformat()).execute()
            
            return [Reminder(**r) for r in result.data]
        except Exception as e:
            logger.error(f"Error getting due reminders: {e}")
            return []
    
    # Birthday Operations
    async def save_birthday(self, birthday: Birthday) -> Birthday:
        """Save a birthday to the database."""
        try:
            if not birthday.id:
                birthday.id = uuid4()
                birthday.created_at = datetime.now()
            
            result = self.client.table("birthdays").insert(birthday.dict()).execute()
            return Birthday(**result.data[0])
        except Exception as e:
            logger.error(f"Error saving birthday: {e}")
            raise
    
    async def get_user_birthdays(self, user_id: UUID) -> List[Birthday]:
        """Get user birthdays."""
        try:
            result = self.client.table("birthdays").select("*").eq("user_id", str(user_id)).order("birthdate", desc=False).execute()
            return [Birthday(**b) for b in result.data]
        except Exception as e:
            logger.error(f"Error getting user birthdays: {e}")
            return []
    
    async def get_upcoming_birthdays(self, user_id: UUID, days_ahead: int = 30) -> List[Birthday]:
        """Get upcoming birthdays within specified days."""
        try:
            # This would need custom SQL for date calculations across years
            result = self.client.rpc(
                'get_upcoming_birthdays',
                {
                    'user_id': str(user_id),
                    'days_ahead': days_ahead
                }
            ).execute()
            
            return [Birthday(**b) for b in result.data]
        except Exception as e:
            logger.error(f"Error getting upcoming birthdays: {e}")
            return []
    
    # Session Operations
    async def create_session(self, user_id: UUID, session_type: str = "brain_dump", tags: Optional[List[str]] = None) -> Session:
        """Create a new session."""
        try:
            session = Session(
                id=uuid4(),
                user_id=user_id,
                type=session_type,
                start_time=datetime.now(),
                status=SessionStatus.ACTIVE,
                tags=tags or []
            )
            
            result = self.client.table("sessions").insert(session.dict()).execute()
            return Session(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_active_session(self, user_id: UUID) -> Optional[Session]:
        """Get active session for user."""
        try:
            result = self.client.table("sessions").select("*").eq("user_id", str(user_id)).eq("status", SessionStatus.ACTIVE.value).order("start_time", desc=True).limit(1).execute()
            
            if result.data:
                return Session(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            return None
    
    async def end_session(self, session_id: UUID, status: SessionStatus = SessionStatus.COMPLETED) -> bool:
        """End a session."""
        try:
            result = self.client.table("sessions").update({
                "status": status.value,
                "end_time": datetime.now().isoformat()
            }).eq("id", str(session_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    # Tag Operations
    async def get_user_tags(self, user_id: UUID) -> Dict[str, int]:
        """Get user tags with usage counts."""
        try:
            # This would need a custom RPC function to aggregate tags
            result = self.client.rpc(
                'get_user_tag_counts',
                {'user_id': str(user_id)}
            ).execute()
            
            return {item['tag']: item['count'] for item in result.data}
        except Exception as e:
            logger.error(f"Error getting user tags: {e}")
            return {}
    
    async def update_message_vector(self, message_id: UUID, embedding: List[float]) -> bool:
        """Update message with vector embedding."""
        try:
            result = self.client.table("messages").update({
                "vector_embedding": embedding
            }).eq("id", str(message_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating message vector: {e}")
            return False
