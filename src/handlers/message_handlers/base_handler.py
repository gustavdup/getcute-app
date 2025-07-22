"""
Base handler class for message processing.
All message handlers inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.models.database import Message as DBMessage, User
from src.models.message_types import ProcessedMessage
from src.utils.logger import MessageProcessingLogger


class BaseHandler(ABC):
    """Base class for all message handlers."""
    
    # No longer need a base constructor - each handler initializes its own services
    
    @abstractmethod
    async def can_handle(self, message: ProcessedMessage, user: User, classification: Dict[str, Any]) -> bool:
        """
        Check if this handler can process the given message.
        
        Args:
            message: The incoming message
            user: The user who sent the message
            classification: AI classification results as dict
            
        Returns:
            bool: True if this handler can process the message
        """
        pass
    
    @abstractmethod
    async def handle(self, message: ProcessedMessage, user: User, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the message.
        
        Args:
            message: The incoming message
            user: The user who sent the message
            classification: AI classification results as dict
            
        Returns:
            Dict containing processing results
        """
        pass
    
    def _create_message_data(self, message: ProcessedMessage) -> Dict[str, Any]:
        """Create a standard message data structure for logging."""
        return {
            "message_id": message.message_id,
            "user_phone": message.user_phone,
            "content": message.content,
            "message_type": message.message_type,
            "media_id": message.media_id
        }
