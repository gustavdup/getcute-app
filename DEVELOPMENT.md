# Development Guide - Cute WhatsApp Bot 🤖💚

## Quick Start

### 1. Setup Environment
```bash
# Run the setup script
python setup.py

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/Linux/macOS:
source venv/bin/activate

# Install dependencies (if not done by setup.py)
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Edit `.env` file with your credentials:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-webhook-verify-token

# Application
SECRET_KEY=your-secret-key-for-jwt
WEBHOOK_URL=https://your-domain.com/webhook
```

### 3. Database Setup
1. Create a Supabase project
2. Enable pgvector extension in Supabase
3. Run the SQL from `database_schema.sql` in Supabase SQL editor

### 4. Run the Application
```bash
python src/main.py
```

The application will be available at:
- Main API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- Portal: http://localhost:8000/portal

## Development Workflow

### Testing the Bot Locally

1. **Test Webhook Endpoint**
   ```bash
   curl -X POST http://localhost:8000/webhook/test
   ```

2. **Simulate WhatsApp Messages**
   Use the admin panel or create test scripts to simulate incoming messages.

3. **Check Logs**
   The application logs all activities. Check the console output for debugging.

## Project Structure Overview

```
src/
├── main.py                 # FastAPI app entry point
├── config/                 # Configuration and settings
├── models/                 # Database and message models
├── services/               # External API integrations
├── handlers/               # Message routing and processing
├── ai/                     # AI classification and NLP
├── workflows/              # Complex multi-step processes
└── utils/                  # Helper functions

admin/                      # Admin panel for debugging
portal/                     # User portal templates
```

## Key Components

### 1. Message Flow
```
WhatsApp → Webhook → MessageRouter → AI Classification → Appropriate Handler → Database/Response
```

### 2. AI Classification
The `MessageClassifier` uses OpenAI to categorize messages:
- **Notes**: General information to save
- **Reminders**: Time-based tasks
- **Birthdays**: Birthday information
- **Slash Commands**: Bot commands like /help
- **Brain Dump**: Session-based note taking

### 3. Brain Dump Sessions
Users can start focused note-taking sessions:
1. Send `#tag1 #tag2` to start
2. All subsequent messages get those tags
3. Session auto-expires or ends with `/end`

### 4. Tagging System
- Automatic tag extraction from `#hashtags`
- AI-powered tag suggestions
- Tag management through portal

## Adding New Features

### 1. New Slash Command
1. Add handler in `slash_commands.py`
2. Update command routing in `handle_command()`
3. Add any new database operations needed

### 2. New Message Type
1. Add to `MessageType` enum in `models/database.py`
2. Update AI classification prompt
3. Add handler logic in `message_router.py`

### 3. New Workflow
1. Create new file in `workflows/`
2. Implement workflow class with async methods
3. Integrate with message router

## Database Operations

### Common Queries
```python
# Get user
user = await db_service.get_or_create_user(phone_number)

# Save message
message = Message(user_id=user.id, content="Hello", type=MessageType.NOTE)
await db_service.save_message(message)

# Search messages
results = await db_service.search_messages_vector(user.id, embedding)
```

### Adding New Tables
1. Add model in `models/database.py`
2. Update `database_schema.sql`
3. Add service methods in `supabase_service.py`

## WhatsApp Integration

### Message Types Supported
- Text messages
- Images (with captions)
- Audio/Voice notes
- Documents
- Interactive buttons

### Sending Messages
```python
# Text message
await whatsapp_service.send_text_message(phone, "Hello!")

# Interactive menu
await whatsapp_service.send_interactive_message(
    phone, 
    "Choose an option:",
    [{"id": "opt1", "title": "Option 1"}]
)
```

## Testing

### Unit Tests
Create test files in `tests/` directory:
```python
import pytest
from src.ai.message_classifier import MessageClassifier

@pytest.mark.asyncio
async def test_classify_note():
    classifier = MessageClassifier()
    result = await classifier.classify_message("Remember to buy milk")
    assert result.message_type == "note"
```

### Integration Tests
Test the full webhook flow:
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_webhook_verification():
    response = client.get("/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your_token")
    assert response.status_code == 200
```

## Debugging

### Common Issues

1. **Import Errors**: Make sure virtual environment is activated
2. **Database Connection**: Check Supabase credentials in `.env`
3. **AI Classification**: Verify OpenAI API key
4. **WhatsApp Webhook**: Ensure webhook URL is publicly accessible

### Logging
Adjust log level in `.env`:
```env
LOG_LEVEL=DEBUG
```

### Admin Panel
Use the admin panel at `/admin` to:
- View recent conversations
- Check AI classification results
- Monitor system health
- Debug user sessions

## Deployment

### Production Checklist
- [ ] Set up production Supabase database
- [ ] Configure WhatsApp webhook with production URL
- [ ] Set environment variables securely
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies

### Environment Variables for Production
```env
DEBUG=False
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Contributing

1. Follow the established code structure
2. Add type hints to all functions
3. Include docstrings for classes and methods
4. Add error handling for external API calls
5. Write tests for new features
6. Update this guide for new components

## Future Enhancements

### Planned Features
- [ ] Voice message transcription
- [ ] Image content analysis
- [ ] Multi-language support
- [ ] Team collaboration
- [ ] Analytics dashboard
- [ ] Mobile app companion
- [ ] Telegram integration

### Architecture Improvements
- [ ] Move to Supabase Edge Functions
- [ ] Add Redis for caching
- [ ] Implement proper queue system
- [ ] Add comprehensive testing suite
- [ ] Set up CI/CD pipeline

## Support

For issues and questions:
1. Check the logs for error messages
2. Review this development guide
3. Check Supabase and OpenAI service status
4. Test with simplified inputs
5. Use the admin panel for debugging

Remember: This is a comprehensive personal productivity tool designed to be intuitive and minimal-friction for users, especially those with ADHD who benefit from quick brain-dumping capabilities.
