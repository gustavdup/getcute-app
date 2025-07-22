# GetCute WhatsApp Bot 🤖💚

A comprehensive, ADHD-friendly WhatsApp bot for effortless brain-dumping, note-taking, and personal knowledge management with AI-powered organization.

## 🎯 Project Overview

**GetCute** is an intelligent WhatsApp bot designed to be your personal AI assistant for capturing and organizing thoughts, reminders, and memories. Built specifically with ADHD users in mind, it eliminates friction in note-taking and provides smart organization through AI classification and tagging.

### Key Features
- 🧠 **Brain Dump Sessions**: Capture multiple thoughts in sequence without friction
- 🤖 **AI Classification**: Automatic categorization of notes, reminders, and birthdays
- 🎯 **Smart Tagging**: AI-suggested tags with manual override capability
- 🔍 **Vector Search**: Semantic search through your entire knowledge base
- 🔊 **Voice Support**: Automatic transcription of voice notes using OpenAI Whisper
- 📸 **Media Handling**: Support for images, documents, and voice messages
- ⏰ **Natural Language Reminders**: Set reminders with human-like expressions
- 🎂 **Birthday Tracking**: Never forget important dates with smart notifications
- 🌐 **Web Portal**: Access your data through a clean, responsive web interface
- 📊 **Admin Dashboard**: Monitor, debug, and analyze bot interactions
- 💬 **Chat-Style UI**: WhatsApp-style chat interface for reviewing conversations
- 🔄 **Auto Token Management**: Automatic WhatsApp token renewal and health monitoring

## 🧱 Tech Stack

### Core Backend
- **Python 3.10+** with FastAPI framework for high-performance API
- **Uvicorn** ASGI server for async request handling
- **Pydantic** for data validation and settings management

### AI & Machine Learning
- **OpenAI GPT-4** for message classification, parsing, and generation
- **OpenAI Whisper** for voice transcription and audio processing
- **Vector embeddings** (1536-dimensional) for semantic search capabilities
- **Natural language processing** for time/date parsing and intent recognition

### Database & Storage
- **Supabase** (PostgreSQL) with advanced features:
  - **pgvector extension** for vector similarity search
  - **Row-level security (RLS)** for data isolation
  - **Real-time subscriptions** for instant updates
  - **Built-in authentication** and user management
- **Supabase Storage** with user-specific file organization
- **Automated backups** and point-in-time recovery

### WhatsApp Integration
- **WhatsApp Business API** for reliable messaging
- **Cloudflare Tunnel** for secure webhook exposure
- **Token management system** with automatic renewal
- **Webhook verification** for security

### Frontend & UI
- **Jinja2** templating for server-side rendering
- **Modern CSS Grid/Flexbox** for responsive layouts
- **Vanilla JavaScript** for interactive features
- **WhatsApp-style UI** components for familiar experience

## 📁 Comprehensive Project Structure

```
getcute-app/
├── 📁 src/                          # Main source code
│   ├── 🐍 main.py                   # FastAPI application entry point with all routes
│   │
│   ├── 📁 handlers/                 # Message processing pipeline
│   │   ├── 🐍 message_router.py     # Central message routing and workflow coordination
│   │   ├── 🐍 slash_commands.py     # Command handlers (/help, /portal, /search, etc.)
│   │   └── 🐍 webhook_handler.py    # WhatsApp webhook endpoints and validation
│   │
│   ├── 📁 ai/                       # AI and ML components
│   │   ├── 🐍 message_classifier.py # GPT-4 powered message classification
│   │   ├── 🐍 reminder_parser.py    # Natural language time/date parsing
│   │   ├── 🐍 birthday_parser.py    # Birthday extraction from conversational text
│   │   └── 🐍 embeddings.py         # OpenAI vector embedding generation
│   │
│   ├── 📁 services/                 # External service integrations
│   │   ├── 🐍 whatsapp_service.py   # WhatsApp Business API wrapper with token management
│   │   ├── 🐍 whatsapp_token_manager.py # Automatic token renewal and health monitoring
│   │   ├── 🐍 supabase_service.py   # Database operations with admin/user clients
│   │   ├── 🐍 storage_service.py    # File upload/download with user organization
│   │   └── 🐍 openai_service.py     # OpenAI API integration and error handling
│   │
│   ├── 📁 models/                   # Data models and schemas
│   │   ├── 🐍 message_types.py      # WhatsApp message type definitions and validation
│   │   └── 🐍 database_models.py    # Pydantic models for API validation
│   │
│   ├── 📁 workflows/                # Business logic workflows
│   │   ├── 🐍 brain_dump.py         # Multi-message brain dumping session management
│   │   ├── 🐍 tagging.py            # AI tag suggestion and user tagging workflows
│   │   ├── 🐍 search.py             # Vector similarity and full-text search
│   │   └── 🐍 reminders.py          # Reminder processing and scheduling
│   │
│   └── 📁 utils/                    # Utility functions
│       ├── 🐍 helpers.py            # Common helper functions and utilities
│       ├── 🐍 validators.py         # Input validation and sanitization
│       └── 🐍 logger.py             # Centralized logging configuration
│
├── 📁 admin/                        # Admin dashboard and monitoring
│   ├── 🐍 admin_panel.py            # Main admin API endpoints and dashboard
│   ├── � user_admin.py             # User-specific admin views and detailed analytics
│   └── 📁 templates/                # Admin UI templates
│       ├── 🎨 dashboard.html        # Main admin overview with real-time stats
│       ├── 🎨 users.html            # User management and selection interface
│       ├── 🎨 user_detail.html      # Detailed user view with chat-style UI
│       └── 🎨 user_selection.html   # User selection with search and filtering
│
├── 📁 portal/                       # User web interface (future feature)
│   └── � templates/                # User-facing web templates
│
├── 📁 logs/                         # Application logging
├── 📁 uploads/                      # User file uploads and media
├── 📁 temp_uploads/                 # Temporary processing files
│
├── 🔧 run_server.py                 # Production server launcher with tunnel management
├── 🔧 start_bot.py                  # Unified bot and tunnel startup script
├── � simple_server.py              # Minimal server for testing webhooks
├── � test_webhook.py               # Webhook connectivity testing utilities
├── � setup.py                      # Project initialization and dependency setup
│
├── � database_schema.sql           # Initial database structure
├── 📊 setup_supabase.sql            # Complete Supabase setup with pgvector
├── � update_messages_table.sql     # Bot response tracking enhancements
├── 📊 additional_analytics.sql      # Advanced analytics functions
│
├── ⚙️ config.yml.example            # Cloudflare tunnel configuration
├── ⚙️ .env.example                  # Environment variables template
├── � requirements.txt              # Python dependencies
├── 📋 .gitignore                    # Git ignore rules
├── � DEVELOPMENT.md                # Development setup and guidelines
├── � TOKEN_EXPIRATION_GUIDE.md     # WhatsApp token management guide
├── 📖 DATABASE_STATUS.md            # Database setup and status information
└── � README.md                     # This comprehensive guide
```

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** installed and accessible via command line
- **Supabase account** with a new project created
- **OpenAI API account** with GPT-4 access
- **WhatsApp Business API** access (Meta for Developers)
- **Git** for version control
- **Windows/macOS/Linux** compatible

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/gustavdup/getcute-app.git
cd getcute-app

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

```bash
# Initialize Supabase (run these in your Supabase SQL editor)
psql -h your-supabase-host -p 5432 -U postgres -d postgres -f setup_supabase.sql

# Or copy and paste the contents of setup_supabase.sql into Supabase SQL editor
```

### 3. Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
```

Required environment variables:
```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# AI Services
OPENAI_API_KEY=sk-your-openai-key

# WhatsApp
WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WEBHOOK_VERIFY_TOKEN=your-custom-verify-token

# Optional: For automatic token renewal
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret

# Environment
ENVIRONMENT=development
```

### 4. Quick Launch

```bash
# For development (includes tunnel setup)
python start_bot.py

# For production
python run_server.py
```

### 5. WhatsApp Webhook Setup

1. **Get your public URL** (displayed when starting the bot)
2. **Configure WhatsApp webhook**:
   - URL: `https://your-tunnel-url.trycloudflare.com/webhook`
   - Verify Token: (from your .env file)
   - Subscribe to: `messages` field

### 6. Verify Setup

- **Health Check**: `http://localhost:8000/health`
- **Admin Dashboard**: `http://localhost:8000/admin`
- **Test Webhook**: Use `test_webhook.py` script

## 💬 Usage Examples

### Basic Interaction
```
User: "Remind me to call mom tomorrow at 3pm"
Bot: 🤖 I'll remind you to call mom tomorrow at 3:00 PM

User: "John's birthday is March 15th"  
Bot: 🤖 I've saved John's birthday on March 15th

User: "I need to buy groceries, pick up dry cleaning, and book dentist appointment"
Bot: 🤖 I've saved your note with 3 tasks. Would you like me to set reminders for any of these?
```

### Voice Messages
- Send voice notes → Automatic transcription → AI classification
- Supports multiple languages
- Voice notes stored with transcription for searchability

### Brain Dump Sessions
```
User: "Starting a brain dump"
Bot: 🤖 Brain dump mode activated! Send me all your thoughts.

User: "Project deadline next Friday"
User: "Need to update portfolio website"  
User: "Call insurance about claim"
User: "Done"

Bot: 🤖 Captured 3 items in your brain dump! Would you like me to suggest tags or set reminders?
```

## 🔧 Core Features Deep Dive

### AI-Powered Classification
- **Automatic Detection**: Notes, reminders, birthdays, questions
- **Context Understanding**: Handles conversational, fragmented input
- **Multi-language Support**: Processes content in multiple languages
- **Confidence Scoring**: Provides classification confidence levels

### Smart Tagging System
- **AI Suggestions**: GPT-4 generates relevant tags based on content
- **User Override**: Easy tag customization and management
- **Hierarchical Tags**: Support for nested tag structures
- **Tag Analytics**: Popular tags and usage patterns

### Vector Search Capabilities
- **Semantic Similarity**: Find related content even with different wording
- **Hybrid Search**: Combines vector similarity with keyword matching
- **Context-Aware**: Considers conversation context in search results
- **Fast Retrieval**: Optimized for real-time search responses

### Advanced Reminder System
- **Natural Language**: "Tomorrow at 3", "next Friday", "in 2 hours"
- **Recurring Reminders**: Daily, weekly, monthly patterns
- **Smart Notifications**: WhatsApp message delivery
- **Timezone Support**: Handles user timezone preferences

## 📊 Admin Dashboard Features

### Real-Time Monitoring
- **Live User Activity**: See active conversations and interactions
- **Message Flow**: Track message processing and AI classification
- **System Health**: Monitor API status, token health, database performance
- **Error Tracking**: Real-time error logging and debugging

### User Management
- **User Profiles**: Detailed user activity and preferences
- **Conversation History**: Chat-style UI for reviewing interactions
- **Analytics Dashboard**: Usage patterns, popular features, engagement metrics
- **Content Management**: Moderate and manage user data

### Search and Analytics
- **Global Search**: Search across all users and conversations
- **Usage Analytics**: Feature adoption, AI accuracy, user satisfaction
- **Performance Metrics**: Response times, success rates, error rates
- **Export Capabilities**: Data export for analysis and backup

## 🛡️ Security & Privacy

### Data Protection
- **Row-Level Security**: Supabase RLS ensures data isolation
- **Encrypted Storage**: All files encrypted at rest and in transit
- **User Consent**: Clear privacy policy and consent management
- **Data Retention**: Configurable data retention policies

### Authentication & Authorization
- **Multi-Factor Authentication**: Optional MFA for admin access
- **Session Management**: Secure session handling and timeout
- **API Key Security**: Secure API key storage and rotation
- **Audit Logging**: Complete audit trail for all actions

### Compliance
- **GDPR Ready**: Right to deletion, data portability, consent management
- **Data Minimization**: Only collect necessary data
- **Transparent Processing**: Clear communication about data usage
- **User Control**: Users control their data and can export/delete anytime
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

## 🧪 Testing & Development

### Run Tests
```bash
# Test environment setup
python src/test_setup.py

# Test webhook connectivity
python test_webhook.py

# Health check
curl http://localhost:8000/health
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG  # Linux/Mac
set LOG_LEVEL=DEBUG     # Windows

# Start with verbose output
python run_server.py --debug
```

## 🔄 Continuous Integration

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install
```

### Code Quality
- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **MyPy**: Type checking
- **Pytest**: Unit and integration testing

## 🐛 Troubleshooting

### Common Issues

#### WhatsApp Token Expired
```bash
# Check token status
curl http://localhost:8000/admin/token-status

# Follow the TOKEN_EXPIRATION_GUIDE.md for detailed steps
```

#### Database Connection Issues
```bash
# Test Supabase connection
python -c "from src.services.supabase_service import SupabaseService; SupabaseService().health_check()"

# Check environment variables
python src/test_setup.py
```

#### OpenAI API Issues
```bash
# Verify API key and quota
python -c "import openai; print(openai.Model.list())"

# Check rate limits and billing
```

#### Cloudflare Tunnel Issues
```bash
# Test tunnel connectivity
curl https://your-tunnel-url.trycloudflare.com/health

# Restart tunnel
python start_bot.py --restart-tunnel
```

### Getting Help
- **Check logs**: `tail -f logs/app.log`
- **Review documentation**: `DEVELOPMENT.md`
- **GitHub Issues**: Create detailed bug reports
- **Admin Dashboard**: Monitor system health at `/admin`

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `pip install -r requirements.txt`
4. Set up pre-commit hooks: `pre-commit install`
5. Make your changes
6. Run tests: `python -m pytest`
7. Commit changes: `git commit -m 'Add amazing feature'`
8. Push to branch: `git push origin feature/amazing-feature`
9. Create Pull Request

### Code Style Guidelines
- **Python**: Follow PEP 8, use Black for formatting
- **Documentation**: Comprehensive docstrings for all functions
- **Type Hints**: Use type annotations throughout
- **Error Handling**: Comprehensive exception handling
- **Logging**: Use structured logging with appropriate levels

### Feature Development
- **Start with an Issue**: Describe the feature and get feedback
- **Write Tests First**: Test-driven development preferred
- **Small PRs**: Keep pull requests focused and small
- **Documentation**: Update README and docs as needed
- **Breaking Changes**: Discuss major changes in issues first

## 📈 Roadmap

### Upcoming Features
- **🔔 Push Notifications**: Browser notifications for reminders
- **📅 Calendar Integration**: Google Calendar sync
- **🎨 Custom Themes**: User interface personalization  
- **📊 Advanced Analytics**: Detailed usage insights
- **🔗 API Access**: Public API for third-party integrations
- **📱 Mobile App**: React Native companion app
- **🤝 Team Features**: Shared notes and collaborative brain dumps
- **🌍 Multi-language**: Full internationalization support

### Planned Improvements
- **Performance**: Database query optimization
- **Security**: Enhanced encryption and security features
- **Scalability**: Redis caching and load balancing
- **AI**: More sophisticated NLP and context understanding

## 📞 Support & Community

### Documentation
- **README.md**: This comprehensive guide
- **DEVELOPMENT.md**: Development setup and guidelines
- **TOKEN_EXPIRATION_GUIDE.md**: WhatsApp token management
- **DATABASE_STATUS.md**: Database setup and configuration
- **API Documentation**: Interactive docs at `/docs`

### Getting Help
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community Q&A and feature discussions
- **Admin Dashboard**: System monitoring and debugging
- **Health Endpoints**: System status and diagnostics

### License
MIT License - see LICENSE file for details

### Acknowledgments
- **OpenAI**: For GPT-4 and Whisper API
- **Supabase**: For database and authentication services
- **WhatsApp Business API**: For reliable messaging infrastructure
- **FastAPI**: For the high-performance web framework
- **Contributors**: All the amazing people who make this project better

---

**Built with ❤️ for ADHD brains and anyone who needs frictionless note-taking.**

*GetCute WhatsApp Bot - Your AI-powered personal knowledge companion*
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
