"""
Service for detecting and managing user timezones.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from src.services.supabase_service import SupabaseService
from src.utils.timezone_utils import TimezoneManager
from src.models.database import User

logger = logging.getLogger(__name__)


class UserTimezoneService:
    """Service for managing user timezone settings."""
    
    def __init__(self, db_service: SupabaseService):
        self.db_service = db_service
    
    async def detect_and_set_timezone(self, user_id: str, phone_number: str) -> str:
        """
        Detect user's timezone and set it in the database.
        
        Uses multiple detection methods in order of reliability:
        1. Phone number country code mapping
        2. Interactive detection (ask user)
        3. Fallback to UTC
        
        Args:
            user_id: User's ID
            phone_number: User's phone number (format: +1234567890)
            
        Returns:
            Detected timezone string
        """
        try:
            # Method 1: Detect from phone number country code
            detected_timezone = self._detect_timezone_from_phone(phone_number)
            
            if detected_timezone != "UTC":
                # Update user's timezone in database
                await self.set_user_timezone(user_id, detected_timezone)
                logger.info(f"Detected timezone {detected_timezone} from phone {phone_number} for user {user_id}")
                return detected_timezone
            
            # Method 2: If phone detection fails, we'll need interactive detection
            # For now, fallback to UTC and mark for interactive setup
            await self.set_user_timezone(user_id, "UTC")
            logger.info(f"Could not detect timezone from phone {phone_number}, defaulting to UTC for user {user_id}")
            
            # TODO: Send interactive timezone setup message to user
            return "UTC"
            
        except Exception as e:
            logger.error(f"Error detecting timezone for user {user_id}: {e}")
            # Fallback to UTC
            await self.set_user_timezone(user_id, "UTC")
            return "UTC"
    
    def _detect_timezone_from_phone(self, phone_number: str) -> str:
        """
        Detect timezone from phone number country code.
        
        Args:
            phone_number: Phone number in international format (+1234567890 or 1234567890)
            
        Returns:
            IANA timezone string or "UTC" if cannot determine
        """
        try:
            # Handle both formats: +27123456789 and 27123456789
            if phone_number.startswith('+'):
                number_without_plus = phone_number[1:]  # Remove the +
            else:
                number_without_plus = phone_number  # Already without +
            
            # Must have at least 7 digits (country code + some digits)
            if len(number_without_plus) < 7:
                return "UTC"
            
            # Extract country code (this is simplified - real implementation would use a proper library)
            # Common country codes and their primary timezones
            country_timezone_map = {
                # North America
                "1": "America/New_York",        # US/Canada (Eastern as default)
                
                # Europe
                "33": "Europe/Paris",           # France
                "34": "Europe/Madrid",          # Spain
                "39": "Europe/Rome",            # Italy
                "41": "Europe/Zurich",          # Switzerland
                "43": "Europe/Vienna",          # Austria
                "44": "Europe/London",          # UK
                "45": "Europe/Copenhagen",      # Denmark
                "46": "Europe/Stockholm",       # Sweden
                "47": "Europe/Oslo",            # Norway
                "49": "Europe/Berlin",          # Germany
                "31": "Europe/Amsterdam",       # Netherlands
                "32": "Europe/Brussels",        # Belgium
                "351": "Europe/Lisbon",         # Portugal
                "358": "Europe/Helsinki",       # Finland
                "420": "Europe/Prague",         # Czech Republic
                "48": "Europe/Warsaw",          # Poland
                
                # Asia Pacific
                "81": "Asia/Tokyo",             # Japan
                "82": "Asia/Seoul",             # South Korea
                "86": "Asia/Shanghai",          # China
                "65": "Asia/Singapore",         # Singapore
                "60": "Asia/Kuala_Lumpur",      # Malaysia
                "66": "Asia/Bangkok",           # Thailand
                "84": "Asia/Ho_Chi_Minh",       # Vietnam
                "62": "Asia/Jakarta",           # Indonesia
                "63": "Asia/Manila",            # Philippines
                "91": "Asia/Kolkata",           # India
                "92": "Asia/Karachi",           # Pakistan
                "971": "Asia/Dubai",            # UAE
                "966": "Asia/Riyadh",           # Saudi Arabia
                
                # Australia/Oceania
                "61": "Australia/Sydney",       # Australia
                "64": "Pacific/Auckland",       # New Zealand
                
                # South America
                "55": "America/Sao_Paulo",      # Brazil
                "54": "America/Argentina/Buenos_Aires",  # Argentina
                "56": "America/Santiago",       # Chile
                "57": "America/Bogota",         # Colombia
                "51": "America/Lima",           # Peru
                
                # Africa
                "27": "Africa/Johannesburg",    # South Africa
                "20": "Africa/Cairo",           # Egypt
                "234": "Africa/Lagos",          # Nigeria
                "254": "Africa/Nairobi",        # Kenya
            }
            
            # Try exact matches first (for longer country codes)
            for code_length in [4, 3, 2, 1]:  # Check longer codes first
                if len(number_without_plus) > code_length:
                    country_code = number_without_plus[:code_length]  # Extract country code
                    if country_code in country_timezone_map:
                        timezone = country_timezone_map[country_code]
                        logger.info(f"Detected timezone {timezone} from country code +{country_code} (phone: {phone_number})")
                        return timezone
            
            # If no match found, default to UTC
            logger.warning(f"Could not determine timezone from phone number {phone_number}")
            return "UTC"
            
        except Exception as e:
            logger.error(f"Error detecting timezone from phone {phone_number}: {e}")
            return "UTC"
    
    def detect_timezone_from_time_reference(self, user_message: str, utc_now: datetime) -> Optional[str]:
        """
        Detect timezone from user's time references in their messages.
        
        Example: If user says "remind me at 5 PM" and it's currently 3 PM UTC,
        and their local context suggests it's currently 5 PM for them,
        then they're likely in UTC+2.
        
        Args:
            user_message: User's message containing time reference
            utc_now: Current UTC datetime
            
        Returns:
            IANA timezone string or None if cannot determine
        """
        try:
            import re
            
            # Look for time references in the message
            time_patterns = [
                r'\b(\d{1,2}):(\d{2})\s*(AM|PM)\b',           # 5:30 PM
                r'\b(\d{1,2})\s*(AM|PM)\b',                   # 5 PM  
                r'\b(\d{1,2}):(\d{2})\b',                     # 17:30 (24h)
                r'\bat\s+(\d{1,2})\b',                        # at 5
            ]
            
            user_hour = None
            is_pm = False
            
            for pattern in time_patterns:
                match = re.search(pattern, user_message.upper())
                if match:
                    if 'AM' in pattern or 'PM' in pattern:
                        user_hour = int(match.group(1))
                        is_pm = 'PM' in match.groups()
                        if is_pm and user_hour != 12:
                            user_hour += 12
                        elif not is_pm and user_hour == 12:
                            user_hour = 0
                    else:
                        user_hour = int(match.group(1))
                    break
            
            if user_hour is None:
                return None
            
            # Compare with current UTC time
            utc_hour = utc_now.hour
            
            # Calculate potential offset
            # This is a simplified heuristic - assumes user means "today"
            offset_hours = user_hour - utc_hour
            
            # Handle day boundary issues (rough approximation)
            if offset_hours > 12:
                offset_hours -= 24
            elif offset_hours < -12:
                offset_hours += 24
            
            # Only trust offsets that make sense (±12 hours)
            if -12 <= offset_hours <= 12:
                detected_timezone = TimezoneManager.detect_timezone_from_offset(offset_hours)
                logger.info(f"Detected timezone {detected_timezone} from time reference '{user_message}' (offset: {offset_hours}h)")
                return detected_timezone
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting timezone from time reference: {e}")
            return None
    
    async def set_user_timezone(self, user_id: str, timezone_str: str) -> bool:
        """
        Set a user's timezone in the database.
        
        Args:
            user_id: User's ID
            timezone_str: IANA timezone string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate timezone
            if not TimezoneManager.is_valid_timezone(timezone_str):
                logger.warning(f"Invalid timezone {timezone_str} for user {user_id}, using UTC")
                timezone_str = "UTC"
            
            # Update in database
            result = self.db_service.admin_client.table("users").update({
                "timezone": timezone_str
            }).eq("id", user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error setting timezone {timezone_str} for user {user_id}: {e}")
            return False
    
    async def get_user_timezone(self, user_id: str) -> str:
        """
        Get a user's timezone from the database.
        
        Args:
            user_id: User's ID
            
        Returns:
            User's timezone string, defaults to UTC if not found
        """
        try:
            result = self.db_service.admin_client.table("users").select("timezone").eq("id", user_id).execute()
            
            if result.data and result.data[0].get("timezone"):
                return result.data[0]["timezone"]
            else:
                # User doesn't have timezone set, detect and set it
                user_result = self.db_service.admin_client.table("users").select("phone_number").eq("id", user_id).execute()
                if user_result.data:
                    phone_number = user_result.data[0]["phone_number"]
                    return await self.detect_and_set_timezone(user_id, phone_number)
                else:
                    return "UTC"
                    
        except Exception as e:
            logger.error(f"Error getting timezone for user {user_id}: {e}")
            return "UTC"
    
    async def update_timezone_from_command(self, user_id: str, timezone_command: str) -> tuple[bool, str]:
        """
        Update user's timezone from a command like "/timezone Europe/Berlin".
        
        Args:
            user_id: User's ID
            timezone_command: Timezone command string
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract timezone from command
            parts = timezone_command.strip().split()
            if len(parts) < 2:
                return False, "Please specify a timezone. Example: /timezone Europe/Berlin"
            
            timezone_str = parts[1]
            
            # Validate timezone
            if not TimezoneManager.is_valid_timezone(timezone_str):
                return False, f"Invalid timezone: {timezone_str}. Please use IANA timezone format (e.g., Europe/Berlin, America/New_York)"
            
            # Set timezone
            success = await self.set_user_timezone(user_id, timezone_str)
            
            if success:
                # Get timezone info for confirmation
                tz_info = TimezoneManager.get_timezone_info(timezone_str)
                return True, f"✅ Timezone set to {timezone_str}\nCurrent time: {tz_info['current_time']} ({tz_info['timezone_name']})"
            else:
                return False, "Failed to update timezone. Please try again."
                
        except Exception as e:
            logger.error(f"Error updating timezone from command for user {user_id}: {e}")
            return False, "Error updating timezone. Please try again."
    
    async def improve_timezone_from_message(self, user_id: str, message_content: str) -> bool:
        """
        Try to improve timezone detection based on time references in user messages.
        
        This is called when processing reminder messages to potentially refine
        the user's timezone based on their time references.
        
        Args:
            user_id: User's ID
            message_content: User's message content
            
        Returns:
            True if timezone was updated, False otherwise
        """
        try:
            # Get current timezone
            current_timezone = await self.get_user_timezone(user_id)
            
            # Only try to improve if currently set to UTC (default)
            if current_timezone != "UTC":
                return False
            
            # Try to detect from time reference
            utc_now = datetime.now(timezone.utc)
            detected_timezone = self.detect_timezone_from_time_reference(message_content, utc_now)
            
            if detected_timezone and detected_timezone != "UTC":
                # Update timezone
                success = await self.set_user_timezone(user_id, detected_timezone)
                if success:
                    logger.info(f"Improved timezone from message: {detected_timezone} for user {user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error improving timezone from message for user {user_id}: {e}")
            return False
    
    def get_timezone_help_message(self) -> str:
        """
        Get help message for timezone commands.
        
        Returns:
            Help message string
        """
        return """🌍 **Timezone Commands:**

To set your timezone:
`/timezone [IANA_TIMEZONE]`

Examples:
• `/timezone Europe/Berlin` (Germany)
• `/timezone America/New_York` (US Eastern)
• `/timezone Asia/Tokyo` (Japan)
• `/timezone Australia/Sydney` (Australia)

To see your current timezone:
`/timezone info`

**Common Timezones:**
• Europe: Berlin, London, Paris, Rome
• America: New_York, Los_Angeles, Chicago, Toronto
• Asia: Tokyo, Shanghai, Singapore, Dubai
• Australia: Sydney, Melbourne, Perth

For full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"""
