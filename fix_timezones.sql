-- Fix timezone issues in existing messages
-- This script ensures all timestamps are stored as UTC properly

-- First, let's check what we have
SELECT 
    id,
    message_timestamp,
    created_at,
    EXTRACT(timezone FROM message_timestamp) as msg_tz,
    EXTRACT(timezone FROM created_at) as created_tz
FROM messages 
ORDER BY message_timestamp DESC 
LIMIT 10;

-- If timestamps are stored without timezone or with wrong timezone,
-- we need to convert them to proper UTC

-- Option 1: If timestamps are stored as local time but should be UTC
-- UPDATE messages 
-- SET message_timestamp = message_timestamp AT TIME ZONE 'Europe/Berlin' AT TIME ZONE 'UTC'
-- WHERE message_timestamp IS NOT NULL;

-- Option 2: If timestamps are stored without timezone info and are actually UTC
-- UPDATE messages 
-- SET message_timestamp = message_timestamp AT TIME ZONE 'UTC'
-- WHERE message_timestamp IS NOT NULL;

-- Option 3: If timestamps need to be converted from local time to UTC
-- (Replace 'Your/Timezone' with your actual timezone)
-- UPDATE messages 
-- SET message_timestamp = (message_timestamp AT TIME ZONE 'Your/Timezone') AT TIME ZONE 'UTC'
-- WHERE message_timestamp IS NOT NULL;

-- After fixing, verify the timestamps look correct:
-- SELECT 
--     id,
--     message_timestamp,
--     message_timestamp AT TIME ZONE 'UTC' as utc_time,
--     message_timestamp AT TIME ZONE 'Europe/Berlin' as local_time
-- FROM messages 
-- ORDER BY message_timestamp DESC 
-- LIMIT 5;

-- For new messages going forward, ensure they're always stored with +00:00 timezone
