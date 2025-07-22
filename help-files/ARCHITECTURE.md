# GetCute WhatsApp Bot - Architecture & Flow Documentation

## 🏗️ System Architecture Overview

This document explains the detailed architecture, data flow, and interaction between all Python files in the GetCute WhatsApp Bot project.

## 🔄 Message Processing Flow

### 1. **Incoming Message Journey**

```
WhatsApp Message 
    ↓
Cloudflare Tunnel (webhook exposure)
    ↓
FastAPI App (main.py) 
    ↓
Webhook Handler (handlers/webhook_handler.py)
    ↓
Message Router (handlers/message_router.py)
    ↓
AI Classification (ai/message_classifier.py)
    ↓
Workflow Processing (workflows/*.py)
    ↓
Database Storage (services/supabase_service.py)
    ↓
WhatsApp Response (services/whatsapp_service.py)
```

### 2. **Detailed Component Flow**

#### **Entry Points → Core Processing**

1. **`main.py`** - FastAPI Application
   - Initializes FastAPI application
   - Sets up all route handlers
   - Configures CORS and middleware
   - Includes admin and webhook routers
   - Health check endpoints

2. **`run_server.py`** - Production Server Launcher
   - Loads environment configuration
   - Manages Cloudflare tunnel integration
   - Handles server startup and shutdown
   - Production-ready with error handling

3. **`start_bot.py`** - Unified Startup Script
   - Combines server and tunnel management
   - Development-friendly setup
   - Displays webhook URLs and status
   - Auto-tunnel configuration

#### **Message Processing Pipeline**

4. **`handlers/webhook_handler.py`** - WhatsApp Webhook Endpoints
   - **Purpose**: Receives and validates WhatsApp webhooks
   - **Key Functions**:
     - `verify_webhook()` - GET endpoint for WhatsApp verification
     - `handle_webhook()` - POST endpoint for incoming messages
     - `validate_signature()` - Security verification
   - **Flow**: Extracts message data → Validates signature → Routes to message_router

5. **`handlers/message_router.py`** - Central Message Routing
   - **Purpose**: Orchestrates the entire message processing workflow
   - **Key Functions**:
     - `process_whatsapp_message()` - Main entry point
     - `handle_different_message_types()` - Routes by message type (text, audio, image)
     - `coordinate_workflows()` - Manages brain dump sessions, tagging, etc.
   - **Flow**: Message validation → User management → Classification → Workflow routing → Response

6. **`handlers/slash_commands.py`** - Command Processing
   - **Purpose**: Handles special bot commands (/help, /search, /portal, etc.)
   - **Key Functions**:
     - `handle_help_command()` - User assistance
     - `handle_search_command()` - Search functionality
     - `handle_portal_command()` - Web portal access
   - **Flow**: Command detection → Parameter parsing → Feature execution → Response

#### **AI & Intelligence Layer**

7. **`ai/message_classifier.py`** - GPT-4 Message Classification
   - **Purpose**: Determines message intent and type using AI
   - **Key Functions**:
     - `classify_message()` - Main classification logic
     - `determine_intent()` - Note vs Reminder vs Birthday vs Command
     - `extract_confidence()` - Classification confidence scoring
   - **Flow**: Message content → GPT-4 API call → Intent classification → Confidence assessment

8. **`ai/reminder_parser.py`** - Natural Language Time Parsing
   - **Purpose**: Extracts dates and times from conversational text
   - **Key Functions**:
     - `parse_reminder_time()` - Converts "tomorrow at 3pm" to datetime
     - `handle_relative_dates()` - "next Friday", "in 2 hours"
     - `parse_recurring_patterns()` - "every Monday", "daily"
   - **Flow**: Text input → Time pattern recognition → DateTime conversion → Validation

9. **`ai/birthday_parser.py`** - Birthday Information Extraction
   - **Purpose**: Extracts person names and birth dates from messages
   - **Key Functions**:
     - `extract_birthday_info()` - Gets name and date
     - `parse_date_formats()` - Handles various date formats
     - `validate_birthday_data()` - Ensures data completeness
   - **Flow**: Message content → Name/date extraction → Format standardization → Validation

10. **`ai/embeddings.py`** - Vector Embedding Generation
    - **Purpose**: Creates searchable vector representations of content
    - **Key Functions**:
      - `generate_embeddings()` - OpenAI embedding API calls
      - `store_vectors()` - Save to pgvector database
      - `similarity_search()` - Find semantically similar content
    - **Flow**: Text content → OpenAI embedding → Vector storage → Search indexing

#### **Workflow Orchestration**

11. **`workflows/brain_dump.py`** - Multi-Message Session Management
    - **Purpose**: Handles continuous brain dumping sessions
    - **Key Functions**:
      - `start_brain_dump()` - Initiates session
      - `add_to_session()` - Accumulates messages
      - `end_session()` - Processes and stores complete session
    - **Flow**: Session detection → Message accumulation → Batch processing → Tag suggestion

12. **`workflows/tagging.py`** - AI Tag Suggestion & Management
    - **Purpose**: Suggests and manages tags for content organization
    - **Key Functions**:
      - `suggest_tags()` - AI-powered tag recommendations
      - `apply_user_tags()` - User-specified tag processing
      - `merge_tag_suggestions()` - Combines AI and user tags
    - **Flow**: Content analysis → AI tag generation → User preference checking → Tag application

13. **`workflows/search.py`** - Vector & Text Search
    - **Purpose**: Provides semantic and keyword search capabilities
    - **Key Functions**:
      - `vector_search()` - Semantic similarity search
      - `keyword_search()` - Full-text search
      - `hybrid_search()` - Combines both approaches
    - **Flow**: Query processing → Vector/text search → Result ranking → Response formatting

14. **`workflows/reminders.py`** - Reminder Processing & Scheduling
    - **Purpose**: Handles reminder creation, storage, and scheduling
    - **Key Functions**:
      - `create_reminder()` - Processes reminder creation
      - `schedule_notification()` - Sets up future delivery
      - `handle_recurring()` - Manages repeat patterns
    - **Flow**: Reminder parsing → Database storage → Scheduling setup → Notification queuing

#### **External Service Integration**

15. **`services/whatsapp_service.py`** - WhatsApp Business API
    - **Purpose**: All WhatsApp API interactions with token management
    - **Key Functions**:
      - `send_message()` - Text message delivery
      - `send_media()` - Image/audio/document sharing
      - `download_media()` - Retrieves user-sent media
      - `validate_webhook()` - Security verification
    - **Flow**: Message preparation → Token validation → API call → Response handling → Database logging

16. **`services/whatsapp_token_manager.py`** - Token Health Management
    - **Purpose**: Automatic token renewal and health monitoring
    - **Key Functions**:
      - `check_token_expiry()` - Monitors token health
      - `refresh_token()` - Automatic token renewal
      - `get_fresh_token()` - Ensures valid tokens for API calls
    - **Flow**: Token status check → Expiry detection → Automatic renewal → Health monitoring

17. **`services/supabase_service.py`** - Database Operations
    - **Purpose**: All database interactions with admin/user client management
    - **Key Functions**:
      - `store_message()` - Message persistence
      - `vector_search()` - Semantic search queries
      - `user_management()` - User data operations
      - `admin_queries()` - Admin dashboard data
    - **Flow**: Data validation → Client selection (admin/user) → Database operation → Error handling

18. **`services/storage_service.py`** - File Management
    - **Purpose**: Handles all file uploads, downloads, and organization
    - **Key Functions**:
      - `upload_file()` - Stores user media in organized folders
      - `download_file()` - Retrieves files with signed URLs
      - `cleanup_failed_uploads()` - Maintains storage hygiene
    - **Flow**: File validation → User folder creation → Upload to Supabase Storage → URL generation

19. **`services/openai_service.py`** - OpenAI API Integration
    - **Purpose**: Centralized OpenAI API calls with error handling
    - **Key Functions**:
      - `chat_completion()` - GPT-4 text generation
      - `create_embeddings()` - Vector embedding generation
      - `transcribe_audio()` - Whisper speech-to-text
    - **Flow**: Request preparation → API call → Response processing → Error handling

#### **Data Models & Validation**

20. **`models/message_types.py`** - WhatsApp Message Definitions
    - **Purpose**: Type definitions and validation for WhatsApp message formats
    - **Key Functions**:
      - `WhatsAppMessage` - Base message model
      - `TextMessage`, `AudioMessage`, `ImageMessage` - Specific types
      - `validate_message_format()` - Input validation
    - **Flow**: Incoming data → Type validation → Model instantiation → Processing pipeline

21. **`models/database_models.py`** - API Data Models
    - **Purpose**: Pydantic models for API request/response validation
    - **Key Functions**:
      - `UserModel`, `MessageModel`, `ReminderModel` - Data structures
      - `validate_inputs()` - Input sanitization
      - `serialize_outputs()` - Response formatting
    - **Flow**: API input → Validation → Processing → Response serialization

#### **Admin & Monitoring**

22. **`admin/admin_panel.py`** - Main Admin Dashboard
    - **Purpose**: Core admin functionality and system monitoring
    - **Key Functions**:
      - `dashboard_stats()` - System overview and metrics
      - `user_management()` - User administration
      - `conversation_monitoring()` - Real-time conversation tracking
      - `token_health()` - WhatsApp token status and refresh
    - **Flow**: Admin request → Authentication → Data aggregation → Dashboard rendering

23. **`admin/user_admin.py`** - Detailed User Management
    - **Purpose**: Individual user analysis and detailed conversation views
    - **Key Functions**:
      - `user_detail_view()` - Comprehensive user profiles
      - `conversation_history()` - Chat-style conversation display
      - `user_analytics()` - Usage patterns and statistics
    - **Flow**: User selection → Data retrieval → Timeline construction → Detailed analytics

#### **Utilities & Helpers**

24. **`utils/helpers.py`** - Common Utilities
    - **Purpose**: Shared helper functions used across the application
    - **Key Functions**:
      - `format_datetime()` - Consistent date/time formatting
      - `sanitize_input()` - Input cleaning and validation
      - `generate_uuid()` - Unique identifier generation
    - **Flow**: Called by various components → Processing → Return standardized results

25. **`utils/validators.py`** - Input Validation
    - **Purpose**: Comprehensive input validation and sanitization
    - **Key Functions**:
      - `validate_phone_number()` - Phone number format validation
      - `sanitize_message_content()` - Content cleaning
      - `validate_file_type()` - Media file validation
    - **Flow**: Input received → Validation rules applied → Sanitized output → Processing continues

## 🔀 Data Flow Patterns

### **Pattern 1: Simple Message Processing**
```
User sends "Buy groceries" 
    ↓ webhook_handler.py receives
    ↓ message_router.py coordinates
    ↓ message_classifier.py determines "note"
    ↓ tagging.py suggests #shopping
    ↓ supabase_service.py stores message
    ↓ whatsapp_service.py confirms receipt
```

### **Pattern 2: Complex Reminder Processing**
```
User sends "Remind me to call mom tomorrow at 3pm"
    ↓ webhook_handler.py receives
    ↓ message_router.py coordinates  
    ↓ message_classifier.py determines "reminder"
    ↓ reminder_parser.py extracts time/date
    ↓ reminders.py creates reminder entry
    ↓ supabase_service.py stores reminder + message
    ↓ whatsapp_service.py confirms setup
```

### **Pattern 3: Brain Dump Session**
```
User sends "#work Starting brain dump"
    ↓ brain_dump.py detects start signal
    ↓ Session state stored in database
    
User sends "Project deadline Friday"  
    ↓ brain_dump.py adds to existing session
    
User sends "Need to update website"
    ↓ brain_dump.py adds to session
    
User sends "Done with brain dump"
    ↓ brain_dump.py processes complete session
    ↓ tagging.py suggests tags for all messages
    ↓ embeddings.py generates vectors for search
    ↓ supabase_service.py stores complete session
```

### **Pattern 4: Media Processing**
```
User sends voice message
    ↓ webhook_handler.py receives media webhook
    ↓ whatsapp_service.py downloads audio file
    ↓ storage_service.py uploads to user folder
    ↓ openai_service.py transcribes with Whisper
    ↓ message_classifier.py classifies transcribed text
    ↓ embeddings.py generates vectors for searchability  
    ↓ supabase_service.py stores transcription + metadata
    ↓ whatsapp_service.py confirms processing
```

### **Pattern 5: Search Query Processing**
```
User sends "/search project ideas"
    ↓ slash_commands.py detects search command
    ↓ search.py processes query
    ↓ embeddings.py generates query vector
    ↓ supabase_service.py performs vector similarity search
    ↓ search.py ranks and formats results
    ↓ whatsapp_service.py sends formatted results
```

### **Pattern 6: Admin Dashboard Request**
```
Admin visits /admin/user/users/uuid
    ↓ main.py routes to user_admin.py
    ↓ user_admin.py fetches user data
    ↓ supabase_service.py queries messages, reminders, birthdays
    ↓ Data organized by type and date
    ↓ Template rendered with chat-style conversation view
    ↓ JavaScript handles timeline interactions and search
```

## 🏛️ Architectural Principles

### **1. Separation of Concerns**
- **Handlers**: HTTP request/response management
- **Services**: External API integrations
- **Workflows**: Business logic and orchestration
- **AI**: Machine learning and intelligence
- **Models**: Data structures and validation
- **Utils**: Shared functionality

### **2. Dependency Flow**
- **Main** → **Handlers** → **Workflows** → **Services**
- **AI components** used by **Workflows**
- **Models** used throughout for validation
- **Utils** used everywhere for common operations

### **3. Error Handling Strategy**
- **Graceful Degradation**: System continues operating with reduced functionality
- **Comprehensive Logging**: Detailed error tracking for debugging
- **User-Friendly Messages**: Clear error communication to users
- **Automatic Retry**: Transient failures handled automatically

### **4. Scalability Considerations**
- **Async Processing**: FastAPI with async/await throughout
- **Database Optimization**: Efficient queries with proper indexing
- **Caching Strategy**: Prepared for Redis integration
- **Stateless Design**: Easy horizontal scaling

### **5. Security Implementation**
- **Input Validation**: All inputs validated at entry points
- **Row-Level Security**: Database-level access control
- **Token Management**: Secure API key handling
- **File Isolation**: User-specific storage organization

## 🔧 Configuration & Environment

### **Environment-Specific Behavior**
- **Development**: `ENVIRONMENT=development` enables debug features
- **Production**: `ENVIRONMENT=production` optimizes for performance
- **Testing**: `ENVIRONMENT=test` uses test databases and mocks

### **Service Dependencies**
- **Required**: Supabase, OpenAI, WhatsApp Business API
- **Optional**: Cloudflare Tunnel (for local development)
- **Monitoring**: Built-in health checks and status endpoints

## 📊 Performance & Monitoring

### **Built-in Monitoring**
- **Health Endpoints**: System status and component health
- **Admin Dashboard**: Real-time system monitoring
- **Token Status**: WhatsApp token health tracking
- **Database Metrics**: Connection and query performance

### **Logging Strategy**
- **Structured Logging**: JSON-formatted logs for parsing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Component Identification**: Each component logs with context
- **Error Tracking**: Comprehensive error capture and reporting

This architecture ensures the GetCute WhatsApp Bot is maintainable, scalable, and provides a seamless experience for both users and administrators while maintaining high code quality and security standards.
