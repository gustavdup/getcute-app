"""
WhatsApp webhook handler for processing incoming messages.
"""
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

from models.message_types import WhatsAppWebhook, ProcessedMessage
from services.whatsapp_service import WhatsAppService
from services.supabase_service import SupabaseService
from handlers.message_router import MessageRouter

logger = logging.getLogger(__name__)

webhook_router = APIRouter()

# Initialize services with database connection
db_service = SupabaseService()
whatsapp_service = WhatsAppService(db_service)
message_router = MessageRouter(whatsapp_service)

# Message deduplication cache (in production, use Redis or database)
processed_message_ids = set()
MAX_CACHE_SIZE = 1000  # Prevent memory issues


@webhook_router.get("/")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Verify WhatsApp webhook during setup."""
    try:
        if hub_mode == "subscribe":
            challenge = whatsapp_service.verify_webhook(hub_verify_token, hub_challenge)
            if challenge:
                logger.info("Webhook verified successfully")
                return PlainTextResponse(challenge)
            else:
                logger.error("Webhook verification failed")
                raise HTTPException(status_code=403, detail="Verification failed")
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@webhook_router.post("/")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages."""
    try:
        body = await request.body()
        webhook_data = json.loads(body)
        
        # Parse webhook payload
        webhook = WhatsAppWebhook(**webhook_data)
        
        # Process each entry
        for entry in webhook.entry:
            for change in entry.changes:
                if change.field == "messages":
                    await process_messages(change.value)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Return 200 to prevent WhatsApp from retrying
        return {"status": "error", "message": str(e)}


async def process_messages(value: Dict[str, Any]):
    """Process incoming messages from webhook value."""
    try:
        messages = value.get("messages", [])
        contacts = value.get("contacts", [])
        
        # Create contact lookup
        contact_lookup = {contact["wa_id"]: contact for contact in contacts}
        
        for message_data in messages:
            # Extract message information
            user_phone = message_data.get("from")
            message_id = message_data.get("id")
            timestamp_str = message_data.get("timestamp")
            message_type = message_data.get("type", "text")
            
            if not user_phone or not message_id:
                logger.warning("Missing required message fields")
                continue
            
            # Check for duplicate message processing
            if message_id in processed_message_ids:
                logger.info(f"Skipping duplicate message: {message_id}")
                continue
            
            # Add to processed cache (with size limit)
            processed_message_ids.add(message_id)
            if len(processed_message_ids) > MAX_CACHE_SIZE:
                # Remove oldest entries (simplified - in production use LRU cache)
                processed_message_ids.pop()
            
            # Convert timestamp
            try:
                # WhatsApp timestamps are in UTC, so use utcfromtimestamp
                timestamp = datetime.utcfromtimestamp(int(timestamp_str))
            except (ValueError, TypeError):
                timestamp = datetime.now(timezone.utc)
            
            # Extract content based on message type
            content = ""
            media_url = None
            media_id = None
            
            if message_type == "text":
                content = message_data.get("text", {}).get("body", "")
            elif message_type == "image":
                image_data = message_data.get("image", {})
                content = image_data.get("caption", "[Image]")
                media_id = image_data.get("id")
            elif message_type == "audio" or message_type == "voice":
                audio_data = message_data.get(message_type, {})
                content = "[Audio message]"
                media_id = audio_data.get("id")
            elif message_type == "document":
                doc_data = message_data.get("document", {})
                content = f"[Document: {doc_data.get('filename', 'Unknown')}]"
                media_id = doc_data.get("id")
            else:
                content = f"[{message_type.title()} message]"
            
            # Create processed message
            processed_message = ProcessedMessage(
                user_phone=user_phone,
                message_id=message_id,
                timestamp=timestamp,
                content=content,
                message_type=message_type,
                media_url=media_url,
                media_id=media_id
            )
            
            # Route message for processing
            await message_router.route_message(processed_message)
            
    except Exception as e:
        logger.error(f"Error processing messages: {e}")


@webhook_router.post("/test")
async def test_webhook():
    """Test endpoint for development."""
    # Use a simple global variable instead of function attribute
    global _test_called
    if '_test_called' not in globals():
        globals()['_test_called'] = True
        
        # Send a test message
        test_message = ProcessedMessage(
            user_phone="+1234567890",
            message_id="test_123",
            timestamp=datetime.now(timezone.utc),
            content="Hello, this is a test message!",
            message_type="text"
        )
        
        await message_router.route_message(test_message)
        
        return {"status": "test message sent"}
    else:
        return {"status": "test already called"}
