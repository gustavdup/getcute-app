"""
Slash command handler for processing bot commands.
"""
import logging
from typing import Dict, Any
from models.message_types import ProcessedMessage, ClassificationResult
from models.database import User
from services.whatsapp_service import WhatsAppService
from services.supabase_service import SupabaseService
from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class SlashCommandHandler:
    """Handles slash commands like /portal, /help, /tags, etc."""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.db_service = SupabaseService()
        # self.auth_service = AuthService()  # Will create this
    
    async def handle_command(self, user: User, message: ProcessedMessage, classification: ClassificationResult):
        """Route slash commands to appropriate handlers."""
        try:
            command = classification.extracted_data.get("command", "").lower()
            
            command_handlers = {
                "/portal": self._handle_portal,
                "/help": self._handle_help,
                "/tags": self._handle_tags,
                "/notes": self._handle_notes,
                "/reminders": self._handle_reminders,
                "/birthdays": self._handle_birthdays,
                "/search": self._handle_search,
                "/end": self._handle_end_session
            }
            
            handler = command_handlers.get(command)
            if handler:
                await handler(user, message)
            else:
                await self._handle_unknown_command(user, message, command)
                
        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            await self.whatsapp_service.send_text_message(
                message.user_phone,
                "Sorry, I couldn't process that command. Try /help for available options."
            )
    
    async def _handle_portal(self, user: User, message: ProcessedMessage):
        """Handle /portal command - send authenticated dashboard link."""
        try:
            # Generate SSO token and portal URL
            # For now, send a placeholder
            portal_url = f"https://your-domain.com/portal?token=placeholder_token_for_{user.id}"
            
            await self.whatsapp_service.send_portal_link(
                message.user_phone,
                portal_url,
                "dashboard"
            )
            
        except Exception as e:
            logger.error(f"Error handling portal command: {e}")
    
    async def _handle_help(self, user: User, message: ProcessedMessage):
        """Handle /help command - send interactive help menu."""
        try:
            await self.whatsapp_service.send_help_menu(message.user_phone)
            
        except Exception as e:
            logger.error(f"Error handling help command: {e}")
    
    async def _handle_tags(self, user: User, message: ProcessedMessage):
        """Handle /tags command - show user's tags."""
        try:
            if not user.id:
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "Unable to retrieve your tags right now. Please try again."
                )
                return
                
            user_tags = await self.db_service.get_user_tags(user.id)
            
            if not user_tags:
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "🏷️ You don't have any tags yet! Start adding tags to your notes with #tagname"
                )
                return
            
            # Sort tags by usage count
            sorted_tags = sorted(user_tags.items(), key=lambda x: x[1], reverse=True)
            
            # Format tag list
            tag_lines = []
            for tag, count in sorted_tags[:20]:  # Show top 20 tags
                tag_lines.append(f"#{tag} ({count})")
            
            tag_text = "🏷️ Your Tags:\n\n" + "\n".join(tag_lines)
            
            if len(sorted_tags) > 20:
                tag_text += f"\n\n... and {len(sorted_tags) - 20} more. View all in your portal."
            
            await self.whatsapp_service.send_text_message(message.user_phone, tag_text)
            
        except Exception as e:
            logger.error(f"Error handling tags command: {e}")
    
    async def _handle_notes(self, user: User, message: ProcessedMessage):
        """Handle /notes command - send notes menu."""
        try:
            await self.whatsapp_service.send_notes_menu(message.user_phone)
            
        except Exception as e:
            logger.error(f"Error handling notes command: {e}")
    
    async def _handle_reminders(self, user: User, message: ProcessedMessage):
        """Handle /reminders command - send reminders menu."""
        try:
            await self.whatsapp_service.send_reminders_menu(message.user_phone)
            
        except Exception as e:
            logger.error(f"Error handling reminders command: {e}")
    
    async def _handle_birthdays(self, user: User, message: ProcessedMessage):
        """Handle /birthdays command - send birthdays menu."""
        try:
            await self.whatsapp_service.send_birthdays_menu(message.user_phone)
            
        except Exception as e:
            logger.error(f"Error handling birthdays command: {e}")
    
    async def _handle_search(self, user: User, message: ProcessedMessage):
        """Handle /search command - send search menu."""
        try:
            await self.whatsapp_service.send_search_menu(message.user_phone)
            
        except Exception as e:
            logger.error(f"Error handling search command: {e}")
    
    async def _handle_end_session(self, user: User, message: ProcessedMessage):
        """Handle /end command - end active brain dump session."""
        try:
            if not user.id:
                return
                
            active_session = await self.db_service.get_active_session(user.id)
            
            if active_session:
                # End the session if it has a valid ID
                if active_session.id:
                    await self.db_service.end_session(active_session.id)
                    tags_text = " ".join([f"#{tag}" for tag in (active_session.tags or [])])
                    await self.whatsapp_service.send_text_message(
                        message.user_phone,
                        f"✅ Brain dump session ended! Your notes are saved. {tags_text}"
                    )
                else:
                    await self.whatsapp_service.send_text_message(
                        message.user_phone,
                        "❌ Error: Session has no valid ID. Please try again."
                    )
            else:
                await self.whatsapp_service.send_text_message(
                    message.user_phone,
                    "No active brain dump session to end."
                )
                
        except Exception as e:
            logger.error(f"Error handling end session command: {e}")
    
    async def _handle_unknown_command(self, user: User, message: ProcessedMessage, command: str):
        """Handle unknown slash commands."""
        await self.whatsapp_service.send_text_message(
            message.user_phone,
            f"Unknown command: {command}\n\nAvailable commands:\n"
            "• /portal - Access your dashboard\n"
            "• /help - Get help\n"
            "• /tags - View your tags\n"
            "• /notes - Manage notes\n"
            "• /reminders - Manage reminders\n"
            "• /birthdays - Manage birthdays\n"
            "• /search - Search your content\n"
            "• /end - End brain dump session"
        )


# FastAPI router for API endpoints
from fastapi import APIRouter

commands_router = APIRouter()

@commands_router.get("/")
async def commands_info():
    """Information about available commands."""
    return {
        "commands": [
            {"command": "/portal", "description": "Access your personal dashboard"},
            {"command": "/help", "description": "Get help and guidance"},
            {"command": "/tags", "description": "View and manage your tags"},
            {"command": "/notes", "description": "Access your notes"},
            {"command": "/reminders", "description": "Manage your reminders"},
            {"command": "/birthdays", "description": "Track birthdays"},
            {"command": "/search", "description": "Search your content"},
            {"command": "/end", "description": "End brain dump session"}
        ]
    }
