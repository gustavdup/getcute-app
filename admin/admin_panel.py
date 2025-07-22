"""
Admin panel for debugging and monitoring the Cute WhatsApp Bot.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import settings
from services.supabase_service import SupabaseService
from models.database import User, Message

logger = logging.getLogger(__name__)

admin_router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")


def verify_admin_access(username: Optional[str] = None, password: Optional[str] = None):
    """Simple admin authentication - in production use proper auth."""
    if not settings.debug:
        if username != settings.admin_username or password != settings.admin_password:
            raise HTTPException(status_code=401, detail="Unauthorized")


@admin_router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard with conversation overview."""
    try:
        db_service = SupabaseService()
        
        # Get recent statistics
        stats = await get_admin_stats(db_service)
        
        # Get recent conversations
        recent_conversations = await get_recent_conversations(db_service)
        
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "stats": stats,
            "conversations": recent_conversations,
            "current_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/users")
async def get_users(limit: int = 50):
    """Get list of users for admin."""
    try:
        db_service = SupabaseService()
        
        # This would be implemented with proper pagination
        # For now, return mock data
        users = [
            {
                "id": "user1",
                "phone_number": "+1234567890",
                "platform": "whatsapp",
                "created_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "message_count": 45,
                "active_sessions": 0
            },
            {
                "id": "user2", 
                "phone_number": "+1987654321",
                "platform": "whatsapp",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "last_seen": (datetime.now() - timedelta(hours=2)).isoformat(),
                "message_count": 23,
                "active_sessions": 1
            }
        ]
        
        return {"users": users, "total": len(users)}
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/conversations/{user_id}")
async def get_user_conversation(user_id: str, limit: int = 100):
    """Get full conversation for a specific user."""
    try:
        db_service = SupabaseService()
        
        # This would fetch actual conversation data
        # For now, return mock conversation
        conversation = [
            {
                "id": "msg1",
                "timestamp": datetime.now().isoformat(),
                "type": "note",
                "content": "Remember to buy groceries",
                "tags": ["personal", "shopping"],
                "classification_result": {
                    "message_type": "note",
                    "confidence": 0.95,
                    "ai_reasoning": "Clear note-taking intent, no time references"
                },
                "source_type": "text",
                "session_id": None,
                "vector_status": "embedded"
            },
            {
                "id": "msg2", 
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "type": "reminder",
                "content": "Call mom tomorrow at 2pm",
                "tags": ["family"],
                "classification_result": {
                    "message_type": "reminder", 
                    "confidence": 0.88,
                    "ai_reasoning": "Contains time reference and action item"
                },
                "source_type": "text",
                "session_id": None,
                "vector_status": "embedded"
            }
        ]
        
        return {
            "user_id": user_id,
            "conversation": conversation,
            "total_messages": len(conversation)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/stats")
async def get_system_stats():
    """Get system-wide statistics."""
    try:
        db_service = SupabaseService()
        
        stats = await get_admin_stats(db_service)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/errors")
async def get_recent_errors(limit: int = 50):
    """Get recent error logs."""
    try:
        # This would integrate with logging system
        # For now, return mock errors
        errors = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": "Failed to process media file",
                "context": {
                    "user_id": "user1",
                    "message_id": "msg123",
                    "error_type": "MediaProcessingError"
                }
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "level": "WARNING",
                "message": "AI classification confidence below threshold",
                "context": {
                    "user_id": "user2",
                    "message_id": "msg124",
                    "confidence": 0.45
                }
            }
        ]
        
        return {"errors": errors, "total": len(errors)}
        
    except Exception as e:
        logger.error(f"Error getting errors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_admin_stats(db_service: SupabaseService) -> Dict[str, Any]:
    """Get statistics for admin dashboard."""
    try:
        # This would query actual database
        # For now, return mock stats
        return {
            "total_users": 156,
            "active_users_24h": 45,
            "total_messages": 3247,
            "messages_24h": 189,
            "total_reminders": 234,
            "active_reminders": 87,
            "total_birthdays": 156,
            "upcoming_birthdays": 12,
            "active_sessions": 3,
            "avg_classification_confidence": 0.87,
            "vector_embeddings": 3102,
            "system_health": "healthy",
            "database_status": "connected",
            "ai_service_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return {}


async def get_recent_conversations(db_service: SupabaseService, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversation summaries."""
    try:
        # This would query actual recent conversations
        # For now, return mock data
        return [
            {
                "user_id": "user1",
                "phone_number": "+1234567890",
                "last_message": "Remember to buy groceries",
                "last_message_time": datetime.now().isoformat(),
                "message_type": "note",
                "classification_confidence": 0.95,
                "tags": ["personal", "shopping"],
                "has_active_session": False
            },
            {
                "user_id": "user2",
                "phone_number": "+1987654321", 
                "last_message": "#work #ideas brainstorming session notes",
                "last_message_time": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "message_type": "brain_dump_start",
                "classification_confidence": 1.0,
                "tags": ["work", "ideas"],
                "has_active_session": True
            }
        ]
        
    except Exception as e:
        logger.error(f"Error getting recent conversations: {e}")
        return []
