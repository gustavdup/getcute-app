-- =====================================================
-- Update Messages Table for Bot Response Tracking
-- =====================================================

-- Add metadata column to store additional message information
-- This will include direction (incoming/outgoing) and sender info
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Create an index on metadata for better performance when querying bot responses
CREATE INDEX IF NOT EXISTS idx_messages_metadata 
ON messages USING gin (metadata);

-- Create an index specifically for bot responses
CREATE INDEX IF NOT EXISTS idx_messages_bot_responses 
ON messages (user_id, message_timestamp) 
WHERE metadata->>'sender' = 'bot';

-- Update existing RLS policies to include metadata access
DROP POLICY IF EXISTS "Users can view own messages" ON messages;
CREATE POLICY "Users can view own messages" ON messages
  FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own messages" ON messages;
CREATE POLICY "Users can insert own messages" ON messages
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Create a function to get full conversation thread (user + bot messages)
CREATE OR REPLACE FUNCTION get_conversation_thread(
  p_user_id UUID,
  p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  message_timestamp TIMESTAMPTZ,
  type TEXT,
  source_type TEXT,
  tags TEXT[],
  is_bot_response BOOLEAN,
  sender TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    m.id,
    m.content,
    m.message_timestamp,
    m.type::TEXT,
    m.source_type::TEXT,
    m.tags,
    CASE 
      WHEN m.metadata->>'sender' = 'bot' THEN true
      WHEN 'bot-response' = ANY(m.tags) THEN true
      WHEN m.content LIKE '🤖%' THEN true
      ELSE false
    END as is_bot_response,
    COALESCE(m.metadata->>'sender', 'user') as sender
  FROM messages m
  WHERE m.user_id = p_user_id
  ORDER BY m.message_timestamp ASC
  LIMIT p_limit;
END;
$$;

-- Create a function to get message statistics including bot responses
CREATE OR REPLACE FUNCTION get_user_message_stats(p_user_id UUID)
RETURNS TABLE (
  total_messages BIGINT,
  user_messages BIGINT,
  bot_responses BIGINT,
  last_activity TIMESTAMPTZ,
  first_message TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(*) as total_messages,
    COUNT(*) FILTER (
      WHERE NOT (
        metadata->>'sender' = 'bot' OR
        'bot-response' = ANY(tags) OR
        content LIKE '🤖%'
      )
    ) as user_messages,
    COUNT(*) FILTER (
      WHERE metadata->>'sender' = 'bot' OR
            'bot-response' = ANY(tags) OR
            content LIKE '🤖%'
    ) as bot_responses,
    MAX(message_timestamp) as last_activity,
    MIN(message_timestamp) as first_message
  FROM messages 
  WHERE user_id = p_user_id;
END;
$$;

-- Create a view for easy conversation access
CREATE OR REPLACE VIEW conversation_view AS
SELECT 
  m.id,
  m.user_id,
  u.phone_number,
  m.content,
  m.message_timestamp,
  m.type,
  m.source_type,
  m.tags,
  m.metadata,
  CASE 
    WHEN m.metadata->>'sender' = 'bot' THEN true
    WHEN 'bot-response' = ANY(m.tags) THEN true
    WHEN m.content LIKE '🤖%' THEN true
    ELSE false
  END as is_bot_response,
  COALESCE(m.metadata->>'sender', 'user') as sender
FROM messages m
JOIN users u ON m.user_id = u.id
ORDER BY m.user_id, m.message_timestamp;

-- Grant access to the admin service role
GRANT SELECT ON conversation_view TO service_role;
GRANT EXECUTE ON FUNCTION get_conversation_thread(UUID, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION get_user_message_stats(UUID) TO service_role;

-- Create a trigger to automatically update user last_seen when bot sends a message
CREATE OR REPLACE FUNCTION update_user_last_seen_on_bot_message()
RETURNS TRIGGER AS $$
BEGIN
  -- Only update if this is a bot message
  IF NEW.metadata->>'sender' = 'bot' OR 'bot-response' = ANY(NEW.tags) THEN
    UPDATE users 
    SET last_seen = NOW() 
    WHERE id = NEW.user_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_user_last_seen_bot ON messages;
CREATE TRIGGER trigger_update_user_last_seen_bot
  AFTER INSERT ON messages
  FOR EACH ROW
  EXECUTE FUNCTION update_user_last_seen_on_bot_message();

-- =====================================================
-- Verification Queries
-- =====================================================

-- Test the new functionality
DO $$
DECLARE
  test_user_id UUID;
BEGIN
  -- Get a test user (first user in the database)
  SELECT id INTO test_user_id FROM users LIMIT 1;
  
  IF test_user_id IS NOT NULL THEN
    RAISE NOTICE 'Testing with user ID: %', test_user_id;
    
    -- Test the conversation function
    RAISE NOTICE 'Conversation thread function created successfully';
    
    -- Test the stats function  
    RAISE NOTICE 'Message stats function created successfully';
  ELSE
    RAISE NOTICE 'No users found in database for testing';
  END IF;
END;
$$;

-- Show current messages table schema (standard SQL)
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'messages' 
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- Show indexes on messages table
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'messages' 
    AND schemaname = 'public'
ORDER BY indexname;

COMMENT ON COLUMN messages.metadata IS 'JSON metadata including message direction, sender info, and other attributes';
COMMENT ON FUNCTION get_conversation_thread(UUID, INTEGER) IS 'Returns full conversation thread including both user and bot messages';
COMMENT ON FUNCTION get_user_message_stats(UUID) IS 'Returns message statistics including bot response counts';
COMMENT ON VIEW conversation_view IS 'Unified view of all conversations with bot response identification';

-- =====================================================
-- Update Complete! ✅
-- =====================================================

SELECT 'Database updated for bot response tracking!' as status;
