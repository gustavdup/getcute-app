-- Update messages table to support command message type
-- This adds the 'command' type to the existing message_type check constraint

BEGIN;

-- First, let's see the current constraint
-- DROP the existing constraint if it exists
ALTER TABLE messages 
DROP CONSTRAINT IF EXISTS messages_type_check;

-- Add the updated constraint that includes 'command'
ALTER TABLE messages 
ADD CONSTRAINT messages_type_check 
CHECK (type IN ('note', 'reminder', 'birthday', 'brain_dump', 'bot_response', 'command'));

-- Also ensure the enum type includes command (if using enum)
-- This might not be needed if using varchar, but included for completeness
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_type_enum') THEN
--         CREATE TYPE message_type_enum AS ENUM ('note', 'reminder', 'birthday', 'brain_dump', 'bot_response', 'command');
--     ELSE
--         -- Add command to existing enum if it doesn't exist
--         ALTER TYPE message_type_enum ADD VALUE IF NOT EXISTS 'command';
--     END IF;
-- END $$;

COMMIT;
