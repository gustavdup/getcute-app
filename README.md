# Cute WhatsApp Bot 🤖💚

A no-friction WhatsApp bot designed for brain-dumping and managing notes, reminders, and birthdays with AI assistance.

## 🎯 Project Goal

Create an intuitive WhatsApp bot for users (especially ADHD audience) to easily:
- Save notes (text, image, voice)
- Set reminders with natural language
- Track birthdays
- Organize content with tags
- Search through their personal knowledge base

## 🧱 Tech Stack

- **Backend**: Python (FastAPI)
- **Database**: Supabase (PostgreSQL with pgvector)
- **Auth**: Supabase Auth with SSO
- **Storage**: Supabase Storage
- **AI/NLP**: OpenAI GPT for message classification
- **TTS/STT**: Whisper API for voice transcription
- **Bot Platform**: WhatsApp Business API
- **Frontend**: Simple HTML/CSS/JavaScript portal

## 📁 Project Structure

```
getcute-app/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Environment variables and config
│   │   └── database.py         # Supabase connection setup
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── message_router.py   # Routes incoming messages
│   │   ├── slash_commands.py   # Handles /portal, /help, /tags etc
│   │   └── webhook_handler.py  # WhatsApp webhook processing
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── message_classifier.py  # AI classification of messages
│   │   ├── reminder_parser.py     # Parse reminder from natural language
│   │   ├── birthday_parser.py     # Parse birthday information
│   │   └── embeddings.py          # Vector embeddings for search
│   ├── services/
│   │   ├── __init__.py
│   │   ├── whatsapp_service.py    # WhatsApp API integration
│   │   ├── supabase_service.py    # Database operations
│   │   ├── auth_service.py        # SSO and authentication
│   │   ├── media_service.py       # Handle images, voice notes
│   │   └── reminder_service.py    # Scheduled reminders
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── brain_dump.py          # Brain dump session management
│   │   ├── tagging.py             # Tag management and suggestions
│   │   └── search.py              # Search functionality
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # Database schema models
│   │   └── message_types.py       # Message and response types
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py             # Common utility functions
│       └── validators.py          # Input validation
├── admin/
│   ├── __init__.py
│   ├── admin_panel.py             # Debug admin interface
│   └── templates/
│       └── admin.html             # Admin panel HTML
├── portal/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── index.html
│       ├── search.html
│       └── dashboard.html
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔤 Core Features

### Slash Commands
- `/portal` - Get authenticated dashboard link
- `/help` - Interactive help menu
- `/tags` - Manage and view tags
- `/notes` - View and filter notes
- `/reminders` - Manage reminders
- `/birthdays` - Birthday management
- `/search` - Search with text/image/voice

### AI-Powered Message Classification
- Automatically categorizes messages as notes, reminders, or birthdays
- Natural language processing for time/date extraction
- Smart tagging suggestions

### Brain Dump Sessions
- Start with `#tag1 #tag2` to begin focused note-taking
- All subsequent messages tagged automatically
- Session timeout and management

### Media Support
- Voice note transcription
- Image caption generation
- Vector search across all content types

## 🚀 Getting Started

1. **Clone and Setup**
   ```bash
   cd getcute-app
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Fill in your API keys and database credentials
   ```

3. **Database Setup**
   - Create Supabase project
   - Enable pgvector extension
   - Run database migrations

4. **Run Development Server**
   ```bash
   python src/main.py
   ```

5. **Admin Panel**
   - Access at `http://localhost:8000/admin`
   - Debug conversations and AI classifications

## 🗃️ Database Schema

### Core Tables
- `users` - User profiles and settings
- `messages` - All messages with vector embeddings
- `reminders` - Scheduled reminders
- `birthdays` - Birthday tracking
- `sessions` - Brain dump sessions

## 🔐 Authentication Flow

1. User sends `/portal` command
2. System generates SSO token
3. WhatsApp sends authenticated link
4. User accesses portal pre-logged in

## 🧪 Development Notes

- Modular architecture for easy maintenance
- Comprehensive error handling and logging
- Vector search with pgvector for semantic search
- AI classification with fallback rules
- Mobile-first responsive design for portal

## 📝 Contributing

1. Follow the established module structure
2. Add comprehensive docstrings
3. Include error handling for all external API calls
4. Test with various message formats and edge cases

## 🔮 Future Roadmap

- Multi-platform support (Telegram, Signal)
- Subscription management
- Enhanced AI features
- Mobile app companion
- Team collaboration features
