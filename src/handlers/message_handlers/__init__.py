"""
Message handlers package.

This package contains specialized handlers for different types of messages:
- BirthdayHandler: Processes birthday-related messages using AI extraction
- ReminderHandler: Processes reminder messages using AI extraction
- NoteHandler: Processes general note messages
- BaseHandler: Base class for all handlers
"""

from .base_handler import BaseHandler
from .birthday_handler import BirthdayHandler
from .note_handler import NoteHandler
from .reminder_handler import ReminderHandler

__all__ = [
    "BaseHandler",
    "BirthdayHandler", 
    "NoteHandler",
    "ReminderHandler"
]
