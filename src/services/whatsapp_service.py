"""
WhatsApp Business API service for sending and receiving messages.
"""
import logging
import json
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime
from config.settings import settings
from services.whatsapp_token_manager import token_manager
from models.database import Message, MessageType, SourceType
from models.message_types import (
    WhatsAppTextMessage, WhatsAppInteractiveMessage,
    WhatsAppInteractive, WhatsAppInteractiveBody,
    WhatsAppInteractiveAction, WhatsAppInteractiveButton,
    WhatsAppInteractiveHeader
)

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for WhatsApp Business API operations."""
    
    def __init__(self, db_service=None):
        self.base_url = f"https://graph.facebook.com/v18.0/{settings.whatsapp_phone_number_id}"
        self.db_service = db_service
        
    def set_db_service(self, db_service):
        """Set the database service for storing outgoing messages."""
        self.db_service = db_service
    
    async def _store_outgoing_message(self, user_phone: str, message_content: str, message_type: str = "text"):
        """Store outgoing messages in the database."""
        if not self.db_service:
            return
            
        try:
            # Get or create user from phone number
            user = await self.db_service.get_or_create_user(user_phone)
            
            # Create outgoing message record
            outgoing_message = Message(
                user_id=user.id,
                message_timestamp=datetime.now(),
                type=MessageType.NOTE,  # Bot responses are generally notes/responses
                content=f"🤖 {message_content}",  # Prefix with robot emoji to indicate bot response
                source_type=SourceType.TEXT,
                tags=["bot-response"],  # Tag all bot responses
                metadata={"direction": "outgoing", "sender": "bot"}  # Store direction in metadata
            )
            
            await self.db_service.save_message(outgoing_message)
            logger.debug(f"Stored outgoing message to {user_phone}")
            
        except Exception as e:
            logger.warning(f"Failed to store outgoing message: {e}")
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with a valid access token."""
        try:
            token = await token_manager.ensure_valid_token()
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        except Exception as e:
            logger.error(f"Failed to get valid token: {e}")
            # Fallback to configured token
            return {
                "Authorization": f"Bearer {settings.whatsapp_access_token}",
                "Content-Type": "application/json"
            }
    
    async def send_text_message(self, to: str, message: str) -> bool:
        """Send a text message."""
        try:
            payload = WhatsAppTextMessage(
                to=to,
                text={"body": message}
            )
            
            headers = await self._get_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload.dict()
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent successfully to {to}")
                    
                    # Store the outgoing message in database
                    await self._store_outgoing_message(to, message)
                    
                    return True
                else:
                    logger.error(f"Failed to send message: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    async def send_interactive_message(
        self, 
        to: str, 
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None
    ) -> bool:
        """Send an interactive message with buttons."""
        try:
            # Create buttons
            button_objects = []
            for i, button in enumerate(buttons[:3]):  # WhatsApp allows max 3 buttons
                button_objects.append(
                    WhatsAppInteractiveButton(
                        reply={
                            "id": button.get("id", f"btn_{i}"),
                            "title": button.get("title", f"Option {i+1}")
                        }
                    )
                )
            
            # Create interactive structure
            interactive = WhatsAppInteractive(
                body=WhatsAppInteractiveBody(text=body_text),
                action=WhatsAppInteractiveAction(buttons=button_objects)
            )
            
            if header_text:
                interactive.header = WhatsAppInteractiveHeader(text=header_text)
            
            payload = WhatsAppInteractiveMessage(
                to=to,
                interactive=interactive
            )
            
            headers = await self._get_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload.dict()
                )
                
                if response.status_code == 200:
                    logger.info(f"Interactive message sent successfully to {to}")
                    return True
                else:
                    logger.error(f"Failed to send interactive message: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp interactive message: {e}")
            return False
    
    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp."""
        try:
            headers = await self._get_headers()
            
            # First, get the media URL
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{media_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get media URL: {response.text}")
                    return None
                
                media_data = response.json()
                media_url = media_data.get("url")
                
                if not media_url:
                    logger.error("No URL found in media response")
                    return None
                
                # Download the media
                media_response = await client.get(
                    media_url,
                    headers=headers
                )
                
                if media_response.status_code == 200:
                    return media_response.content
                else:
                    logger.error(f"Failed to download media: {media_response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading WhatsApp media: {e}")
            return None
    
    def verify_webhook(self, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook."""
        if token == settings.whatsapp_webhook_verify_token:
            return challenge
        return None
    
    # Pre-built message templates
    async def send_help_menu(self, to: str) -> bool:
        """Send the help menu with interactive buttons."""
        buttons = [
            {"id": "help_notes", "title": "💭 How to save notes?"},
            {"id": "help_tags", "title": "🏷️ How to add tags?"},
            {"id": "help_reminders", "title": "⏰ How reminders work?"}
        ]
        
        return await self.send_interactive_message(
            to=to,
            header_text="🤖 Cute Bot Help",
            body_text="What would you like to know about?",
            buttons=buttons
        )
    
    async def send_notes_menu(self, to: str) -> bool:
        """Send the notes management menu."""
        buttons = [
            {"id": "notes_recent", "title": "📝 Last 24h notes"},
            {"id": "notes_by_tag", "title": "🏷️ Filter by tag"},
            {"id": "notes_portal", "title": "🌐 View in portal"}
        ]
        
        return await self.send_interactive_message(
            to=to,
            header_text="📚 Your Notes",
            body_text="How would you like to view your notes?",
            buttons=buttons
        )
    
    async def send_reminders_menu(self, to: str) -> bool:
        """Send the reminders management menu."""
        buttons = [
            {"id": "reminders_upcoming", "title": "⏰ Upcoming reminders"},
            {"id": "reminders_recurring", "title": "🔄 Recurring reminders"},
            {"id": "reminders_portal", "title": "🌐 Manage in portal"}
        ]
        
        return await self.send_interactive_message(
            to=to,
            header_text="⏰ Your Reminders",
            body_text="What would you like to do with your reminders?",
            buttons=buttons
        )
    
    async def send_birthdays_menu(self, to: str) -> bool:
        """Send the birthdays management menu."""
        buttons = [
            {"id": "birthdays_upcoming", "title": "🎂 Upcoming birthdays"},
            {"id": "birthdays_add", "title": "➕ Add new birthday"},
            {"id": "birthdays_portal", "title": "🌐 Birthday manager"}
        ]
        
        return await self.send_interactive_message(
            to=to,
            header_text="🎂 Birthday Tracker",
            body_text="What would you like to do?",
            buttons=buttons
        )
    
    async def send_search_menu(self, to: str) -> bool:
        """Send the search options menu."""
        buttons = [
            {"id": "search_text", "title": "📝 Search with text"},
            {"id": "search_image", "title": "🖼️ Upload image"},
            {"id": "search_voice", "title": "🎤 Send voice note"}
        ]
        
        return await self.send_interactive_message(
            to=to,
            header_text="🔍 Search Your Content",
            body_text="How would you like to search?",
            buttons=buttons
        )
    
    async def send_tag_prompt(self, to: str, suggested_tags: Optional[List[str]] = None) -> bool:
        """Send a tag suggestion prompt."""
        message = "Want to add tags to this? Reply within 2 minutes with #tags."
        
        if suggested_tags:
            tags_text = " ".join([f"#{tag}" for tag in suggested_tags])
            message += f"\n\nSuggested tags: {tags_text}"
        
        return await self.send_text_message(to, message)
    
    async def send_brain_dump_prompt(self, to: str, tags: List[str]) -> bool:
        """Send brain dump session continuation prompt."""
        tags_text = " ".join([f"#{tag}" for tag in tags])
        message = f"Want to keep dumping into {tags_text}? Send /end to finish."
        
        return await self.send_text_message(to, message)
    
    async def send_portal_link(self, to: str, portal_url: str, context: str = "dashboard") -> bool:
        """Send an authenticated portal link."""
        context_messages = {
            "dashboard": "🌐 Here's your personal dashboard:",
            "search": "🔍 Here are your search results:",
            "notes": "📝 View your notes here:",
            "reminders": "⏰ Manage your reminders:",
            "birthdays": "🎂 Your birthday manager:"
        }
        
        default_message = "🌐 Here's your portal:"
        message = f"{context_messages.get(context, default_message)}\n\n{portal_url}"
        return await self.send_text_message(to, message)
