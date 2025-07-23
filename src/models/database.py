"""
Database schema models for Supabase tables.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


class MessageType(str, Enum):
    """Types of messages that can be processed."""
    NOTE = "note"
    REMINDER = "reminder"
    BIRTHDAY = "birthday"
    SLASH_COMMAND = "slash_command"
    BRAIN_DUMP = "brain_dump"
    COMMAND = "command"


class SourceType(str, Enum):
    """Source types for messages."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"


class SessionStatus(str, Enum):
    """Status of brain dump sessions."""
    ACTIVE = "active"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RepeatType(str, Enum):
    """Reminder repeat types."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class FileType(str, Enum):
    """File types for uploaded media."""
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    VIDEO = "video"


class UploadStatus(str, Enum):
    """Upload status for files."""
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class TranscriptionStatus(str, Enum):
    """Transcription status for audio/video files."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


# Database Models
class User(BaseModel):
    """User model for database storage."""
    id: Optional[UUID] = None
    phone_number: str
    platform: str = "whatsapp"
    timezone: str = "UTC"  # IANA timezone (e.g., "America/New_York", "Europe/Berlin")
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Message(BaseModel):
    """Message model for database storage."""
    id: Optional[UUID] = None
    user_id: UUID
    message_timestamp: datetime
    type: MessageType
    content: str
    tags: Optional[List[str]] = []
    session_id: Optional[UUID] = None
    vector_embedding: Optional[List[float]] = None
    transcription: Optional[str] = None
    source_type: SourceType
    origin_message_id: Optional[str] = None
    media_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Reminder(BaseModel):
    """Reminder model for database storage."""
    id: Optional[UUID] = None
    user_id: UUID
    title: str
    description: Optional[str] = None
    trigger_time: datetime
    repeat_type: RepeatType = RepeatType.NONE
    repeat_interval: Optional[int] = None
    repeat_until: Optional[datetime] = None  # End date for recurring reminders
    tags: Optional[List[str]] = []
    is_active: bool = True
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Birthday(BaseModel):
    """Birthday model for database storage."""
    id: Optional[UUID] = None
    user_id: UUID
    person_name: str
    birthdate: datetime  # Year can be 1900 if unknown
    tags: Optional[List[str]] = []
    notification_settings: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Session(BaseModel):
    """Session model for brain dump sessions."""
    id: Optional[UUID] = None
    user_id: UUID
    type: str = "brain_dump"
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SessionStatus = SessionStatus.ACTIVE
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class File(BaseModel):
    """File model for media storage tracking."""
    id: Optional[UUID] = None
    user_id: UUID
    message_id: Optional[UUID] = None
    filename: str  # Generated filename in storage
    original_filename: str  # Original filename from user
    file_type: FileType
    mime_type: str
    file_size_bytes: int
    storage_path: str  # Full path in Supabase storage
    storage_bucket: str = "user-media"
    upload_status: UploadStatus = UploadStatus.UPLOADING
    transcription_status: TranscriptionStatus = TranscriptionStatus.PENDING
    transcription_text: Optional[str] = None
    duration_seconds: Optional[int] = None  # For audio/video files
    dimensions: Optional[Dict[str, int]] = None  # For images/videos: {"width": 1920, "height": 1080}
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# Response Models
class UserResponse(BaseModel):
    """User response model for API."""
    id: str
    phone_number: str
    platform: str
    created_at: datetime
    last_seen: Optional[datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageResponse(BaseModel):
    """Message response model for API."""
    id: str
    type: MessageType
    content: str
    tags: List[str]
    timestamp: datetime
    source_type: SourceType
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResult(BaseModel):
    """Search result model."""
    message: MessageResponse
    similarity_score: Optional[float] = None
    snippet: Optional[str] = None
