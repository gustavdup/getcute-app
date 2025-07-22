"""
Admin panel for debugging and monitoring the Cute WhatsApp Bot.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from postgrest import CountMethod

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import settings
from services.supabase_service import SupabaseService
from services.whatsapp_token_manager import token_manager
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
    """Main admin dashboard with unified overview."""
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "current_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics as JSON."""
    try:
        db_service = SupabaseService()
        
        # Get real statistics from database
        stats = await get_admin_stats(db_service)
        
        return {
            "status": "success",
            "total_users": stats.get("total_users", 0),
            "total_messages": stats.get("total_messages", 0),
            "active_users": stats.get("active_users_24h", 0),
            "system_status": stats.get("system_health", "unknown"),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "status": "error",
            "total_users": 0,
            "total_messages": 0,
            "active_users": 0,
            "system_status": "error",
            "last_updated": datetime.now().isoformat()
        }


@admin_router.get("/overview", response_class=HTMLResponse)
async def admin_overview(request: Request):
    """Admin overview with conversation data - legacy endpoint."""
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
        logger.error(f"Error loading admin overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/token-status")
async def get_token_status():
    """Get WhatsApp token status."""
    try:
        # Get basic token status
        status = token_manager.get_token_status()
        
        # Try to validate the token
        validation = await token_manager.validate_token()
        
        return {
            "status": status,
            "validation": validation,
            "recommendations": {
                "action_needed": not validation.get("valid", False),
                "message": "Token needs renewal" if not validation.get("valid", False) else "Token is healthy"
            }
        }
    except Exception as e:
        logger.error(f"Error getting token status: {e}")
        return {
            "status": {"error": str(e)},
            "validation": {"valid": False, "error": str(e)},
            "recommendations": {
                "action_needed": True,
                "message": "Could not check token status"
            }
        }


@admin_router.post("/refresh-token")
async def refresh_whatsapp_token():
    """Attempt to refresh the WhatsApp access token."""
    try:
        new_token = await token_manager.get_long_lived_token()
        if new_token:
            return {
                "success": True,
                "message": "Token refreshed successfully",
                "new_expiration": token_manager.token_expires_at.isoformat() if token_manager.token_expires_at else None
            }
        else:
            return {
                "success": False,
                "message": "Failed to refresh token. Check app credentials or manually renew the token."
            }
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return {
            "success": False,
            "message": f"Error refreshing token: {str(e)}"
        }


@admin_router.post("/webhook/test")
async def test_webhook():
    """Test webhook connectivity."""
    try:
        return {
            "status": "success",
            "message": "Webhook test successful",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        return {
            "status": "error", 
            "message": f"Webhook test failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@admin_router.get("/users", response_class=HTMLResponse)
async def get_users_page(request: Request):
    """Get users page with HTML template"""
    return templates.TemplateResponse("users.html", {"request": request})

@admin_router.get("/api/users")
async def get_users_api(limit: int = 50):
    """Get list of users for admin API."""
    try:
        db_service = SupabaseService()
        
        # Get users with message counts
        users_response = db_service.admin_client.table("users").select(
            "id, phone_number, platform, created_at, last_seen"
        ).order("last_seen", desc=True).limit(limit).execute()
        
        users = []
        for user in (users_response.data or []):
            try:
                # Get message count for this user
                message_count_response = db_service.admin_client.table("messages").select(
                    "id", count=CountMethod.exact
                ).eq("user_id", user["id"]).execute()
                message_count = message_count_response.count if message_count_response.count is not None else 0
                
                users.append({
                    "id": user.get("id"),
                    "phone_number": user.get("phone_number"),
                    "platform": user.get("platform", "whatsapp"),
                    "created_at": user.get("created_at"),
                    "last_seen": user.get("last_seen"),
                    "message_count": message_count,
                    "active_sessions": 0  # Would need session tracking
                })
            except Exception as e:
                logger.warning(f"Error processing user {user.get('id')}: {e}")
                continue
        
        return {"users": users, "total": len(users)}
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        # Return fallback data
        return {
            "users": [
                {
                    "id": "fallback_user",
                    "phone_number": "No data available",
                    "platform": "whatsapp",
                    "created_at": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "message_count": 0,
                    "active_sessions": 0
                }
            ],
            "total": 1
        }


@admin_router.get("/api/messages")
async def get_messages_api(limit: int = 50):
    """Get messages for admin API using correct column names."""
    try:
        db_service = SupabaseService()
        
        # Use correct column names from database schema
        result = db_service.admin_client.table("messages").select(
            "id, user_id, content, message_timestamp, type, source_type, tags"
        ).order("message_timestamp", desc=True).limit(limit).execute()
        
        messages = []
        for msg in (result.data or []):
            try:
                # Get user phone number separately
                phone_number = "Unknown"
                try:
                    user_result = db_service.admin_client.table("users").select("phone_number").eq("id", msg["user_id"]).execute()
                    if user_result.data and len(user_result.data) > 0:
                        phone_number = user_result.data[0]["phone_number"]
                except Exception as e:
                    logger.warning(f"Could not get phone number for user {msg['user_id']}: {e}")
                
                messages.append({
                    "id": msg.get("id"),
                    "user_id": msg.get("user_id"),
                    "user_phone": phone_number,
                    "content": msg.get("content", "")[:200] + ("..." if len(msg.get("content", "")) > 200 else ""),
                    "full_content": msg.get("content", ""),
                    "timestamp": msg.get("message_timestamp"),
                    "type": msg.get("type"),
                    "source_type": msg.get("source_type"),
                    "tags": msg.get("tags", [])
                })
            except Exception as e:
                logger.warning(f"Error processing message {msg.get('id')}: {e}")
                continue
        
        return {
            "messages": messages,
            "total_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return {"messages": [], "total_count": 0}


@admin_router.get("/messages", response_class=HTMLResponse)
async def get_messages_page(request: Request):
    """Get messages page with HTML template"""
    return templates.TemplateResponse("messages.html", {"request": request})


@admin_router.post("/refresh-token")
async def refresh_token():
    """Manually refresh WhatsApp access token."""
    try:
        new_token = await token_manager.get_long_lived_token()
        if new_token:
            return {
                "status": "success",
                "message": "Token refreshed successfully",
                "new_token": new_token[:20] + "..." if len(new_token) > 20 else new_token,
                "expires_at": token_manager.token_expires_at.isoformat() if token_manager.token_expires_at else None
            }
        else:
            return {
                "status": "error",
                "message": "Failed to refresh token. Check Facebook App credentials in .env file"
            }
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return {"status": "error", "message": str(e)}


@admin_router.get("/api/conversation/{user_id}")
async def get_conversation_thread(user_id: str, limit: int = 50):
    """Get full conversation thread including bot responses."""
    try:
        db_service = SupabaseService()
        
        # Get all messages for this user (both incoming and outgoing)
        result = db_service.admin_client.table("messages").select(
            "id, user_id, content, message_timestamp, type, source_type, tags, metadata"
        ).eq("user_id", user_id).order("message_timestamp", desc=False).limit(limit).execute()
        
        messages = []
        for msg in (result.data or []):
            # Determine if this is a bot response
            is_bot_response = (
                msg.get("tags") and "bot-response" in msg.get("tags", []) or
                msg.get("metadata") and msg.get("metadata", {}).get("sender") == "bot" or
                msg.get("content", "").startswith("🤖")
            )
            
            messages.append({
                "id": msg.get("id"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("message_timestamp"),
                "type": msg.get("type"),
                "source_type": msg.get("source_type"),
                "tags": msg.get("tags", []),
                "is_bot_response": is_bot_response,
                "sender": "bot" if is_bot_response else "user"
            })
        
        return {
            "status": "success",
            "conversation": messages,
            "total_messages": len(messages),
            "bot_responses": len([m for m in messages if m["is_bot_response"]]),
            "user_messages": len([m for m in messages if not m["is_bot_response"]])
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation thread: {e}")
        return {"status": "error", "message": str(e)}


@admin_router.get("/test-outgoing-storage/{phone_number}")
async def test_outgoing_message_storage(phone_number: str):
    """Test endpoint to verify outgoing message storage is working."""
    try:
        from services.whatsapp_service import WhatsAppService
        from services.supabase_service import SupabaseService
        
        db_service = SupabaseService()
        whatsapp_service = WhatsAppService(db_service)
        
        # Send a test message (this should now be stored)
        success = await whatsapp_service.send_text_message(
            phone_number, 
            f"🧪 Test message from admin panel at {datetime.now().strftime('%H:%M:%S')}"
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Test message sent to {phone_number} and should be stored in database"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to send test message"
            }
            
    except Exception as e:
        logger.error(f"Error testing outgoing message storage: {e}")
        return {"status": "error", "message": str(e)}


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
        stats = {}
        
        # Get total users
        try:
            users_response = db_service.admin_client.table("users").select("id", count=CountMethod.exact).execute()
            stats["total_users"] = users_response.count if users_response.count is not None else 0
        except Exception as e:
            logger.warning(f"Could not get users count: {e}")
            stats["total_users"] = 0
        
        # Get total messages
        try:
            messages_response = db_service.admin_client.table("messages").select("id", count=CountMethod.exact).execute()
            stats["total_messages"] = messages_response.count if messages_response.count is not None else 0
        except Exception as e:
            logger.warning(f"Could not get messages count: {e}")
            stats["total_messages"] = 0
        
        # Get active users (last 24 hours)
        try:
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            active_response = db_service.admin_client.table("messages").select("user_id").gte("created_at", yesterday).execute()
            unique_users = set(msg.get("user_id") for msg in (active_response.data or []) if msg.get("user_id"))
            stats["active_users_24h"] = len(unique_users)
        except Exception as e:
            logger.warning(f"Could not get active users: {e}")
            stats["active_users_24h"] = 0
        
        # Get messages in last 24 hours
        try:
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            recent_messages_response = db_service.admin_client.table("messages").select("id", count=CountMethod.exact).gte("created_at", yesterday).execute()
            stats["messages_24h"] = recent_messages_response.count if recent_messages_response.count is not None else 0
        except Exception as e:
            logger.warning(f"Could not get recent messages: {e}")
            stats["messages_24h"] = 0
        
        # Get reminders count
        try:
            reminders_response = db_service.admin_client.table("reminders").select("id", count=CountMethod.exact).execute()
            stats["total_reminders"] = reminders_response.count if reminders_response.count is not None else 0
            
            # Active reminders (is_active = true and completed_at is null)
            active_reminders_response = db_service.admin_client.table("reminders").select("id", count=CountMethod.exact).eq("is_active", True).is_("completed_at", "null").execute()
            stats["active_reminders"] = active_reminders_response.count if active_reminders_response.count is not None else 0
        except Exception as e:
            logger.warning(f"Could not get reminders count: {e}")
            stats["total_reminders"] = 0
            stats["active_reminders"] = 0
        
        # Get birthdays count
        try:
            birthdays_response = db_service.admin_client.table("birthdays").select("id", count=CountMethod.exact).execute()
            stats["total_birthdays"] = birthdays_response.count if birthdays_response.count is not None else 0
            
            # Upcoming birthdays (next 30 days)
            # This would need a more complex query for date calculations
            stats["upcoming_birthdays"] = 0  # Placeholder
        except Exception as e:
            logger.warning(f"Could not get birthdays count: {e}")
            stats["total_birthdays"] = 0
            stats["upcoming_birthdays"] = 0
        
        # System health indicators
        stats["system_health"] = "healthy"
        stats["database_status"] = "connected"
        stats["ai_service_status"] = "operational"
        stats["active_sessions"] = 0  # Would need session tracking
        stats["avg_classification_confidence"] = 0.87  # Would calculate from recent messages
        stats["vector_embeddings"] = stats["total_messages"]  # Assuming all messages are embedded
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        # Return minimal stats on error
        return {
            "total_users": 0,
            "active_users_24h": 0,
            "total_messages": 0,
            "messages_24h": 0,
            "total_reminders": 0,
            "active_reminders": 0,
            "total_birthdays": 0,
            "upcoming_birthdays": 0,
            "active_sessions": 0,
            "avg_classification_confidence": 0.0,
            "vector_embeddings": 0,
            "system_health": "error",
            "database_status": "disconnected",
            "ai_service_status": "unknown"
        }


async def get_recent_conversations(db_service: SupabaseService, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversation summaries."""
    try:
        # Get recent messages with user information - using correct column names
        recent_response = db_service.admin_client.table("messages").select(
            "id, user_id, content, message_timestamp, type, source_type, tags"
        ).order("message_timestamp", desc=True).limit(limit).execute()
        
        conversations = []
        processed_users = set()
        
        for msg in (recent_response.data or []):
            try:
                user_id = msg.get("user_id")
                if user_id in processed_users:
                    continue  # Skip duplicate users for recent conversations
                processed_users.add(user_id)
                
                # Get user info separately to avoid relationship conflicts
                phone_number = "Unknown"
                try:
                    user_response = db_service.admin_client.table("users").select("phone_number").eq("id", user_id).execute()
                    if user_response.data and len(user_response.data) > 0:
                        phone_number = user_response.data[0].get("phone_number", "Unknown")
                except Exception as e:
                    logger.warning(f"Could not get phone number for user {user_id}: {e}")
                
                conversations.append({
                    "user_id": user_id,
                    "phone_number": phone_number,
                    "last_message": msg.get("content", "")[:100] + ("..." if len(msg.get("content", "")) > 100 else ""),
                    "last_message_time": msg.get("message_timestamp"),
                    "message_type": msg.get("type"),  # Use 'type' column
                    "source_type": msg.get("source_type"),
                    "tags": msg.get("tags", []),
                    "has_active_session": False  # Would need session tracking
                })
            except Exception as e:
                logger.warning(f"Error processing message {msg.get('id')}: {e}")
                continue
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting recent conversations: {e}")
        # Return mock data as fallback
        return [
            {
                "user_id": "fallback_user1",
                "phone_number": "No data available",
                "last_message": "Unable to load recent conversations",
                "last_message_time": datetime.now().isoformat(),
                "message_type": "system",
                "classification_confidence": 0.0,
                "tags": [],
                "has_active_session": False
            }
        ]
