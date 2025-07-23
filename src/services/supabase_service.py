"""
Supabase database service for CRUD operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from src.config.database import get_db_client, get_admin_client
from src.models.database import (
    User, Message, Reminder, Birthday, Session, File,
    MessageType, SourceType, SessionStatus, RepeatType, FileType, UploadStatus, TranscriptionStatus
)
from src.utils.logger import get_message_logger, safe_log_content

logger = logging.getLogger(__name__)
msg_logger = get_message_logger()


class SupabaseService:
    """Service class for Supabase database operations."""
    
    def __init__(self):
        self.client = get_db_client()
        self.admin_client = get_admin_client()
    
    # User Operations
    async def get_or_create_user(self, phone_number: str, platform: str = "whatsapp") -> tuple[User, bool]:
        """Get existing user or create new one. Returns (user, is_new_user)."""
        try:
            # Try to get existing user (use admin client to bypass RLS)
            result = self.admin_client.table("users").select("*").eq("phone_number", phone_number).execute()
            
            if result.data:
                user_data = result.data[0]
                user_data['last_seen'] = datetime.now(timezone.utc)
                
                # Update last_seen (use admin client)
                self.admin_client.table("users").update({"last_seen": user_data['last_seen'].isoformat()}).eq("id", user_data['id']).execute()
                
                return User(**user_data), False  # Existing user
            else:
                # Create new user (use admin client to bypass RLS)
                new_user = User(
                    id=uuid4(),
                    phone_number=phone_number,
                    platform=platform,
                    created_at=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc)
                )
                
                # Convert to dict with proper serialization
                user_data = new_user.dict()
                user_data['id'] = str(user_data['id'])  # Convert UUID to string
                user_data['created_at'] = user_data['created_at'].isoformat()
                user_data['last_seen'] = user_data['last_seen'].isoformat()
                
                result = self.admin_client.table("users").insert(user_data).execute()
                return User(**result.data[0]), True  # New user
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            raise
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        try:
            result = self.admin_client.table("users").select("*").eq("id", str(user_id)).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def _serialize_nested_objects(self, obj: Any) -> Any:
        """Recursively convert UUID objects and other non-serializable objects to strings."""
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_nested_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_nested_objects(item) for item in obj]
        else:
            return obj
    
    # Message Operations
    async def save_message(self, message: Message) -> Message:
        """Save a message to the database."""
        try:
            logger.info(f"Saving message: {safe_log_content(message.content)}...")
            msg_logger.log_database_operation("INSERT", "messages", None, success=True)
            
            if not message.id:
                message.id = uuid4()
            
            # Convert to dict with proper serialization
            message_data = message.dict()
            message_data['id'] = str(message_data['id'])  # Convert UUID to string
            message_data['user_id'] = str(message_data['user_id'])  # Convert UUID to string
            if message_data.get('session_id'):
                message_data['session_id'] = str(message_data['session_id'])
            message_data['message_timestamp'] = message_data['message_timestamp'].isoformat()
            
            # Recursively convert any UUID objects in metadata to strings
            if message_data.get('metadata'):
                message_data['metadata'] = self._serialize_nested_objects(message_data['metadata'])
            
            # Use admin client to bypass RLS
            result = self.admin_client.table("messages").insert(message_data).execute()
            
            saved_message = Message(**result.data[0])
            logger.info(f"Successfully saved message with ID: {saved_message.id}")
            msg_logger.log_database_operation("INSERT", "messages", str(saved_message.id), success=True)
            
            return saved_message
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            msg_logger.log_database_operation("INSERT", "messages", None, success=False, error=str(e))
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
            query = self.admin_client.table("messages").select("*").eq("user_id", str(user_id))
            
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
            result = self.admin_client.rpc(
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
        """Save a reminder to the database (create or update)."""
        try:
            # Set created_at only if it's a new reminder (no existing ID or created_at)
            if not reminder.id:
                reminder.id = uuid4()
            if not reminder.created_at:
                reminder.created_at = datetime.now(timezone.utc)
            
            # Convert to dict with proper serialization
            reminder_data = reminder.dict()
            reminder_data['id'] = str(reminder_data['id'])
            reminder_data['user_id'] = str(reminder_data['user_id'])
            reminder_data['created_at'] = reminder_data['created_at'].isoformat()
            reminder_data['trigger_time'] = reminder_data['trigger_time'].isoformat()
            if reminder_data.get('completed_at'):
                reminder_data['completed_at'] = reminder_data['completed_at'].isoformat()
            if reminder_data.get('repeat_until'):
                reminder_data['repeat_until'] = reminder_data['repeat_until'].isoformat()
            
            # Use upsert to handle both create and update operations
            result = self.admin_client.table("reminders").upsert(reminder_data).execute()
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
            query = self.admin_client.table("reminders").select("*").eq("user_id", str(user_id))
            
            if active_only:
                query = query.eq("is_active", True)
            
            if upcoming_only:
                query = query.gte("trigger_time", datetime.now(timezone.utc).isoformat())
            
            result = query.order("trigger_time", desc=False).execute()
            return [Reminder(**r) for r in result.data]
        except Exception as e:
            logger.error(f"Error getting user reminders: {e}")
            return []
    
    async def get_due_reminders(self, time_window_minutes: int = 5) -> List[Reminder]:
        """Get reminders that are due within the time window."""
        try:
            # CRITICAL: Use UTC time to match database storage timezone
            now = datetime.now(timezone.utc)
            # Look back 1 hour to catch any missed reminders due to system downtime/restarts
            start_time = now - timedelta(hours=1)  
            end_time = now + timedelta(minutes=time_window_minutes)
            
            # Get reminders that:
            # 1. Are active
            # 2. Have trigger_time between start_time and end_time
            # 3. Don't have completed_at set (haven't been sent yet)
            result = self.admin_client.table("reminders").select("*").eq(
                "is_active", True
            ).gte(
                "trigger_time", start_time.isoformat()
            ).lte(
                "trigger_time", end_time.isoformat()
            ).is_(
                "completed_at", "null"
            ).execute()
            
            return [Reminder(**r) for r in result.data]
        except Exception as e:
            logger.error(f"Error getting due reminders: {e}")
            return []
    
    async def get_missed_recurring_reminders(self, hours_back: int = 768) -> List[Reminder]:  # 768 hours = 32 days
        """
        Find recurring reminders that should have triggered but didn't get their next occurrence created.
        This is a failsafe for system downtime scenarios.
        
        Logic: For each completed recurring reminder, check if the NEXT occurrence in the chain exists.
        If not, create ONE reminder for the next expected occurrence (not multiple missed ones).
        """
        try:
            # CRITICAL: Use UTC time to match database storage timezone
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(hours=hours_back)
            
            # Find completed recurring reminders that:
            # 1. Were completed (sent) in the past X hours (32 days for monthly reminders)
            # 2. Are recurring (not NONE)
            # 3. Should have had a next occurrence created
            # 4. But no active reminder exists for the expected next trigger time
            
            result = self.admin_client.table("reminders").select("*").eq(
                "is_active", False  # Completed reminders
            ).neq(
                "repeat_type", "none"  # Recurring reminders only
            ).gte(
                "completed_at", cutoff_time.isoformat()  # Completed in the lookback window
            ).not_.is_(
                "completed_at", "null"  # Must have completed_at set
            ).execute()
            
            completed_recurring = [Reminder(**r) for r in result.data]
            recovery_reminders = []
            
            # For each completed recurring reminder, check if the recurring chain continues
            for reminder in completed_recurring:
                if not reminder.completed_at or not reminder.trigger_time:
                    continue
                
                # Find the NEXT occurrence that should exist
                next_expected_reminder = self._find_next_expected_occurrence(reminder, now)
                
                if next_expected_reminder:
                    recovery_reminders.append(next_expected_reminder)
            
            if recovery_reminders:
                logger.info(f"Found {len(recovery_reminders)} broken recurring chains - creating recovery reminders")
            
            return recovery_reminders
            
        except Exception as e:
            logger.error(f"Error finding missed recurring reminders: {e}")
            return []
    
    def _find_next_expected_occurrence(self, completed_reminder: Reminder, current_time: datetime) -> Optional[Reminder]:
        """
        Find the next occurrence that should exist in the recurring chain.
        Only creates ONE reminder to continue the chain, not multiple missed ones.
        """
        try:
            # Calculate the next occurrence that should have been created
            next_trigger = self._calculate_next_trigger_time(
                completed_reminder.trigger_time, 
                completed_reminder.repeat_type
            )
            
            if not next_trigger:
                return None
            
            # Skip if next occurrence would be after repeat_until
            if completed_reminder.repeat_until and next_trigger > completed_reminder.repeat_until:
                return None
            
            # Check if any active reminder exists for this recurring series
            existing_result = self.admin_client.table("reminders").select("id").eq(
                "user_id", str(completed_reminder.user_id)
            ).eq(
                "title", completed_reminder.title
            ).eq(
                "is_active", True
            ).eq(
                "repeat_type", completed_reminder.repeat_type
            ).execute()
            
            # If an active reminder exists for this series, the chain is intact
            if existing_result.data:
                return None
            
            # No active reminder exists - the chain is broken
            # Create the NEXT occurrence to continue the chain
            
            # If the expected time has passed, calculate the next appropriate time
            if next_trigger <= current_time:
                next_trigger = self._calculate_next_appropriate_time(
                    completed_reminder.trigger_time,
                    completed_reminder.repeat_type,
                    current_time
                )
            
            if not next_trigger:
                return None
            
            # Create recovery reminder for the next occurrence
            recovery_reminder = Reminder(
                id=uuid4(),
                user_id=completed_reminder.user_id,
                title=completed_reminder.title,  # Keep original title (no [Missed] prefix)
                description=completed_reminder.description,
                trigger_time=next_trigger,
                repeat_type=completed_reminder.repeat_type,
                repeat_interval=completed_reminder.repeat_interval,
                repeat_until=completed_reminder.repeat_until,
                tags=completed_reminder.tags or [],
                is_active=True,
                created_at=current_time
            )
            
            logger.info(f"Creating recovery reminder for broken chain: {completed_reminder.title} -> {next_trigger}")
            return recovery_reminder
            
        except Exception as e:
            logger.error(f"Error finding next expected occurrence: {e}")
            return None
    
    def _calculate_next_appropriate_time(
        self, 
        original_trigger: datetime, 
        repeat_type: str, 
        current_time: datetime
    ) -> Optional[datetime]:
        """
        Calculate the next appropriate time to continue the recurring chain.
        This accounts for multiple missed occurrences and finds the next future time.
        """
        try:
            if repeat_type == "daily":
                # For daily reminders, find the next occurrence at the same time
                next_time = original_trigger.replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day
                )
                
                # If today's time has passed, schedule for tomorrow
                if next_time <= current_time:
                    next_time = next_time + timedelta(days=1)
                    
                return next_time
                
            elif repeat_type == "weekly":
                # For weekly reminders, find the next occurrence on the same day of week
                days_ahead = (original_trigger.weekday() - current_time.weekday()) % 7
                if days_ahead == 0:  # Same day of week
                    # Check if time has passed today
                    today_at_time = current_time.replace(
                        hour=original_trigger.hour,
                        minute=original_trigger.minute,
                        second=original_trigger.second,
                        microsecond=0
                    )
                    if today_at_time <= current_time:
                        days_ahead = 7  # Next week
                    else:
                        days_ahead = 0  # Later today
                
                next_time = current_time + timedelta(days=days_ahead)
                next_time = next_time.replace(
                    hour=original_trigger.hour,
                    minute=original_trigger.minute,
                    second=original_trigger.second,
                    microsecond=0
                )
                return next_time
                
            elif repeat_type == "monthly":
                # For monthly reminders, schedule for next month on same day
                next_month = current_time.month + 1
                next_year = current_time.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                
                try:
                    next_time = current_time.replace(
                        year=next_year,
                        month=next_month,
                        day=min(original_trigger.day, 28),  # Safe day to avoid month overflow
                        hour=original_trigger.hour,
                        minute=original_trigger.minute,
                        second=original_trigger.second
                    )
                    return next_time
                except ValueError:
                    # Fallback: add 30 days
                    return current_time + timedelta(days=30)
                    
            elif repeat_type == "yearly":
                # For yearly reminders, schedule for next year
                try:
                    next_time = original_trigger.replace(year=current_time.year + 1)
                    if next_time <= current_time:
                        next_time = next_time.replace(year=current_time.year + 2)
                    return next_time
                except ValueError:
                    # Fallback: add 365 days
                    return current_time + timedelta(days=365)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating next appropriate time: {e}")
            return None
    
    def _calculate_next_trigger_time(self, original_trigger: datetime, repeat_type: str) -> Optional[datetime]:
        """Calculate the next trigger time based on repeat type."""
        try:
            if repeat_type == "daily":
                return original_trigger + timedelta(days=1)
            elif repeat_type == "weekly":
                return original_trigger + timedelta(weeks=1)
            elif repeat_type == "monthly":
                return original_trigger + timedelta(days=30)  # Approximate
            elif repeat_type == "yearly":
                return original_trigger + timedelta(days=365)  # Approximate
            else:
                return None
        except Exception as e:
            logger.error(f"Error calculating next trigger time: {e}")
            return None
    
    # Birthday Operations
    async def save_birthday(self, birthday: Birthday) -> Birthday:
        """Save a birthday to the database."""
        try:
            logger.info(f"Saving birthday for {birthday.person_name}")
            msg_logger.log_database_operation("INSERT", "birthdays", None, success=True)
            
            if not birthday.id:
                birthday.id = uuid4()
                birthday.created_at = datetime.now(timezone.utc)
            
            # Convert to dict with proper serialization
            birthday_data = birthday.dict()
            birthday_data['id'] = str(birthday_data['id'])
            birthday_data['user_id'] = str(birthday_data['user_id'])
            birthday_data['created_at'] = birthday_data['created_at'].isoformat()
            birthday_data['birthdate'] = birthday_data['birthdate'].isoformat() if hasattr(birthday_data['birthdate'], 'isoformat') else str(birthday_data['birthdate'])
            
            result = self.admin_client.table("birthdays").insert(birthday_data).execute()
            
            saved_birthday = Birthday(**result.data[0])
            logger.info(f"Successfully saved birthday for {birthday.person_name} with ID: {saved_birthday.id}")
            msg_logger.log_database_operation("INSERT", "birthdays", str(saved_birthday.id), success=True)
            
            return saved_birthday
            
        except Exception as e:
            logger.error(f"Error saving birthday for {birthday.person_name}: {e}")
            msg_logger.log_database_operation("INSERT", "birthdays", None, success=False, error=str(e))
            raise
    
    async def get_user_birthdays(self, user_id: UUID) -> List[Birthday]:
        """Get user birthdays."""
        try:
            result = self.admin_client.table("birthdays").select("*").eq("user_id", str(user_id)).order("birthdate", desc=False).execute()
            return [Birthday(**b) for b in result.data]
        except Exception as e:
            logger.error(f"Error getting user birthdays: {e}")
            return []
    
    async def get_upcoming_birthdays(self, user_id: UUID, days_ahead: int = 30) -> List[Birthday]:
        """Get upcoming birthdays within specified days."""
        try:
            # Try custom RPC function for date calculations across years
            result = self.admin_client.rpc(
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
                start_time=datetime.now(timezone.utc),
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
            result = self.admin_client.table("sessions").select("*").eq("user_id", str(user_id)).eq("status", SessionStatus.ACTIVE.value).order("start_time", desc=True).limit(1).execute()
            
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
                "end_time": datetime.now(timezone.utc).isoformat()
            }).eq("id", str(session_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    async def update_session_metadata(self, session_id: UUID, metadata: Dict[str, Any]) -> bool:
        """Update session metadata."""
        try:
            result = self.admin_client.table("sessions").update({
                "metadata": metadata
            }).eq("id", str(session_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating session metadata: {e}")
            return False
    
    async def update_session_tags(self, session_id: UUID, tags: List[str]) -> bool:
        """Update session tags."""
        try:
            result = self.admin_client.table("sessions").update({
                "tags": tags
            }).eq("id", str(session_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating session tags: {e}")
            return False
    
    # Tag Operations
    async def get_user_tags(self, user_id: UUID) -> Dict[str, int]:
        """Get user tags with usage counts."""
        try:
            # Try custom RPC function to aggregate tags
            result = self.admin_client.rpc(
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

    # File Operations
    async def save_file_record(self, file: File) -> File:
        """Save a file record to the database."""
        try:
            logger.info(f"Saving file record: {file.original_filename}")
            
            if not file.id:
                file.id = uuid4()
            if not file.created_at:
                file.created_at = datetime.now(timezone.utc)
            
            # Convert to dict with proper serialization
            file_data = file.dict()
            file_data['id'] = str(file_data['id'])
            file_data['user_id'] = str(file_data['user_id'])
            if file_data.get('message_id'):
                file_data['message_id'] = str(file_data['message_id'])
            file_data['created_at'] = file_data['created_at'].isoformat()
            if file_data.get('deleted_at'):
                file_data['deleted_at'] = file_data['deleted_at'].isoformat()
            
            result = self.admin_client.table("files").insert(file_data).execute()
            
            saved_file = File(**result.data[0])
            logger.info(f"Successfully saved file record with ID: {saved_file.id}")
            
            return saved_file
            
        except Exception as e:
            logger.error(f"Error saving file record: {e}")
            raise
    
    async def get_user_files(self, user_id: UUID, file_type: Optional[str] = None) -> List[File]:
        """Get user files."""
        try:
            query = self.admin_client.table("files").select("*").eq("user_id", str(user_id)).eq("upload_status", "completed").is_("deleted_at", "null")
            
            if file_type:
                query = query.eq("file_type", file_type)
            
            result = query.order("created_at", desc=True).execute()
            return [File(**f) for f in result.data]
        except Exception as e:
            logger.error(f"Error getting user files: {e}")
            return []
    
    async def update_file_status(self, file_id: UUID, upload_status: str, transcription_text: Optional[str] = None) -> bool:
        """Update file upload status and transcription."""
        try:
            update_data = {"upload_status": upload_status}
            if transcription_text:
                update_data["transcription_text"] = transcription_text
                update_data["transcription_status"] = "completed"
            
            result = self.admin_client.table("files").update(update_data).eq("id", str(file_id)).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating file status: {e}")
            return False
    
    async def get_file_by_id(self, file_id: UUID) -> Optional[File]:
        """Get file by ID."""
        try:
            result = self.client.table("files").select("*").eq("id", str(file_id)).execute()
            if result.data:
                return File(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return None
