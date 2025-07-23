"""
Comprehensive logging configuration for the WhatsApp bot.
Tracks messages through all processing stages.
"""
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import sys


def safe_log_content(content: str, max_length: int = 50) -> str:
    """Make content safe for logging by replacing emojis and problematic Unicode characters.
    
    Args:
        content: The content to make safe
        max_length: Maximum length to truncate to
        
    Returns:
        Safe content string for logging
    """
    # Truncate first
    safe_content = content[:max_length]
    
    # Replace common emojis that cause Windows console issues
    emoji_replacements = {
        '🤖': '[BOT]',
        '✅': '[OK]',
        '❌': '[ERROR]',
        '📱': '[PHONE]',
        '📷': '[IMAGE]',
        '🎵': '[AUDIO]',
        '📄': '[DOC]',
        '⚠️': '[WARN]',
        '🔍': '[SEARCH]',
        '💾': '[SAVE]',
        '💚': '[HEART]',
        '🔔': '[BELL]',
        '📅': '[CALENDAR]',
        '⏰': '[CLOCK]',
        '🎯': '[TARGET]',
    }
    
    for emoji, replacement in emoji_replacements.items():
        safe_content = safe_content.replace(emoji, replacement)
    
    # If there are still problematic Unicode characters, replace them
    if sys.platform.startswith('win'):
        try:
            safe_content.encode('cp1252')
        except UnicodeEncodeError:
            safe_content = safe_content.encode('ascii', 'replace').decode('ascii')
    
    return safe_content


class SafeUnicodeFormatter(logging.Formatter):
    """Formatter that handles Unicode characters safely for Windows console."""
    
    def format(self, record):
        # Get the formatted message
        formatted = super().format(record)
        
        # On Windows, replace problematic Unicode characters to avoid encoding errors
        if sys.platform.startswith('win'):
            # Replace common emojis that cause issues on Windows console
            replacements = {
                '🤖': '[BOT]',
                '✅': '[OK]',
                '❌': '[ERROR]',
                '📱': '[PHONE]',
                '📷': '[IMAGE]',
                '🎵': '[AUDIO]',
                '📄': '[DOC]',
                '⚠️': '[WARN]',
                '🔍': '[SEARCH]',
                '💾': '[SAVE]',
            }
            
            for emoji, replacement in replacements.items():
                formatted = formatted.replace(emoji, replacement)
        
        return formatted


class MessageProcessingLogger:
    """Custom logger for tracking message processing stages."""
    
    def __init__(self, name: str = "message_processing"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler for all messages
        file_handler = logging.handlers.RotatingFileHandler(
            "logs/message_processing.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # File handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            "logs/errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler for development with UTF-8 encoding
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Detailed formatter for files
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        
        # Simple formatter for console with Unicode safety
        simple_formatter = SafeUnicodeFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def log_message_stage(self, stage: str, message_data: Dict[str, Any], extra_info: Optional[Dict[str, Any]] = None):
        """Log a message processing stage with structured data."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "message_id": message_data.get("message_id", "unknown"),
            "user_phone": message_data.get("user_phone", "unknown"),
            "content_preview": str(message_data.get("content", ""))[:100],
            "message_type": message_data.get("message_type", "unknown"),
            "media_id": message_data.get("media_id"),
            "extra_info": extra_info or {}
        }
        
        self.logger.info(f"STAGE_{stage.upper()}: {json.dumps(log_entry, indent=2)}")
    
    def log_error_stage(self, stage: str, error: Exception, message_data: Dict[str, Any], extra_info: Optional[Dict[str, Any]] = None):
        """Log an error during message processing."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "message_id": message_data.get("message_id", "unknown"),
            "user_phone": message_data.get("user_phone", "unknown"),
            "content_preview": str(message_data.get("content", ""))[:100],
            "extra_info": extra_info or {}
        }
        
        self.logger.error(f"ERROR_STAGE_{stage.upper()}: {json.dumps(log_entry, indent=2)}", exc_info=True)
    
    def log_success_stage(self, stage: str, message_data: Dict[str, Any], result: Any = None, extra_info: Optional[Dict[str, Any]] = None):
        """Log a successful completion of a processing stage."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "status": "SUCCESS",
            "message_id": message_data.get("message_id", "unknown"),
            "user_phone": message_data.get("user_phone", "unknown"),
            "result_summary": str(result)[:200] if result else None,
            "extra_info": extra_info or {}
        }
        
        self.logger.info(f"SUCCESS_STAGE_{stage.upper()}: {json.dumps(log_entry, indent=2)}")
    
    def log_classification_result(self, message_data: Dict[str, Any], classification: Dict[str, Any]):
        """Log AI classification results."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "AI_CLASSIFICATION",
            "message_id": message_data.get("message_id", "unknown"),
            "user_phone": message_data.get("user_phone", "unknown"),
            "content_preview": str(message_data.get("content", ""))[:100],
            "classification": {
                "message_type": classification.get("message_type"),
                "confidence": classification.get("confidence"),
                "suggested_tags": classification.get("suggested_tags"),
                "requires_followup": classification.get("requires_followup")
            }
        }
        
        self.logger.info(f"AI_CLASSIFICATION: {json.dumps(log_entry, indent=2)}")
    
    def log_database_operation(self, operation: str, table: str, record_id: Optional[str] = None, success: bool = True, error: Optional[str] = None):
        """Log database operations."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "DATABASE_OPERATION",
            "operation": operation,
            "table": table,
            "record_id": record_id,
            "success": success,
            "error": error
        }
        
        if success:
            self.logger.info(f"DB_SUCCESS: {json.dumps(log_entry, indent=2)}")
        else:
            self.logger.error(f"DB_ERROR: {json.dumps(log_entry, indent=2)}")
    
    def log_media_processing(self, media_type: str, media_id: str, user_id: str, processing_stage: str, success: bool = True, error: Optional[str] = None, file_info: Optional[Dict[str, Any]] = None):
        """Log media processing stages."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "MEDIA_PROCESSING",
            "media_type": media_type,
            "media_id": media_id,
            "user_id": user_id,
            "processing_stage": processing_stage,
            "success": success,
            "error": error,
            "file_info": file_info or {}
        }
        
        if success:
            self.logger.info(f"MEDIA_SUCCESS: {json.dumps(log_entry, indent=2)}")
        else:
            self.logger.error(f"MEDIA_ERROR: {json.dumps(log_entry, indent=2)}")

    def log_ai_extraction_failure(self, extraction_type: str, user_message: str, ai_response: str, message_data: Dict[str, Any], failure_reason: str, extra_info: Optional[Dict[str, Any]] = None):
        """Log AI extraction failures for birthday and reminder requests.
        
        This helps track and improve AI prompts over time by capturing:
        - The user's original message
        - The AI's response (if any)
        - The reason for failure
        - Context about the message
        
        Args:
            extraction_type: "reminder" or "birthday"
            user_message: The original user message
            ai_response: The AI's response (JSON string, error message, etc.)
            message_data: Standard message data dict
            failure_reason: Why the extraction failed
            extra_info: Additional context
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "AI_EXTRACTION_FAILURE",
            "extraction_type": extraction_type,
            "message_id": message_data.get("message_id", "unknown"),
            "user_phone": message_data.get("user_phone", "unknown"),
            "user_id": message_data.get("user_id"),  # Will be populated if available
            "message_timestamp": message_data.get("timestamp"),  # Original message timestamp
            "user_message": user_message,
            "ai_response": ai_response,
            "failure_reason": failure_reason,
            "message_type": message_data.get("message_type", "unknown"),
            "extra_info": extra_info or {}
        }
        
        # Log to both the main log and create specific extraction failures logs
        self.logger.error(f"AI_EXTRACTION_FAILURE_{extraction_type.upper()}: {json.dumps(log_entry, indent=2)}")
        
        # Also write to dedicated extraction failures files
        self._log_to_extraction_failures_file(log_entry)

    def _log_to_extraction_failures_file(self, log_entry: Dict[str, Any]):
        """Write extraction failure logs to a dedicated file for analysis."""
        try:
            os.makedirs("logs", exist_ok=True)
            
            extraction_type = log_entry.get("extraction_type", "unknown")
            
            # Create type-specific logger
            logger_name = f"{extraction_type}_extraction_failures"
            specific_logger = logging.getLogger(logger_name)
            specific_logger.setLevel(logging.ERROR)
            
            # Clear existing handlers to avoid duplicates
            if not specific_logger.handlers:
                # Create specific log file for this extraction type
                log_filename = f"logs/{extraction_type}_process_failures.log"
                failure_handler = logging.handlers.RotatingFileHandler(
                    log_filename,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
                failure_handler.setLevel(logging.ERROR)
                
                # Use a simple formatter for the specific logs - just the essential data
                failure_formatter = logging.Formatter('%(message)s')
                failure_handler.setFormatter(failure_formatter)
                
                specific_logger.addHandler(failure_handler)
                specific_logger.propagate = False
            
            # Create a simplified log entry with only the requested fields
            simplified_entry = {
                "timestamp": log_entry.get("timestamp"),
                "user_id": log_entry.get("user_id") or log_entry.get("user_phone"),  # Prefer user_id, fallback to phone
                "message_id": log_entry.get("message_id"),
                "message_sent_time": log_entry.get("message_timestamp") or log_entry.get("timestamp"),  # Use original message timestamp if available
                "user_message": log_entry.get("user_message"),
                "ai_response": log_entry.get("ai_response")
            }
            
            # Log the simplified entry as JSON for easy parsing
            specific_logger.error(json.dumps(simplified_entry, indent=2))
            
            # Also write to the general extraction failures log (existing functionality)
            general_logger = logging.getLogger("extraction_failures")
            general_logger.setLevel(logging.ERROR)
            
            if not general_logger.handlers:
                general_handler = logging.handlers.RotatingFileHandler(
                    "logs/ai_extraction_failures.log",
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
                general_handler.setLevel(logging.ERROR)
                general_formatter = logging.Formatter('%(message)s')
                general_handler.setFormatter(general_formatter)
                general_logger.addHandler(general_handler)
                general_logger.propagate = False
            
            # Log the full entry to the general log
            general_logger.error(json.dumps(log_entry, indent=2))
            
        except Exception as e:
            # Don't let logging errors break the main flow
            self.logger.warning(f"Failed to write to extraction failures log: {e}")


def setup_application_logging():
    """Set up comprehensive logging for the entire application."""
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Main application log file
    app_handler = logging.handlers.RotatingFileHandler(
        "logs/application.log",
        maxBytes=20*1024*1024,  # 20MB
        backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    
    # Debug log file
    debug_handler = logging.handlers.RotatingFileHandler(
        "logs/debug.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    
    # Error log file
    error_handler = logging.handlers.RotatingFileHandler(
        "logs/error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    
    # Custom console handler that handles Unicode safely
    class SafeConsoleHandler(logging.StreamHandler):
        """Console handler that handles Unicode characters safely on Windows."""
        
        def emit(self, record):
            try:
                msg = self.format(record)
                
                # On Windows, replace problematic Unicode characters
                if sys.platform.startswith('win'):
                    # Replace common emojis that cause issues on Windows console
                    replacements = {
                        '🤖': '[BOT]',
                        '✅': '[OK]', 
                        '❌': '[ERROR]',
                        '📱': '[PHONE]',
                        '📷': '[IMAGE]',
                        '🎵': '[AUDIO]',
                        '📄': '[DOC]',
                        '⚠️': '[WARN]',
                        '🔍': '[SEARCH]',
                        '💾': '[SAVE]',
                    }
                    
                    for emoji, replacement in replacements.items():
                        msg = msg.replace(emoji, replacement)
                    
                    # If there are still Unicode characters that can't be encoded, replace them
                    try:
                        msg.encode('cp1252')
                    except UnicodeEncodeError:
                        # Replace any remaining problematic characters
                        msg = msg.encode('ascii', 'replace').decode('ascii')
                
                stream = self.stream
                stream.write(msg + self.terminator)
                stream.flush()
                
            except Exception:
                self.handleError(record)
    
    console_handler = SafeConsoleHandler()
    console_handler.setLevel(logging.INFO)
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Set formatters
    app_handler.setFormatter(detailed_formatter)
    debug_handler.setFormatter(detailed_formatter)
    error_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)  # Use the regular formatter for console
    
    # Add handlers to root logger
    root_logger.addHandler(app_handler)
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)


# Global message processing logger instance
message_logger = MessageProcessingLogger()


def get_message_logger() -> MessageProcessingLogger:
    """Get the global message processing logger."""
    return message_logger
