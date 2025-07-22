# Cute WhatsApp Bot 🤖💚

A comprehensive, ADHD-friendly WhatsApp bot for effortless brain-dumping, note-taking, and personal knowledge management with AI-powered organization.

## 🎯 Project Overview

**Cute** is an intelligent WhatsApp bot designed to be your personal AI assistant for capturing and organizing thoughts, reminders, and memories. Built specifically with ADHD users in mind, it eliminates friction in note-taking and provides smart organization through AI classification and tagging.

### Key Features
- 🧠 **Brain Dump Sessions**: Capture multiple thoughts in sequence
- 🤖 **AI Classification**: Automatic categorization of notes, reminders, and birthdays
- 🎯 **Smart Tagging**: AI-suggested tags with manual override
- 🔍 **Vector Search**: Semantic search through your knowledge base
- 🔊 **Voice Support**: Automatic transcription of voice notes
- 📸 **Media Handling**: Support for images, documents, and voice messages
- ⏰ **Natural Language Reminders**: Set reminders with human-like expressions
- 🎂 **Birthday Tracking**: Never forget important dates
- 🌐 **Web Portal**: Access your data through a clean web interface
- 📊 **Admin Dashboard**: Monitor and debug bot interactions

## 🧱 Tech Stack

### Backend
- **Python 3.10+** with FastAPI framework
- **Supabase** (PostgreSQL + pgvector for embeddings)
- **OpenAI GPT-4** for message classification and parsing
- **WhatsApp Business API** for messaging
- **Uvicorn** ASGI server

### AI & ML
- **OpenAI API** for text classification and generation
- **Whisper API** for voice transcription
- **Vector embeddings** (1536-dimensional) for semantic search
- **Natural language processing** for time and date parsing

### Storage & Database
- **PostgreSQL** with vector search capabilities
- **Supabase Storage** with user-specific folders
- **Row-level security** for data isolation
- **Real-time subscriptions** for instant updates

### Frontend
- **Jinja2** templating for server-side rendering
- **Vanilla JavaScript** for interactive features
- **Responsive CSS** for mobile-first design

## 📁 Comprehensive Project Structure

```
getcute-app/
├── 📁 src/                          # Main source code
│   ├── 🐍 main.py                   # FastAPI application entry point
│   ├── 🐍 test_setup.py             # Environment validation tests
│   │
│   ├── 📁 config/                   # Configuration management
│   │   ├── 🐍 settings.py           # Pydantic settings with validation
│   │   └── 🐍 database.py           # Supabase client setup
│   │
│   ├── 📁 handlers/                 # Message processing
│   │   ├── 🐍 message_router.py     # Central message routing logic
│   │   ├── 🐍 slash_commands.py     # Command handlers (/help, /portal, etc.)
│   │   └── 🐍 webhook_handler.py    # WhatsApp webhook endpoints
│   │
│   ├── 📁 ai/                       # AI and ML components
│   │   ├── 🐍 message_classifier.py # GPT-powered message classification
│   │   ├── 🐍 reminder_parser.py    # Natural language time parsing
│   │   ├── 🐍 birthday_parser.py    # Birthday extraction from text
│   │   └── 🐍 embeddings.py         # Vector embedding generation
│   │
│   ├── 📁 services/                 # External service integrations
│   │   ├── 🐍 whatsapp_service.py   # WhatsApp Business API wrapper
│   │   ├── 🐍 supabase_service.py   # Database operations and queries
│   │   ├── 🐍 storage_service.py    # File upload/download management
│   │   └── 🐍 auth_service.py       # Authentication and SSO
│   │
│   ├── 📁 models/                   # Data models and schemas
│   │   ├── 🐍 database.py           # SQLAlchemy/Pydantic models
│   │   └── 🐍 message_types.py      # WhatsApp message type definitions
│   │
│   ├── 📁 workflows/                # Business logic workflows
│   │   ├── 🐍 brain_dump.py         # Brain dumping session management
│   │   ├── 🐍 tagging.py            # Tag suggestion and management
│   │   └── 🐍 search.py             # Vector and text search
│   │
│   └── 📁 utils/                    # Utility functions
│       ├── 🐍 helpers.py            # Common helper functions
│       └── 🐍 validators.py         # Input validation utilities
│
├── 📁 portal/                       # Web interface
│   ├── 🌐 main.py                   # Portal Flask/FastAPI app
│   └── 📁 templates/                # Jinja2 templates
│       ├── 🎨 base.html             # Base template
│       ├── 🎨 login.html            # Authentication page
│       ├── 🎨 dashboard.html        # Main user dashboard
│       ├── 🎨 search.html           # Search interface
│       └── 🎨 settings.html         # User preferences
│
├── 📁 admin/                        # Admin dashboard
│   ├── 🐍 admin_panel.py            # Admin API endpoints
│   └── 📁 templates/                # Admin templates
│       ├── 🎨 admin.html            # Main admin dashboard
│       ├── 🎨 users.html            # User management
│       ├── 🎨 conversations.html    # Conversation monitoring
│       └── 🎨 system.html           # System statistics
│
├── 📁 logs/                         # Application logs
├── 📁 uploads/                      # Temporary file uploads
├── 📁 temp_uploads/                 # Processing temporary files
│
├── 📄 database_schema.sql           # Complete database setup
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env.example                  # Environment variables template
├── 📄 .gitignore                    # Git ignore rules
├── 📄 setup.py                      # Project setup and initialization
├── 📄 DEVELOPMENT.md                # Development guidelines
└── 📄 README.md                     # This comprehensive guide
```
## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Supabase account and project
- OpenAI API account
- WhatsApp Business API access
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/gustavdup/getcute-app.git
cd getcute-app

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# Application Configuration
SECRET_KEY=your_secret_key_for_jwt_tokens
WEBHOOK_URL=https://your-domain.com/webhook
```

### 3. Database Setup

Run the database schema in your Supabase SQL editor:

```bash
# The database_schema.sql file contains:
# - Table creation with proper indexes
# - Row-level security policies
# - Helper functions for search and statistics
# - Sample data (optional)
```

Execute the entire `database_schema.sql` file in Supabase Dashboard → SQL Editor.

### 4. Storage Setup

Create a storage bucket in Supabase Dashboard:
1. Go to Storage → Create Bucket
2. Name: `user-media`
3. Set as **Private bucket** (for better security)
4. Configure RLS policies for authenticated access

### 5. Run the Application

```bash
# Run setup validation
python src/test_setup.py

# Start the server
python src/main.py

# Or use uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. WhatsApp Webhook Configuration

1. Set your webhook URL in WhatsApp Business API settings
2. Use the verification token from your `.env` file
3. Subscribe to `messages` events

## 🎯 Core Features & Usage

### 🧠 Brain Dump Sessions

**Start a Session:**
```
#work #ideas
I need to brainstorm some new feature ideas
```

**Continue Adding:**
```
Maybe a calendar integration
Voice commands for setting reminders
Better search filters
```

**End Session:**
```
/end
```

### 📝 Smart Note Taking

**Simple Notes:**
```
Remember to buy groceries tomorrow
```
→ AI classifies as note with #shopping tag

**With Custom Tags:**
```
#meeting #project-x Notes from today's standup
```

### ⏰ Natural Language Reminders

**Examples:**
```
Remind me to call mom tomorrow at 2pm
Set reminder for dentist appointment next Friday
Remind me about the meeting in 30 minutes
```

### 🎂 Birthday Management

**Add Birthdays:**
```
John's birthday is March 15th, 1990
```
→ AI extracts: Name=John, Date=March 15, Year=1990

### 🔍 Intelligent Search

**Text Search:**
```
/search project ideas from last week
```

**Voice Search:**
Send a voice note asking for information

**Image Search:**
Send an image with caption "find similar notes"

### 📁 Media Handling

**Voice Notes:**
- Automatic transcription with Whisper API
- Searchable transcribed content
- Organized in user-specific folders

**Images:**
- Stored in Supabase Storage
- User-isolated folders (`user_folders/{user_id}/`)
- Support for JPG, PNG, GIF, WebP

**Documents:**
- PDF, DOC, TXT support
- Automatic file type detection
- Size limits by file type

## 💻 Web Portal Features

### User Dashboard
- **Recent Activity**: Latest notes, reminders, birthdays
- **Search Interface**: Full-text and semantic search
- **Tag Management**: View and edit all tags
- **Media Gallery**: Browse uploaded images and files
- **Statistics**: Usage analytics and insights

### Admin Dashboard
- **User Management**: Monitor active users and conversations
- **System Health**: Database status, AI service monitoring
- **Error Logs**: Real-time error tracking
- **Performance Metrics**: Response times and classification accuracy

## 🔧 API Endpoints

### WhatsApp Webhook
```
GET  /webhook          # Webhook verification
POST /webhook          # Receive WhatsApp messages
```

### Portal API
```
GET  /                 # Main dashboard
GET  /login           # Authentication page
GET  /search          # Search interface
POST /api/search      # Search API
GET  /api/notes       # Notes API
GET  /api/reminders   # Reminders API
```

### Admin API
```
GET  /admin           # Admin dashboard
GET  /admin/users     # User statistics
GET  /admin/errors    # Error monitoring
GET  /admin/conversations/{user_id}  # User conversation history
```

## 🗄️ Database Schema

### Core Tables
- **users**: User profiles and preferences
- **messages**: All message content with vector embeddings
- **reminders**: Scheduled reminders with repeat patterns
- **birthdays**: Birthday tracking with notification settings
- **sessions**: Brain dump session management
- **files**: Media file metadata and storage paths

### Key Features
- **Vector Search**: 1536-dimensional embeddings for semantic search
- **Row-Level Security**: Users can only access their own data
- **Real-time Updates**: Supabase subscriptions for live data
- **Automated Cleanup**: Failed upload cleanup and data archival

## 🤖 AI Integration

### Message Classification
Uses GPT-4 to classify incoming messages:
- **Note**: General information storage
- **Reminder**: Time-based actionable items
- **Birthday**: Person and date information
- **Command**: Bot commands and queries

### Tag Suggestion
- Analyzes message content for relevant tags
- Considers user's existing tag patterns
- Suggests 3 most relevant tags per message

### Natural Language Processing
- **Time Parsing**: "tomorrow at 2pm", "next Friday", "in 30 minutes"
- **Date Extraction**: Various date formats and relative dates
- **Intent Recognition**: Search queries and command interpretation

## 📊 File Storage Architecture

### Organization Structure
```
Supabase Storage: "user-media"
├── user_folders/
│   ├── {user-uuid-1}/
│   │   ├── 1640995200_a1b2c3d4.jpg    # Images
│   │   ├── 1640995210_e5f6g7h8.ogg    # Voice notes
│   │   ├── 1640995220_i9j0k1l2.pdf    # Documents
│   │   └── .placeholder               # Folder marker
│   ├── {user-uuid-2}/
│   └── ...
```

### File Management
- **Automatic Folder Creation**: User folders created on first upload
- **Unique Filenames**: Timestamp + UUID to prevent conflicts
- **Size Limits**: Images (10MB), Audio (25MB), Documents (20MB), Video (50MB)
- **Cleanup**: Automatic removal of failed uploads after 1 hour
- **Private Storage**: Files accessed via signed URLs with expiration
- **WhatsApp Integration**: Longer-lived URLs (24h) for media sharing

## 🔐 Security & Privacy

### Data Protection
- **Row-Level Security**: Database policies ensure user data isolation
- **Private Storage**: All media files in private Supabase buckets with signed URLs
- **User Folder Isolation**: Each user has their own folder structure
- **Encrypted Communications**: HTTPS for all API communications
- **Token-Based Auth**: JWT tokens for portal authentication

### User Privacy
- **Data Ownership**: Users own all their data
- **Export Capability**: Full data export available
- **Deletion Rights**: Complete data deletion on request
- **No Cross-User Access**: Strict user isolation

## 🚀 Deployment

### Development
```bash
# Start development server
uvicorn src.main:app --reload --host localhost --port 8000

# Run with debug logging
LOG_LEVEL=DEBUG python src/main.py
```

### Production
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or use Docker (Dockerfile included)
docker build -t cute-whatsapp-bot .
docker run -p 8000:8000 cute-whatsapp-bot
```

### Environment Variables (Production)
```env
DEBUG=False
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
WEBHOOK_URL=https://your-production-domain.com/webhook
```

## 🧪 Testing

### Run Tests
```bash
# Environment validation
python src/test_setup.py

# Unit tests (when implemented)
pytest tests/

# Load testing
locust -f tests/load_test.py
```

### Manual Testing
1. Send test messages to your WhatsApp bot
2. Check the admin dashboard for real-time monitoring
3. Verify file uploads work correctly
4. Test the web portal authentication and search

## 📈 Monitoring & Analytics

### Built-in Monitoring
- **Real-time Error Tracking**: All errors logged with context
- **Performance Metrics**: Response times and classification accuracy
- **Usage Statistics**: Message counts, user activity, storage usage
- **Health Checks**: Database connectivity, AI service status

### Admin Dashboard Metrics
- Total users and daily active users
- Message classification accuracy
- Storage usage per user
- Error rates and types
- System resource utilization

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all functions
- Write docstrings for public methods
- Keep functions focused and testable

### Testing Requirements
- All new features must include tests
- Maintain test coverage above 80%
- Test both success and error cases
- Include integration tests for API endpoints

## 📚 Documentation

### Additional Resources
- **DEVELOPMENT.md**: Detailed development guidelines
- **API Documentation**: Auto-generated with FastAPI at `/docs`
- **Database Schema**: Complete schema in `database_schema.sql`
- **Environment Setup**: Detailed in `.env.example`

### Troubleshooting
Common issues and solutions:

**Database Connection Errors:**
- Verify Supabase credentials in `.env`
- Check network connectivity
- Ensure database schema is properly installed

**WhatsApp API Issues:**
- Verify webhook URL is accessible
- Check access token validity
- Ensure proper webhook verification

**AI Classification Errors:**
- Verify OpenAI API key
- Check API quota and usage
- Monitor error logs for specific issues

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Supabase** for the excellent backend-as-a-service platform
- **OpenAI** for powerful AI capabilities
- **FastAPI** for the amazing Python web framework
- **WhatsApp Business API** for messaging infrastructure
- **ADHD Community** for inspiration and feedback

## 📞 Support

### Getting Help
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the docs/ folder for detailed guides

### Contact
- **Project Maintainer**: Gustav Duplessis
- **Email**: [Your contact email]
- **GitHub**: [@gustavdup](https://github.com/gustavdup)

---

**Made with ❤️ for the ADHD community and anyone who wants frictionless note-taking** 🧠✨

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
