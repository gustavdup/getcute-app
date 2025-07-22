"""
Message types and schemas for WhatsApp webhook processing.
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


# WhatsApp Webhook Models
class WhatsAppContact(BaseModel):
    """WhatsApp contact information."""
    profile: Optional[Dict[str, str]] = None
    wa_id: str


class WhatsAppMessage(BaseModel):
    """WhatsApp message from webhook."""
    from_: Optional[str] = Field(None, alias='from')  # Using Field alias for 'from' keyword
    id: str
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    audio: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None
    voice: Optional[Dict[str, str]] = None


class WhatsAppChange(BaseModel):
    """WhatsApp webhook change object."""
    value: Dict[str, Any]
    field: str = "messages"


class WhatsAppEntry(BaseModel):
    """WhatsApp webhook entry object."""
    id: str
    changes: List[WhatsAppChange]


class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload."""
    object: str
    entry: List[WhatsAppEntry]


# Internal Message Processing Models
class ProcessedMessage(BaseModel):
    """Processed message ready for classification."""
    user_phone: str
    message_id: str
    timestamp: datetime
    content: str
    message_type: str  # text, image, audio, etc.
    media_url: Optional[str] = None
    media_id: Optional[str] = None


class ClassificationResult(BaseModel):
    """Result from AI message classification."""
    message_type: str  # note, reminder, birthday, slash_command
    confidence: float
    extracted_data: Dict[str, Any]
    suggested_tags: Optional[List[str]] = None
    requires_followup: bool = False
    followup_type: Optional[str] = None


class ReminderExtraction(BaseModel):
    """Extracted reminder information."""
    title: str
    description: Optional[str] = None
    trigger_time: datetime
    repeat_type: str = "none"
    repeat_interval: Optional[int] = None
    extracted_tags: Optional[List[str]] = None


class BirthdayExtraction(BaseModel):
    """Extracted birthday information."""
    person_name: str
    birthdate: datetime
    year_known: bool = True
    extracted_tags: Optional[List[str]] = None


class TagPromptResponse(BaseModel):
    """Response for tag prompting."""
    should_prompt: bool
    suggested_tags: Optional[List[str]] = None
    timeout_seconds: int = 120


# WhatsApp API Response Models
class WhatsAppTextMessage(BaseModel):
    """WhatsApp text message for sending."""
    messaging_product: str = "whatsapp"
    to: str
    type: str = "text"
    text: Dict[str, str]


class WhatsAppInteractiveButton(BaseModel):
    """WhatsApp interactive button."""
    type: str = "reply"
    reply: Dict[str, str]


class WhatsAppInteractiveAction(BaseModel):
    """WhatsApp interactive action."""
    buttons: List[WhatsAppInteractiveButton]


class WhatsAppInteractiveHeader(BaseModel):
    """WhatsApp interactive header."""
    type: str = "text"
    text: str


class WhatsAppInteractiveBody(BaseModel):
    """WhatsApp interactive body."""
    text: str


class WhatsAppInteractive(BaseModel):
    """WhatsApp interactive message structure."""
    type: str = "button"
    header: Optional[WhatsAppInteractiveHeader] = None
    body: WhatsAppInteractiveBody
    action: WhatsAppInteractiveAction


class WhatsAppInteractiveMessage(BaseModel):
    """WhatsApp interactive message for sending."""
    messaging_product: str = "whatsapp"
    to: str
    type: str = "interactive"
    interactive: WhatsAppInteractive


# Portal and SSO Models
class PortalToken(BaseModel):
    """Portal authentication token."""
    token: str
    expires_at: datetime
    user_id: str
    redirect_path: Optional[str] = None


class SearchQuery(BaseModel):
    """Search query from portal or bot."""
    query: str
    search_type: str = "text"  # text, semantic, image
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
