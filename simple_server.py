"""
Minimal WhatsApp Bot Server for Initial Setup
"""
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Cute WhatsApp Bot - Setup Mode")

@app.get("/")
async def root():
    return {
        "message": "Cute WhatsApp Bot is running! 🤖💚",
        "version": "1.0.0",
        "status": "setup_mode"
    }

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Verify the webhook with WhatsApp."""
    verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "cute_bot_verify_2025_secure_token_xyz789")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        print(f"✅ Webhook verified successfully!")
        print(f"Challenge: {hub_challenge}")
        return PlainTextResponse(hub_challenge)
    else:
        print(f"❌ Webhook verification failed!")
        print(f"Expected token: {verify_token}")
        print(f"Received token: {hub_verify_token}")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive WhatsApp messages."""
    body = await request.json()
    print(f"📨 Received webhook: {body}")
    
    # Extract message data
    try:
        entry = body.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        if messages:
            message = messages[0]
            from_number = message.get('from')
            message_text = message.get('text', {}).get('body', '')
            message_type = message.get('type')
            
            print(f"🔍 Message details:")
            print(f"   From: {from_number}")
            print(f"   Type: {message_type}")
            print(f"   Text: {message_text}")
            
            # Send a response back
            if message_type == 'text' and message_text:
                await send_whatsapp_reply(from_number, f"Hey! I received your message: '{message_text}' 🤖💚\n\nI'm your ADHD-friendly brain dump bot! Try sending me your thoughts, and I'll help organize them.")
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
    
    return {"status": "ok", "message": "Webhook received"}

async def send_whatsapp_reply(to_number: str, message: str):
    """Send a reply message via WhatsApp Business API."""
    import httpx
    
    url = f"https://graph.facebook.com/v21.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"✅ Reply sent successfully to {to_number}")
            else:
                print(f"❌ Failed to send reply: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending reply: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "setup"}

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "localhost")
    
    print("🤖 Starting Cute WhatsApp Bot (Setup Mode)...")
    print(f"📡 Server: http://{host}:{port}")
    print(f"🔗 Webhook URL: http://{host}:{port}/webhook")
    print(f"🔑 Verify Token: {os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'cute_bot_verify_2025_secure_token_xyz789')}")
    print("=" * 50)
    
    uvicorn.run(app, host=host, port=port, reload=False)
