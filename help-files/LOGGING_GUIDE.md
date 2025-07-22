# WhatsApp Bot Comprehensive Logging & Debugging Guide

## 📊 Overview

I've implemented a comprehensive logging system that tracks every stage of message processing through your WhatsApp bot. This system will help you debug issues with image uploads, birthday storage, and any other processing problems.

## 🔧 What Was Added

### 1. Comprehensive Logging System (`src/utils/logger.py`)
- **MessageProcessingLogger**: Specialized logger for tracking message flow
- **Multiple log levels**: DEBUG, INFO, ERROR with separate files
- **Structured JSON logging**: Easy to parse and analyze
- **Rotating log files**: Prevents disk space issues

### 2. Enhanced Message Router (`src/handlers/message_router.py`)
- **Stage-by-stage logging**: Every processing step is tracked
- **Error tracking**: Detailed error context and recovery attempts
- **Media processing logs**: Complete image/file upload pipeline tracking
- **Birthday parsing logs**: Detailed birthday extraction and storage tracking

### 3. Database & Service Logging
- **Supabase operations**: All database saves/queries logged
- **WhatsApp API calls**: Media downloads and message sending tracked
- **Storage service**: File uploads and folder creation monitoring

### 4. Analysis Tools
- **test_logging.py**: Test script to generate sample logs
- **analyze_logs.py**: Log analyzer to understand message flows

## 📁 Log Files Generated

```
logs/
├── message_processing.log    # Detailed message flow tracking
├── application.log          # General application logs  
├── debug.log               # Debug-level information
├── error.log              # Errors only
└── errors.log            # Custom error tracking
```

## 🔍 Debugging Your Issues

### Issue 1: Image Upload Not Creating Folder/Uploading to Supabase

**What to look for in logs:**
```bash
# Check media processing stages
grep "MEDIA_" logs/message_processing.log

# Look for these stages:
MEDIA_DOWNLOAD_START        # WhatsApp media download initiated
WHATSAPP_MEDIA_DOWNLOAD_*   # WhatsApp download success/failure
USER_FOLDER_CREATE_*        # Supabase folder creation
FILE_UPLOAD_*               # File upload to Supabase Storage
```

**Common issues and solutions:**
1. **WhatsApp Media Download Fails**
   - Check if media_id is valid
   - Verify WhatsApp token is still valid
   - Check if media URL is accessible

2. **Supabase Folder Creation Fails**
   - Verify Supabase storage bucket exists (`user-media`)
   - Check if storage service has proper credentials
   - Look for permission issues

3. **File Upload Fails**
   - Check file size limits
   - Verify content type detection
   - Look for network connectivity issues

### Issue 2: Birthday Not Showing Under Birthdays

**What to look for in logs:**
```bash
# Check birthday processing
grep "BIRTHDAY" logs/message_processing.log

# Look for these stages:
BIRTHDAY_PROCESSING     # Birthday handling started
BIRTHDAY_PARSED        # Birthday info extracted from text
BIRTHDAY_COMPLETE      # Birthday saved successfully
DB_SUCCESS             # Database operation succeeded
```

**Common issues and solutions:**
1. **Birthday Parsing Fails**
   - Check if the message format matches expected patterns
   - Look for date parsing errors
   - Verify regex patterns in `_parse_birthday_info()`

2. **Database Storage Fails**
   - Check Supabase `birthdays` table exists
   - Verify user_id is valid (not None)
   - Look for data validation errors

3. **Admin Panel Display Issues**
   - Verify admin queries are using correct column names
   - Check if RLS policies allow admin access
   - Look for frontend JavaScript errors

## 🚀 How to Use the Logging System

### 1. Start with Normal Bot Operation
```bash
python start_bot.py  # or python run_server.py
```

### 2. Send Test Messages
- Send an image via WhatsApp
- Send a birthday message like "John's birthday is March 15th"
- Check logs in real-time

### 3. Analyze the Logs
```bash
# View recent message processing
python analyze_logs.py

# Or manually check specific logs
cat logs/message_processing.log | tail -50
cat logs/error.log
```

### 4. Debug Specific Issues
```bash
# Find all image processing attempts
grep -A 10 -B 5 "MEDIA_PROCESSING" logs/message_processing.log

# Find all birthday processing attempts  
grep -A 10 -B 5 "BIRTHDAY_PROCESSING" logs/message_processing.log

# Find all database errors
grep "DB_ERROR" logs/message_processing.log
```

## 📋 Debugging Checklist

### For Image Upload Issues:
- [ ] Check WhatsApp media download logs
- [ ] Verify Supabase storage bucket exists and is accessible
- [ ] Check user folder creation logs  
- [ ] Verify file upload completion
- [ ] Check if media_url is saved to database
- [ ] Verify signed URL generation

### For Birthday Issues:
- [ ] Check AI classification (should be "birthday")
- [ ] Verify birthday parsing succeeded
- [ ] Check database save operation
- [ ] Verify admin panel queries
- [ ] Check frontend display logic
- [ ] Verify date format compatibility

### For General Issues:
- [ ] Check message reception logs
- [ ] Verify user lookup/creation
- [ ] Check AI classification results
- [ ] Verify WhatsApp response sending
- [ ] Check for any unhandled exceptions

## 🔧 Advanced Debugging

### Custom Log Analysis
```python
# Add this to any file for custom logging
from utils.logger import get_message_logger
msg_logger = get_message_logger()

# Log custom events
msg_logger.log_message_stage("CUSTOM_STAGE", message_data, {"custom_info": "value"})
```

### Real-time Log Monitoring (Linux/Mac)
```bash
# Watch logs in real-time
tail -f logs/message_processing.log

# Filter for specific stages
tail -f logs/message_processing.log | grep "BIRTHDAY\|MEDIA"
```

### Database Operation Monitoring
```python
# All database operations are automatically logged
# Look for these patterns in logs:
DB_SUCCESS: {"operation": "INSERT", "table": "messages", "record_id": "..."}
DB_ERROR: {"operation": "INSERT", "table": "birthdays", "error": "..."}
```

## 🎯 Expected Log Flow for Your Use Cases

### Successful Image Upload Flow:
```
MESSAGE_RECEIVED → USER_LOOKUP → SESSION_CHECK → TAG_RESPONSE_CHECK → 
AI_CLASSIFICATION → WORKFLOW_ROUTING → NOTE_CREATION → MESSAGE_RECORD_CREATION → 
DATABASE_SAVE → MEDIA_PROCESSING_START → WHATSAPP_MEDIA_DOWNLOAD_START → 
WHATSAPP_MEDIA_DOWNLOAD_SUCCESS → USER_FOLDER_CREATE_SUCCESS → 
FILE_UPLOAD_SUCCESS → NOTE_COMPLETE → MESSAGE_COMPLETE
```

### Successful Birthday Processing Flow:
```
MESSAGE_RECEIVED → USER_LOOKUP → SESSION_CHECK → TAG_RESPONSE_CHECK → 
AI_CLASSIFICATION → WORKFLOW_ROUTING → BIRTHDAY_PROCESSING → 
BIRTHDAY_PARSED → DATABASE_SAVE → BIRTHDAY_COMPLETE → MESSAGE_COMPLETE
```

## 📈 Performance Monitoring

The logging system also tracks:
- **Response times**: Time between stages
- **File sizes**: Media file processing
- **Success rates**: Percentage of successful operations
- **Error patterns**: Common failure points

## 🛠️ Next Steps

1. **Run the bot** with the new logging system
2. **Send test messages** (image and birthday)
3. **Check the logs** using `python analyze_logs.py`
4. **Identify specific failure points** from the structured logs
5. **Apply targeted fixes** based on the log analysis

The comprehensive logging system will now show you exactly where in the pipeline things are failing, making debugging much more efficient!

## 📞 Troubleshooting Quick Commands

```bash
# See all recent errors
grep "ERROR" logs/error.log | tail -20

# Check media processing issues  
grep -E "(MEDIA|UPLOAD|DOWNLOAD)" logs/message_processing.log

# Check birthday processing
grep -E "(BIRTHDAY|DB_.*birthday)" logs/message_processing.log

# Monitor live processing
python test_logging.py  # Test with sample data
```
