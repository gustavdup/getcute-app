"""
Supabase database service for CRUD operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from config.database import get_db_client, get_admin_client
from models.database import (
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
            # Try to get existing user (use admin client to bypass RLS)
            result = self.admin_client.table("users").select("*").eq("phone_number", phone_number).execute()
            
            if result.data:
                user_data = result.data[0]
                user_data['last_seen'] = datetime.now()
                
                # Update last_seen (use admin client)
                self.admin_client.table("users").update({"last_seen": user_data['last_seen'].isoformat()}).eq("id", user_data['id']).execute()
                
                return User(**user_data)
            else:
                # Create new user (use admin client to bypass RLS)
                new_user = User(
                    id=uuid4(),
                    phone_number=phone_number,
                    platform=platform,
                    created_at=datetime.now(),
                    last_seen=datetime.now()
                )
                
                # Convert to dict with proper serialization
                user_data = new_user.dict()
                user_data['id'] = str(user_data['id'])  # Convert UUID to string
                user_data['created_at'] = user_data['created_at'].isoformat()
                user_data['last_seen'] = user_data['last_seen'].isoformat()
                
                result = self.admin_client.table("users").insert(user_data).execute()
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
            
            # Convert to dict with proper serialization
            message_data = message.dict()
            message_data['id'] = str(message_data['id'])  # Convert UUID to string
            message_data['user_id'] = str(message_data['user_id'])  # Convert UUID to string
            if message_data.get('session_id'):
                message_data['session_id'] = str(message_data['session_id'])
            message_data['message_timestamp'] = message_data['message_timestamp'].isoformat()
            
            # Use admin client to bypass RLS
            result = self.admin_client.table("messages").insert(message_data).execute()
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
                query = query.gte("message_timestamp", since.isoformat())
            
            result = query.order("message_timestamp", desc=True).limit(limit).execute()
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
        """Search messages using vector similarity (requires pgvector setup)."""
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
            logger.info("Vector search not available - using text search fallback")
            logger.debug(f"Vector search error: {e}")
            
            # Fallback to regular text search
            return await self._fallback_text_search(user_id, limit)
    
    async def _fallback_text_search(self, user_id: UUID, limit: int) -> List[Dict[str, Any]]:
        """Fallback text search when vector search is not available."""
        try:
            result = self.client.table("messages").select("*").eq("user_id", str(user_id)).order("message_timestamp", desc=True).limit(limit).execute()
            
            # Convert to vector search format
            return [
                {
                    "content": msg.get("content", ""),
                    "similarity": 1.0,  # Default similarity
                    "timestamp": msg.get("message_timestamp") or msg.get("timestamp"),  # Handle both column names
                    "tags": msg.get("tags", [])
                }
                for msg in (result.data or [])
            ]
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
    
    # Reminder Operations
    async def save_reminder(self, reminder: Reminder) -> Reminder:
        """Save a reminder to the database."""
        try:
            if not reminder.id:
                reminder.id = uuid4()
                reminder.created_at = datetime.now()
            
            # Convert to dict with proper serialization
            reminder_data = reminder.dict()
            reminder_data['id'] = str(reminder_data['id'])
            reminder_data['user_id'] = str(reminder_data['user_id'])
            reminder_data['created_at'] = reminder_data['created_at'].isoformat()
            reminder_data['trigger_time'] = reminder_data['trigger_time'].isoformat()
            if reminder_data.get('completed_at'):
                reminder_data['completed_at'] = reminder_data['completed_at'].isoformat()
            
            result = self.admin_client.table("reminders").insert(reminder_data).execute()
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
            
            # Convert to dict with proper serialization
            birthday_data = birthday.dict()
            birthday_data['id'] = str(birthday_data['id'])
            birthday_data['user_id'] = str(birthday_data['user_id'])
            birthday_data['created_at'] = birthday_data['created_at'].isoformat()
            birthday_data['birthdate'] = birthday_data['birthdate'].isoformat() if hasattr(birthday_data['birthdate'], 'isoformat') else str(birthday_data['birthdate'])
            
            result = self.admin_client.table("birthdays").insert(birthday_data).execute()
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
            # Try custom RPC function for date calculations across years
            result = self.client.rpc(
                'get_upcoming_birthdays',
                {
                    'user_id': str(user_id),
                    'days_ahead': days_ahead
                }
            ).execute()
            
            return [Birthday(**b) for b in result.data]
        except Exception as e:
            logger.info("Advanced birthday search not available - using simple fallback")
            logger.debug(f"Birthday RPC error: {e}")
            
            # Fallback: just get all birthdays
            return await self.get_user_birthdays(user_id)
    
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
            
            # Convert to dict with proper serialization
            session_data = session.dict()
            session_data['id'] = str(session_data['id'])
            session_data['user_id'] = str(session_data['user_id'])
            session_data['start_time'] = session_data['start_time'].isoformat()
            if session_data.get('end_time'):
                session_data['end_time'] = session_data['end_time'].isoformat()
            
            result = self.admin_client.table("sessions").insert(session_data).execute()
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
            result = self.admin_client.table("sessions").update({
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
            # Try custom RPC function to aggregate tags
            result = self.client.rpc(
                'get_user_tag_counts',
                {'user_id': str(user_id)}
            ).execute()
            
            return {item['tag']: item['count'] for item in result.data}
        except Exception as e:
            logger.info("Advanced tag counting not available - using simple fallback")
            logger.debug(f"Tag RPC error: {e}")
            
            # Fallback: extract tags from messages manually
            try:
                messages = await self.get_user_messages(user_id, limit=100)
                tag_counts = {}
                for msg in messages:
                    if msg.tags:
                        for tag in msg.tags:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                return tag_counts
            except Exception as fallback_error:
                logger.error(f"Tag fallback failed: {fallback_error}")
                return {}
    
    async def update_message_vector(self, message_id: UUID, embedding: List[float]) -> bool:
        """Update message with vector embedding."""
        try:
            result = self.admin_client.table("messages").update({
                "vector_embedding": embedding
            }).eq("id", str(message_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating message vector: {e}")
            return False

    async def update_message_tags(self, message_id: UUID, tags: List[str]) -> bool:
        """Update message with new tags."""
        try:
            result = self.admin_client.table("messages").update({
                "tags": tags
            }).eq("id", str(message_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating message tags: {e}")
            return False
