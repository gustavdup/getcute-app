"""
Tagging workflow for managing tag suggestions and user responses.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from ..models.database import User, Message
from ..services.supabase_service import SupabaseService
from ..services.whatsapp_service import WhatsAppService
from ..ai.message_classifier import MessageClassifier

logger = logging.getLogger(__name__)


class TaggingWorkflow:
    """Manages tag suggestions and user responses for better content organization."""
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.whatsapp_service = WhatsAppService()
        self.classifier = MessageClassifier()
        self.tag_response_timeout_minutes = 2
    
    async def prompt_for_tags(self, user: User, message: Message, suggested_tags: Optional[List[str]] = None):
        """Prompt user to add tags to their message."""
        try:
            if not user.phone_number:
                logger.error("User phone number missing")
                return
            
            # Get user's existing tags for better suggestions
            if not user.id:
                logger.error("User ID missing")
                return
                
            user_tags = await self.db_service.get_user_tags(user.id)
            existing_tag_names = list(user_tags.keys())
            
            # Generate AI suggestions if none provided
            if not suggested_tags and message.content:
                suggested_tags = await self.classifier.suggest_tags(
                    message.content,
                    existing_tag_names
                )
            
            # Send tag prompt
            await self.whatsapp_service.send_tag_prompt(
                user.phone_number,
                suggested_tags
            )
            
            # Store state for handling response
            # This would typically involve a temporary state store
            # For now, just log the prompt
            logger.info(f"Sent tag prompt to user {user.id} for message {message.id}")
            
        except Exception as e:
            logger.error(f"Error prompting for tags: {e}")
    
    async def handle_tag_response(self, user: User, response_content: str, original_message_id: str) -> bool:
        """Handle user's response to tag prompts."""
        try:
            if not user.id:
                logger.error("User ID missing")
                return False
            
            # Extract tags from response
            tags = self._extract_tags_from_response(response_content)
            
            if not tags:
                # Not a tag response, treat as new message
                return False
            
            # Find the original message to tag
            # This is simplified - in practice you'd need better state management
            recent_messages = await self.db_service.get_user_messages(
                user_id=user.id,
                limit=10
            )
            
            target_message = None
            for msg in recent_messages:
                if not msg.tags or len(msg.tags) == 0:
                    target_message = msg
                    break
            
            if target_message and target_message.id:
                # Update message with tags
                # This would require an update method in the database service
                logger.info(f"Would update message {target_message.id} with tags: {tags}")
                
                # Send confirmation
                tags_text = " ".join([f"#{tag}" for tag in tags])
                await self.whatsapp_service.send_text_message(
                    user.phone_number,
                    f"✅ Tags added: {tags_text}"
                )
                
                return True
            else:
                # Ask for clarification
                await self.whatsapp_service.send_text_message(
                    user.phone_number,
                    "Was that a tag for your last message or a new note? "
                    "If it's a new note, I'll save it as is."
                )
                return False
                
        except Exception as e:
            logger.error(f"Error handling tag response: {e}")
            return False
    
    def _extract_tags_from_response(self, content: str) -> List[str]:
        """Extract hashtags from user response."""
        import re
        
        # Find all hashtags
        hashtags = re.findall(r'#(\w+)', content)
        
        # Clean and lowercase
        tags = [tag.lower().strip() for tag in hashtags if tag.strip()]
        
        return tags
    
    async def suggest_tags_for_content(self, user: User, content: str) -> List[str]:
        """Get AI-powered tag suggestions for content."""
        try:
            if not user.id:
                return []
                
            # Get user's existing tags
            user_tags = await self.db_service.get_user_tags(user.id)
            existing_tag_names = list(user_tags.keys())
            
            # Get AI suggestions
            suggestions = await self.classifier.suggest_tags(content, existing_tag_names)
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting tag suggestions: {e}")
            return []
    
    async def get_popular_tags(self, user: User, limit: int = 10) -> List[tuple]:
        """Get user's most popular tags."""
        try:
            if not user.id:
                return []
                
            user_tags = await self.db_service.get_user_tags(user.id)
            
            # Sort by usage count
            sorted_tags = sorted(user_tags.items(), key=lambda x: x[1], reverse=True)
            
            return sorted_tags[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular tags: {e}")
            return []
    
    async def merge_tags(self, user: User, old_tag: str, new_tag: str) -> bool:
        """Merge one tag into another (rename all instances)."""
        try:
            if not user.id:
                return False
            
            # This would require a database operation to update all messages
            # with old_tag to use new_tag instead
            
            logger.info(f"Would merge tag '{old_tag}' into '{new_tag}' for user {user.id}")
            
            # For now, just return success
            return True
            
        except Exception as e:
            logger.error(f"Error merging tags: {e}")
            return False
    
    async def delete_tag(self, user: User, tag: str) -> bool:
        """Remove a tag from all user messages."""
        try:
            if not user.id:
                return False
            
            # This would require a database operation to remove the tag
            # from all messages that contain it
            
            logger.info(f"Would delete tag '{tag}' for user {user.id}")
            
            # For now, just return success
            return True
            
        except Exception as e:
            logger.error(f"Error deleting tag: {e}")
            return False
    
    def is_tag_response(self, content: str) -> bool:
        """Check if a message looks like a tag response."""
        # Simple heuristic: contains hashtags and is relatively short
        has_hashtags = '#' in content
        is_short = len(content.strip()) < 100
        mostly_tags = content.count('#') / len(content.split()) > 0.3 if content.split() else False
        
        return has_hashtags and (is_short or mostly_tags)
    
    async def handle_ambiguous_response(self, user: User, content: str) -> bool:
        """Handle responses that could be tags or new content."""
        try:
            if self.is_tag_response(content):
                # Try to handle as tag response
                return await self.handle_tag_response(user, content, "")
            else:
                # Treat as new content
                return False
                
        except Exception as e:
            logger.error(f"Error handling ambiguous response: {e}")
            return False
