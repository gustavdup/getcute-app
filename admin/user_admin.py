"""
Comprehensive user admin panel for viewing all user interactions and data.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import settings
from services.supabase_service import SupabaseService
from models.database import User, Message, Reminder, Birthday, Session

logger = logging.getLogger(__name__)

user_admin_router = APIRouter()
db_service = SupabaseService()

# Set up templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


@user_admin_router.get("/users", response_class=HTMLResponse)
async def user_selection_page(request: Request):
    """Show user selection page."""
    try:
        # Get all users with basic stats
        users_result = db_service.admin_client.table("users").select("*").order("last_seen", desc=True).execute()
        users = users_result.data if users_result.data else []
        
        # Get message counts for each user
        for user in users:
            try:
                messages_result = db_service.admin_client.table("messages").select("id").eq("user_id", user['id']).execute()
                user['message_count'] = len(messages_result.data) if messages_result.data else 0
            except:
                user['message_count'] = 0
        
        return templates.TemplateResponse("user_selection.html", {
            "request": request,
            "users": users,
            "total_users": len(users)
        })
    except Exception as e:
        logger.error(f"Error loading user selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@user_admin_router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_detail_page(request: Request, user_id: str):
    """Show comprehensive user detail page."""
    try:
        # Get user info
        user_result = db_service.admin_client.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_result.data[0]
        
        # Get all messages without files join to avoid relationship conflicts
        messages_result = db_service.admin_client.table("messages").select(
            "id, user_id, content, message_timestamp, type, tags, file_id, media_url, metadata"
        ).eq("user_id", user_id).order("message_timestamp", desc=True).execute()
        messages = messages_result.data if messages_result.data else []
        
        # Get file info separately for messages that have files
        for msg in messages:
            if msg.get("file_id"):
                try:
                    file_result = db_service.admin_client.table("files").select("*").eq("id", msg["file_id"]).execute()
                    if file_result.data and len(file_result.data) > 0:
                        msg["file_info"] = file_result.data[0]
                except Exception as e:
                    logger.warning(f"Could not get file info for message {msg['id']}: {e}")
                    msg["file_info"] = None
        
        # Get reminders
        reminders_result = db_service.admin_client.table("reminders").select("*").eq("user_id", user_id).order("trigger_time", desc=True).execute()
        reminders = reminders_result.data if reminders_result.data else []
        
        # Get birthdays (most recently added first)
        birthdays_result = db_service.admin_client.table("birthdays").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        birthdays = birthdays_result.data if birthdays_result.data else []
        
        # Get sessions
        sessions_result = db_service.admin_client.table("sessions").select("*").eq("user_id", user_id).order("start_time", desc=True).execute()
        sessions = sessions_result.data if sessions_result.data else []
        
        # Organize messages by type and date
        organized_data = organize_user_data(messages, reminders, birthdays, sessions)
        
        return templates.TemplateResponse("user_detail.html", {
            "request": request,
            "user": user,
            "organized_data": organized_data,
            "stats": calculate_user_stats(messages, reminders, birthdays, sessions)
        })
        
    except Exception as e:
        logger.error(f"Error loading user detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@user_admin_router.get("/api/users/{user_id}/timeline")
async def get_user_timeline(user_id: str, days: int = Query(30, description="Number of days to look back")):
    """Get chronological timeline of all user activities."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all messages without files join to avoid relationship conflicts (newest first)
        messages_result = db_service.admin_client.table("messages").select(
            "id, user_id, content, message_timestamp, type, tags, file_id, media_url, metadata, source_type"
        ).eq("user_id", user_id).gte("message_timestamp", cutoff_date.isoformat()).order("message_timestamp", desc=True).execute()
        
        messages = messages_result.data if messages_result.data else []
        
        # Get file info separately for messages that have files
        for msg in messages:
            if msg.get("file_id"):
                try:
                    file_result = db_service.admin_client.table("files").select(
                        "filename, file_type, transcription_text, storage_path, upload_status"
                    ).eq("id", msg["file_id"]).execute()
                    if file_result.data and len(file_result.data) > 0:
                        msg["file_info"] = file_result.data[0]
                except Exception as e:
                    logger.warning(f"Could not get file info for message {msg['id']}: {e}")
                    msg["file_info"] = None
        
        # Get reminders
        reminders_result = db_service.admin_client.table("reminders").select("*").eq("user_id", user_id).gte("created_at", cutoff_date.isoformat()).execute()
        reminders = reminders_result.data if reminders_result.data else []
        
        # Get birthdays
        birthdays_result = db_service.admin_client.table("birthdays").select("*").eq("user_id", user_id).gte("created_at", cutoff_date.isoformat()).execute()
        birthdays = birthdays_result.data if birthdays_result.data else []
        
        # Create timeline entries
        timeline = []
        
        for msg in messages:
            timeline.append({
                "type": "message",
                "timestamp": msg.get("message_timestamp"),
                "data": msg
            })
        
        for reminder in reminders:
            timeline.append({
                "type": "reminder",
                "timestamp": reminder.get("created_at"),
                "data": reminder
            })
            
        for birthday in birthdays:
            timeline.append({
                "type": "birthday",
                "timestamp": birthday.get("created_at"),
                "data": birthday
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "status": "success",
            "timeline": timeline,
            "total_items": len(timeline)
        }
        
    except Exception as e:
        logger.error(f"Error getting user timeline: {e}")
        return {"status": "error", "message": str(e)}


@user_admin_router.get("/api/users/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get detailed user statistics."""
    try:
        # Get all messages
        messages_result = db_service.admin_client.table("messages").select("*").eq("user_id", user_id).execute()
        messages = messages_result.data if messages_result.data else []
        
        # Get files
        files_result = db_service.admin_client.table("files").select("*").eq("user_id", user_id).execute()
        files = files_result.data if files_result.data else []
        
        # Get reminders
        reminders_result = db_service.admin_client.table("reminders").select("*").eq("user_id", user_id).execute()
        reminders = reminders_result.data if reminders_result.data else []
        
        # Get birthdays
        birthdays_result = db_service.admin_client.table("birthdays").select("*").eq("user_id", user_id).execute()
        birthdays = birthdays_result.data if birthdays_result.data else []
        
        # Calculate stats
        stats = {
            "total_messages": len(messages),
            "messages_by_type": {},
            "messages_by_source": {},
            "total_files": len(files),
            "files_by_type": {},
            "total_reminders": len(reminders),
            "active_reminders": len([r for r in reminders if r.get("is_active")]),
            "completed_reminders": len([r for r in reminders if r.get("completed_at")]),
            "total_birthdays": len(birthdays),
            "total_tags": 0,
            "most_used_tags": {},
            "activity_by_day": {},
            "first_message": None,
            "last_message": None
        }
        
        # Analyze messages
        all_tags = []
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            stats["messages_by_type"][msg_type] = stats["messages_by_type"].get(msg_type, 0) + 1
            
            source_type = msg.get("source_type", "unknown")
            stats["messages_by_source"][source_type] = stats["messages_by_source"].get(source_type, 0) + 1
            
            if msg.get("tags"):
                all_tags.extend(msg["tags"])
                
        # Analyze files
        for file in files:
            file_type = file.get("file_type", "unknown")
            stats["files_by_type"][file_type] = stats["files_by_type"].get(file_type, 0) + 1
        
        # Tag analysis
        stats["total_tags"] = len(all_tags)
        for tag in all_tags:
            stats["most_used_tags"][tag] = stats["most_used_tags"].get(tag, 0) + 1
        
        # Sort tags by usage
        stats["most_used_tags"] = dict(sorted(stats["most_used_tags"].items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Date analysis
        if messages:
            sorted_messages = sorted(messages, key=lambda x: x.get("message_timestamp", ""))
            stats["first_message"] = sorted_messages[0].get("message_timestamp")
            stats["last_message"] = sorted_messages[-1].get("message_timestamp")
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {"status": "error", "message": str(e)}


@user_admin_router.get("/api/conversation/{user_id}")
async def get_user_conversation(user_id: str, days: int = Query(30, description="Number of days to look back")):
    """Get user conversation/messages for timeline display - matches frontend expectation."""
    try:
        # Build the query
        query = db_service.admin_client.table("messages").select(
            "id, user_id, content, message_timestamp, type, tags, file_id, media_url, metadata, source_type"
        ).eq("user_id", user_id)
        
        # Apply date filter only if days > 0
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.gte("message_timestamp", cutoff_date.isoformat())
        
        # Execute query with ordering
        messages_result = query.order("message_timestamp", desc=True).execute()
        
        messages = messages_result.data if messages_result.data else []
        
        # Debug logging
        logger.info(f"Conversation API for user {user_id}, days={days}: Found {len(messages)} messages")
        brain_dumps = [m for m in messages if m.get('type') == 'brain_dump']
        logger.info(f"Brain dumps found: {len(brain_dumps)}")
        for bd in brain_dumps:
            logger.info(f"  Brain dump: {bd.get('id')} - {bd.get('message_timestamp')} - Content length: {len(bd.get('content', ''))}")
        
        # Get file info separately for messages that have files
        for msg in messages:
            if msg.get("file_id"):
                try:
                    file_result = db_service.admin_client.table("files").select(
                        "filename, file_type, transcription_text, storage_path, upload_status"
                    ).eq("id", msg["file_id"]).execute()
                    if file_result.data and len(file_result.data) > 0:
                        msg["file_info"] = file_result.data[0]
                except Exception as e:
                    logger.warning(f"Could not get file info for message {msg['id']}: {e}")
                    msg["file_info"] = None
        
        return {
            "status": "success",
            "conversation": messages,  # Use "conversation" key as expected by frontend
            "messages": messages,      # Also provide "messages" as fallback
            "total_messages": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting user conversation: {e}")
        return {"status": "error", "message": str(e)}


def organize_user_data(messages: List[Dict], reminders: List[Dict], birthdays: List[Dict], sessions: List[Dict]) -> Dict[str, Any]:
    """Organize user data by categories for display."""
    organized = {
        "notes": [],
        "brain_dumps": [],
        "brain_dump_sessions": [],  # Grouped brain dumps by session
        "media_files": [],
        "voice_notes": [],
        "images": [],
        "documents": [],
        "reminders": reminders,
        "birthdays": birthdays,
        "sessions": sessions,
        "tags": set()
    }
    
    # Group brain dump messages by session_id for notes tab
    brain_dump_sessions = {}
    
    for msg in messages:
        msg_type = msg.get("type", "note")
        msg_tags = msg.get("tags", [])
        
        # Skip bot responses and commands for all tabs except timeline
        is_bot_response = "bot-response" in msg_tags if msg_tags else False
        is_command = msg_type == "command"
        
        # Collect all tags (including from bot responses and commands)
        if msg_tags:
            organized["tags"].update(msg_tags)
        
        # Categorize messages (skip bot responses and commands for notes/brain_dumps)
        if not is_bot_response and not is_command:
            if msg_type == "brain_dump":
                organized["brain_dumps"].append(msg)
                
                # Group brain dump messages by session_id
                session_id = msg.get("session_id")
                if session_id:
                    if session_id not in brain_dump_sessions:
                        brain_dump_sessions[session_id] = {
                            "session_id": session_id,
                            "messages": [],
                            "tags": set(),
                            "start_time": None,
                            "end_time": None
                        }
                    
                    brain_dump_sessions[session_id]["messages"].append(msg)
                    if msg_tags:
                        brain_dump_sessions[session_id]["tags"].update(msg_tags)
                    
                    # Track earliest and latest timestamps
                    timestamp = msg.get("message_timestamp")
                    if timestamp:
                        if not brain_dump_sessions[session_id]["start_time"] or timestamp < brain_dump_sessions[session_id]["start_time"]:
                            brain_dump_sessions[session_id]["start_time"] = timestamp
                        if not brain_dump_sessions[session_id]["end_time"] or timestamp > brain_dump_sessions[session_id]["end_time"]:
                            brain_dump_sessions[session_id]["end_time"] = timestamp
                else:
                    # Brain dump without session_id - add as individual note
                    organized["notes"].append(msg)
            else:
                organized["notes"].append(msg)
        
        # Categorize by media type (skip bot responses and commands for media tabs)
        if not is_bot_response and not is_command and msg.get("file_info"):
            file_info = msg["file_info"]
            file_data = {**msg, "file_info": file_info}
            file_type = file_info.get("file_type", "")
            
            if file_type == "audio":
                organized["voice_notes"].append(file_data)
            elif file_type == "image":
                organized["images"].append(file_data)
            elif file_type == "document":
                organized["documents"].append(file_data)
            
            organized["media_files"].append(file_data)
    
    # Convert brain dump sessions dict to list and sort by start time
    for session_id, session_data in brain_dump_sessions.items():
        session_data["tags"] = sorted(list(session_data["tags"]))
        # Create consolidated content for display
        session_data["consolidated_content"] = "\n\n".join([
            msg.get("content", "") for msg in session_data["messages"]
        ])
        organized["brain_dump_sessions"].append(session_data)
    
    # Sort brain dump sessions by start time (newest first)
    organized["brain_dump_sessions"].sort(
        key=lambda x: x.get("start_time", ""),
        reverse=True
    )
    
    # Convert tags set to sorted list
    organized["tags"] = sorted(list(organized["tags"]))
    
    return organized


def calculate_user_stats(messages: List[Dict], reminders: List[Dict], birthdays: List[Dict], sessions: List[Dict]) -> Dict[str, Any]:
    """Calculate summary statistics for user."""
    stats = {
        "total_messages": len(messages),
        "total_reminders": len(reminders),
        "total_birthdays": len(birthdays),
        "total_sessions": len(sessions),
        "active_reminders": len([r for r in reminders if r.get("is_active", False)]),
        "completed_reminders": len([r for r in reminders if r.get("completed_at")]),
        "media_files": len([m for m in messages if m.get("files")]),
        "unique_tags": len(set(tag for msg in messages if msg.get("tags") for tag in msg["tags"]))
    }
    
    return stats
