"""
Common helper functions for the Cute WhatsApp Bot.
"""
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4


def generate_unique_id() -> str:
    """Generate a unique identifier."""
    return str(uuid4())


def clean_phone_number(phone: str) -> str:
    """Clean and format phone number."""
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Ensure it starts with +
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    hashtags = re.findall(r'#(\w+)', text)
    return [tag.lower().strip() for tag in hashtags if tag.strip()]


def remove_hashtags(text: str) -> str:
    """Remove hashtags from text, leaving clean content."""
    return re.sub(r'#\w+\s*', '', text).strip()


def is_url(text: str) -> bool:
    """Check if text contains a URL."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return bool(re.search(url_pattern, text))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_datetime(dt: datetime, format_type: str = "friendly") -> str:
    """Format datetime in various friendly formats."""
    now = datetime.now()
    diff = now - dt
    
    if format_type == "friendly":
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago" if minutes > 1 else "just now"
            else:  # Less than 1 day
                hours = diff.seconds // 3600
                return f"{hours} hours ago" if hours > 1 else "1 hour ago"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%b %d, %Y")
    
    elif format_type == "iso":
        return dt.isoformat()
    
    elif format_type == "short":
        return dt.strftime("%m/%d %H:%M")
    
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_time_expression(text: str) -> Optional[datetime]:
    """Parse natural language time expressions."""
    text = text.lower().strip()
    now = datetime.now()
    
    # Simple patterns - in production, use more sophisticated NLP
    patterns = {
        r'tomorrow': now + timedelta(days=1),
        r'today': now,
        r'next week': now + timedelta(weeks=1),
        r'next month': now + timedelta(days=30),
        r'in (\d+) minutes?': lambda m: now + timedelta(minutes=int(m.group(1))),
        r'in (\d+) hours?': lambda m: now + timedelta(hours=int(m.group(1))),
        r'in (\d+) days?': lambda m: now + timedelta(days=int(m.group(1))),
    }
    
    for pattern, result in patterns.items():
        match = re.search(pattern, text)
        if match:
            if callable(result):
                # Call the lambda function and ensure it returns datetime
                calculated_result = result(match)
                if isinstance(calculated_result, datetime):
                    return calculated_result
            elif isinstance(result, datetime):
                return result
    
    return None


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score."""
    # Simple Jaccard similarity on words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def hash_text(text: str) -> str:
    """Generate hash for text content."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def validate_tag(tag: str) -> bool:
    """Validate if a tag is properly formatted."""
    # Tags should be alphanumeric, can contain underscores and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, tag)) and 1 <= len(tag) <= 50


def sanitize_tag(tag: str) -> str:
    """Sanitize tag input."""
    # Remove # if present, clean whitespace, lowercase
    cleaned = tag.replace('#', '').strip().lower()
    
    # Replace spaces with underscores
    cleaned = re.sub(r'\s+', '_', cleaned)
    
    # Keep only alphanumeric, underscore, hyphen
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', cleaned)
    
    return cleaned[:50]  # Limit length


def group_by_date(items: List[Dict[str, Any]], date_field: str = "timestamp") -> Dict[str, List[Dict[str, Any]]]:
    """Group items by date."""
    groups = {}
    
    for item in items:
        date_str = item.get(date_field, "")
        if isinstance(date_str, str):
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_key = date_obj.strftime("%Y-%m-%d")
            except:
                date_key = "unknown"
        elif isinstance(date_str, datetime):
            date_key = date_str.strftime("%Y-%m-%d")
        else:
            date_key = "unknown"
        
        if date_key not in groups:
            groups[date_key] = []
        groups[date_key].append(item)
    
    return groups


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)  # Convert to float for division
    i = 0
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def is_business_hours(dt: Optional[datetime] = None) -> bool:
    """Check if given time is during business hours (9 AM - 5 PM, Mon-Fri)."""
    if dt is None:
        dt = datetime.now()
    
    # Monday = 0, Sunday = 6
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False
    
    hour = dt.hour
    return 9 <= hour < 17  # 9 AM to 5 PM


def create_portal_url(base_url: str, token: str, path: str = "/") -> str:
    """Create authenticated portal URL."""
    return f"{base_url.rstrip('/')}/portal{path}?token={token}"


def extract_command_args(text: str) -> tuple[str, List[str]]:
    """Extract command and arguments from text."""
    parts = text.strip().split()
    if not parts:
        return "", []
    
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    return command, args


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support."""
    try:
        keys = key.split('.')
        value = dictionary
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default
