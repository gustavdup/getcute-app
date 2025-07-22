"""
Handler manager that coordinates all message handlers.
"""
from typing import List, Dict, Any
from models.message_types import ProcessedMessage
from models.database import User
from .base_handler import BaseHandler
from .birthday_handler import BirthdayHandler
from .note_handler import NoteHandler
from .reminder_handler import ReminderHandler


class HandlerManager:
    """Manages and routes messages to appropriate handlers."""
    
    def __init__(self, db_service, whatsapp_service, openai_service):
        """Initialize the handler manager with services."""
        self.db_service = db_service
        self.whatsapp_service = whatsapp_service
        self.openai_service = openai_service
        
        # Initialize all handlers
        self.handlers: List[BaseHandler] = [
            BirthdayHandler(db_service, whatsapp_service, openai_service),
            ReminderHandler(db_service, whatsapp_service, openai_service),
            NoteHandler(db_service, whatsapp_service, openai_service),  # Note handler should be last as fallback
        ]
    
    async def process_message(self, message: ProcessedMessage, user: User, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route the message to the appropriate handler.
        
        Args:
            message: The processed message
            user: The user who sent the message
            classification: AI classification results
            
        Returns:
            Dict containing processing results
        """
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
    
    def get_handler_by_type(self, handler_type: str) -> BaseHandler:
        """Get a specific handler by type."""
        handler_map = {
            "birthday": BirthdayHandler,
            "reminder": ReminderHandler,
            "note": NoteHandler
        }
        
        handler_class = handler_map.get(handler_type)
        if not handler_class:
            raise ValueError(f"Unknown handler type: {handler_type}")
        
        # Find the handler instance
        for handler in self.handlers:
            if isinstance(handler, handler_class):
                return handler
        
        # If not found, create a new instance
        return handler_class(self.db_service, self.whatsapp_service, self.openai_service)
