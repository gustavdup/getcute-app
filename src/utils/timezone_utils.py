"""
Timezone utilities for handling user timezones in the reminder system.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging
from zoneinfo import ZoneInfo, available_timezones

logger = logging.getLogger(__name__)


class TimezoneManager:
    """Manages timezone operations for users."""
    
    # Common timezone mappings for easier detection
    COMMON_TIMEZONES = {
        # Format: offset_hours -> [primary_timezone, alternatives...]
        -12: ["Pacific/Kwajalein"],
        -11: ["Pacific/Midway", "Pacific/Samoa"],
        -10: ["Pacific/Honolulu", "Pacific/Tahiti"],
        -9: ["America/Anchorage", "America/Juneau"],
        -8: ["America/Los_Angeles", "America/Vancouver", "Pacific/Pitcairn"],
        -7: ["America/Denver", "America/Phoenix", "America/Chihuahua"],
        -6: ["America/Chicago", "America/Mexico_City", "America/Guatemala"],
        -5: ["America/New_York", "America/Toronto", "America/Bogota"],
        -4: ["America/Halifax", "America/Caracas", "America/Santiago"],
        -3: ["America/Sao_Paulo", "America/Argentina/Buenos_Aires", "America/Montevideo"],
        -2: ["America/Noronha", "Atlantic/South_Georgia"],
        -1: ["Atlantic/Azores", "Atlantic/Cape_Verde"],
        0: ["UTC", "Europe/London", "Africa/Casablanca"],
        1: ["Europe/Berlin", "Europe/Paris", "Europe/Rome", "Africa/Lagos"],
        2: ["Europe/Helsinki", "Europe/Athens", "Africa/Cairo", "Asia/Jerusalem"],
        3: ["Europe/Moscow", "Asia/Baghdad", "Africa/Nairobi"],
        4: ["Asia/Dubai", "Asia/Baku", "Indian/Mauritius"],
        5: ["Asia/Karachi", "Asia/Tashkent", "Asia/Colombo"],
        6: ["Asia/Dhaka", "Asia/Almaty", "Asia/Bishkek"],
        7: ["Asia/Bangkok", "Asia/Jakarta", "Asia/Ho_Chi_Minh"],
        8: ["Asia/Shanghai", "Asia/Singapore", "Asia/Manila", "Australia/Perth"],
        9: ["Asia/Tokyo", "Asia/Seoul", "Australia/Darwin"],
        10: ["Australia/Sydney", "Australia/Melbourne", "Pacific/Guam"],
        11: ["Pacific/Norfolk", "Australia/Lord_Howe"],
        12: ["Pacific/Auckland", "Pacific/Fiji", "Asia/Kamchatka"],
    }
    
    @classmethod
    def detect_timezone_from_offset(cls, offset_hours: float) -> str:
        """
        Detect likely timezone from UTC offset.
        
        Args:
            offset_hours: Hours offset from UTC (e.g., 2.0 for UTC+2)
            
        Returns:
            IANA timezone string
        """
        # Round to nearest hour for lookup
        rounded_offset = round(offset_hours)
        
        if rounded_offset in cls.COMMON_TIMEZONES:
            # Return the first (most common) timezone for this offset
            return cls.COMMON_TIMEZONES[rounded_offset][0]
        
        # Fallback to UTC if we can't determine
        logger.warning(f"Unknown timezone offset: {offset_hours}, defaulting to UTC")
        return "UTC"
    
    @classmethod
    def detect_timezone_from_local_time(cls, local_time: datetime, utc_time: datetime) -> str:
        """
        Detect timezone from local and UTC time comparison.
        
        Args:
            local_time: User's local datetime (naive)
            utc_time: UTC datetime (timezone-aware)
            
        Returns:
            IANA timezone string
        """
        # Calculate offset in hours
        if local_time.tzinfo is None:
            # Assume local_time is naive, compare with UTC
            utc_naive = utc_time.replace(tzinfo=None)
            offset_seconds = (local_time - utc_naive).total_seconds()
            offset_hours = offset_seconds / 3600
            
            return cls.detect_timezone_from_offset(offset_hours)
        
        return "UTC"
    
    @classmethod
    def is_valid_timezone(cls, timezone_str: str) -> bool:
        """
        Check if a timezone string is valid IANA timezone.
        
        Args:
            timezone_str: IANA timezone string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ZoneInfo(timezone_str)
            return True
        except Exception:
            return False
    
    @classmethod
    def convert_to_utc(cls, local_time: datetime, user_timezone: str) -> datetime:
        """
        Convert a local datetime to UTC.
        
        Args:
            local_time: Local datetime (naive or timezone-aware)
            user_timezone: User's IANA timezone string
            
        Returns:
            UTC datetime with timezone info
        """
        try:
            if local_time.tzinfo is None:
                # Assume it's in user's timezone
                tz = ZoneInfo(user_timezone)
                local_with_tz = local_time.replace(tzinfo=tz)
            else:
                local_with_tz = local_time
            
            # Convert to UTC
            return local_with_tz.astimezone(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error converting {local_time} from {user_timezone} to UTC: {e}")
            # Fallback: assume it's already UTC
            return local_time.replace(tzinfo=timezone.utc)
    
    @classmethod
    def convert_from_utc(cls, utc_time: datetime, user_timezone: str) -> datetime:
        """
        Convert a UTC datetime to user's local timezone.
        
        Args:
            utc_time: UTC datetime (should be timezone-aware)
            user_timezone: User's IANA timezone string
            
        Returns:
            Local datetime in user's timezone
        """
        try:
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=timezone.utc)
            
            user_tz = ZoneInfo(user_timezone)
            return utc_time.astimezone(user_tz)
            
        except Exception as e:
            logger.error(f"Error converting {utc_time} to {user_timezone}: {e}")
            # Fallback: return as-is
            return utc_time
    
    @classmethod
    def get_timezone_info(cls, user_timezone: str) -> Dict[str, Any]:
        """
        Get information about a timezone.
        
        Args:
            user_timezone: IANA timezone string
            
        Returns:
            Dictionary with timezone info
        """
        try:
            tz = ZoneInfo(user_timezone)
            now_utc = datetime.now(timezone.utc)
            now_local = now_utc.astimezone(tz)
            
            # Calculate current offset
            utc_offset = now_local.utcoffset()
            if utc_offset:
                offset_seconds = utc_offset.total_seconds()
                offset_hours = offset_seconds / 3600
            else:
                offset_hours = 0
            
            return {
                "timezone": user_timezone,
                "current_offset_hours": offset_hours,
                "current_time": now_local.strftime("%Y-%m-%d %H:%M:%S"),
                "is_dst": bool(now_local.dst()),
                "timezone_name": now_local.tzname(),
            }
            
        except Exception as e:
            logger.error(f"Error getting timezone info for {user_timezone}: {e}")
            return {
                "timezone": user_timezone,
                "error": str(e),
                "current_offset_hours": 0,
                "current_time": "Unknown",
                "is_dst": False,
                "timezone_name": "Unknown",
            }
    
    @classmethod
    def format_time_for_user(cls, utc_time: datetime, user_timezone: str, 
                           include_timezone: bool = True) -> str:
        """
        Format a UTC time for display to a user in their timezone.
        
        Args:
            utc_time: UTC datetime
            user_timezone: User's IANA timezone
            include_timezone: Whether to include timezone abbreviation
            
        Returns:
            Formatted time string
        """
        local_time = cls.convert_from_utc(utc_time, user_timezone)
        
        if include_timezone:
            return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        else:
            return local_time.strftime("%Y-%m-%d %H:%M:%S")


# Convenience functions
def get_user_current_time(user_timezone: str) -> datetime:
    """Get current time in user's timezone."""
    utc_now = datetime.now(timezone.utc)
    return TimezoneManager.convert_from_utc(utc_now, user_timezone)


def parse_user_time(time_str: str, user_timezone: str, 
                   base_date: Optional[datetime] = None) -> datetime:
    """
    Parse a time string in user's timezone and convert to UTC.
    
    Args:
        time_str: Time string from user (e.g., "2025-07-23 17:03")
        user_timezone: User's IANA timezone
        base_date: Base date if time_str doesn't include date
        
    Returns:
        UTC datetime
    """
    try:
        # Try to parse the time string
        if base_date and len(time_str) <= 8:  # Likely just time, no date
            # Combine with base date
            from datetime import time
            parsed_time = datetime.strptime(time_str, "%H:%M").time()
            local_dt = datetime.combine(base_date.date(), parsed_time)
        else:
            # Try common datetime formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%d/%m/%Y %H:%M",
                "%m/%d/%Y %H:%M",
            ]:
                try:
                    local_dt = datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Could not parse time string: {time_str}")
        
        # Convert to UTC
        return TimezoneManager.convert_to_utc(local_dt, user_timezone)
        
    except Exception as e:
        logger.error(f"Error parsing user time '{time_str}' in timezone {user_timezone}: {e}")
        raise
