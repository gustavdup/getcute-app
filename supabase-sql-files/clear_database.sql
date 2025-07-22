-- ============================================================================
-- CLEAR DATABASE - Remove All Data While Preserving Structure
-- ============================================================================
-- WARNING: This script will DELETE ALL DATA from your database!
-- Only run this if you want to completely reset your bot's data.
-- The table structure and schema will remain intact.
-- ============================================================================

-- Disable foreign key checks temporarily (if supported)
-- Note: Supabase/PostgreSQL doesn't have FOREIGN_KEY_CHECKS like MySQL
-- Instead, we'll delete in the correct order to respect foreign key constraints

BEGIN;

-- ============================================================================
-- STEP 1: Clear all data in dependency order (children first, then parents)
-- ============================================================================

-- Clear session-related data first
DELETE FROM sessions;

-- Clear file-related data
DELETE FROM files;

-- Clear reminder data
DELETE FROM reminders;

-- Clear birthday data  
DELETE FROM birthdays;

-- Clear messages (this will cascade to related data if configured)
DELETE FROM messages;

-- Clear user data (this should be last as other tables reference users)
DELETE FROM users;

-- ============================================================================
-- STEP 2: Reset auto-increment sequences (if any)
-- ============================================================================
-- Note: PostgreSQL uses sequences for auto-incrementing fields
-- If your tables have serial/auto-increment fields, reset them

-- Reset sequences for tables that might have serial IDs
-- (Adjust table names and sequence names based on your actual schema)

-- Example resets (uncomment if you have auto-incrementing integer IDs):
-- ALTER SEQUENCE users_id_seq RESTART WITH 1;
-- ALTER SEQUENCE messages_id_seq RESTART WITH 1;
-- ALTER SEQUENCE sessions_id_seq RESTART WITH 1;
-- ALTER SEQUENCE reminders_id_seq RESTART WITH 1;
-- ALTER SEQUENCE birthdays_id_seq RESTART WITH 1;
-- ALTER SEQUENCE files_id_seq RESTART WITH 1;

-- ============================================================================
-- STEP 3: Verify all tables are empty
-- ============================================================================

-- Check row counts (should all be 0)
SELECT 
    'users' as table_name, 
    COUNT(*) as row_count 
FROM users

UNION ALL

SELECT 
    'messages' as table_name, 
    COUNT(*) as row_count 
FROM messages

UNION ALL

SELECT 
    'sessions' as table_name, 
    COUNT(*) as row_count 
FROM sessions

UNION ALL

SELECT 
    'reminders' as table_name, 
    COUNT(*) as row_count 
FROM reminders

UNION ALL

SELECT 
    'birthdays' as table_name, 
    COUNT(*) as row_count 
FROM birthdays

UNION ALL

SELECT 
    'files' as table_name, 
    COUNT(*) as row_count 
FROM files

ORDER BY table_name;

-- ============================================================================
-- STEP 4: Optional - Clear Supabase Storage Buckets
-- ============================================================================
-- Note: This SQL cannot delete files from Supabase Storage buckets
-- You'll need to manually clear the 'user-media' bucket through:
-- 1. Supabase Dashboard > Storage > user-media bucket > Select All > Delete
-- 2. Or use the Supabase CLI/API to delete bucket contents

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

-- If everything looks good, commit the transaction
COMMIT;

-- If you want to rollback instead, use:
-- ROLLBACK;

-- ============================================================================
-- POST-CLEANUP NOTES
-- ============================================================================
-- After running this script:
-- 1. All user conversations, notes, reminders, and birthdays will be deleted
-- 2. All WhatsApp message history will be cleared  
-- 3. All file records will be removed (but files may still exist in storage)
-- 4. All brain dump sessions will be cleared
-- 5. The bot will start fresh with no prior context
-- 
-- To fully reset:
-- 1. Run this SQL script in Supabase SQL Editor
-- 2. Clear the 'user-media' storage bucket manually
-- 3. Restart your bot server
-- 4. Send a test message to verify the bot creates new user records
-- ============================================================================
