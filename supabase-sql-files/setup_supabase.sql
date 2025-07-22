-- =====================================================
-- Cute WhatsApp Bot - Supabase Database Setup
-- Complete setup for pgvector and advanced features
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- 1. Add vector column to messages table
-- =====================================================

-- Add vector embedding column (OpenAI embeddings are 1536 dimensions)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS vector_embedding vector(1536);

-- Create vector similarity search index (speeds up vector queries)
CREATE INDEX IF NOT EXISTS messages_vector_embedding_idx 
ON messages USING ivfflat (vector_embedding vector_cosine_ops) 
WITH (lists = 100);

-- =====================================================
-- 2. Vector Search Function
-- =====================================================

CREATE OR REPLACE FUNCTION search_messages_by_vector(
  user_id uuid,
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  content text,
  tags text[],
  message_timestamp timestamptz,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.content,
    m.tags,
    m.timestamp as message_timestamp,
    1 - (m.vector_embedding <=> query_embedding) as similarity
  FROM messages m
  WHERE m.user_id = search_messages_by_vector.user_id
    AND m.vector_embedding IS NOT NULL
    AND 1 - (m.vector_embedding <=> query_embedding) > match_threshold
  ORDER BY m.vector_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- =====================================================
-- 3. Tag Analytics Function
-- =====================================================

CREATE OR REPLACE FUNCTION get_user_tag_counts(user_id uuid)
RETURNS TABLE (
  tag text,
  count bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    unnest(m.tags) as tag,
    COUNT(*) as count
  FROM messages m
  WHERE m.user_id = get_user_tag_counts.user_id
    AND m.tags IS NOT NULL
    AND array_length(m.tags, 1) > 0
  GROUP BY unnest(m.tags)
  ORDER BY count DESC;
END;
$$;

-- =====================================================
-- 4. Birthday Management Functions
-- =====================================================

CREATE OR REPLACE FUNCTION get_upcoming_birthdays(
  user_id uuid,
  days_ahead int DEFAULT 30
)
RETURNS TABLE (
  id uuid,
  person_name text,
  birthdate date,
  year_known boolean,
  days_until int
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    b.id,
    b.person_name,
    b.birthdate,
    b.year_known,
    CASE 
      WHEN EXTRACT(DOY FROM b.birthdate) >= EXTRACT(DOY FROM CURRENT_DATE) THEN
        EXTRACT(DOY FROM b.birthdate) - EXTRACT(DOY FROM CURRENT_DATE)
      ELSE
        (365 + EXTRACT(DOY FROM b.birthdate)) - EXTRACT(DOY FROM CURRENT_DATE)
    END::int as days_until
  FROM birthdays b
  WHERE b.user_id = get_upcoming_birthdays.user_id
    AND (
      CASE 
        WHEN EXTRACT(DOY FROM b.birthdate) >= EXTRACT(DOY FROM CURRENT_DATE) THEN
          EXTRACT(DOY FROM b.birthdate) - EXTRACT(DOY FROM CURRENT_DATE)
        ELSE
          (365 + EXTRACT(DOY FROM b.birthdate)) - EXTRACT(DOY FROM CURRENT_DATE)
      END
    ) <= days_ahead
  ORDER BY days_until ASC;
END;
$$;

-- =====================================================
-- 5. Text Search Functions (fallback when no vectors)
-- =====================================================

CREATE OR REPLACE FUNCTION search_messages_by_text(
  user_id uuid,
  search_query text,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  content text,
  tags text[],
  message_timestamp timestamptz,
  relevance float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.content,
    m.tags,
    m.timestamp as message_timestamp,
    ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', search_query)) as relevance
  FROM messages m
  WHERE m.user_id = search_messages_by_text.user_id
    AND (
      to_tsvector('english', m.content) @@ plainto_tsquery('english', search_query)
      OR m.content ILIKE '%' || search_query || '%'
    )
  ORDER BY relevance DESC, m.timestamp DESC
  LIMIT match_count;
END;
$$;

-- =====================================================
-- 6. Session Analytics Functions
-- =====================================================

CREATE OR REPLACE FUNCTION get_user_session_stats(user_id uuid)
RETURNS TABLE (
  total_sessions bigint,
  active_sessions bigint,
  avg_session_length interval,
  most_used_tags text[]
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE s.status = 'active') as active_sessions,
    AVG(COALESCE(s.end_time, NOW()) - s.start_time) as avg_session_length,
    ARRAY(
      SELECT unnest(s.tags) as tag
      FROM sessions s
      WHERE s.user_id = get_user_session_stats.user_id
        AND s.tags IS NOT NULL
      GROUP BY tag
      ORDER BY COUNT(*) DESC
      LIMIT 5
    ) as most_used_tags
  FROM sessions s
  WHERE s.user_id = get_user_session_stats.user_id;
END;
$$;

-- =====================================================
-- 7. Admin Analytics Functions
-- =====================================================

CREATE OR REPLACE FUNCTION get_admin_stats()
RETURNS TABLE (
  total_users bigint,
  total_messages bigint,
  active_sessions bigint,
  today_messages bigint,
  top_tags text[]
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM messages) as total_messages,
    (SELECT COUNT(*) FROM sessions WHERE status = 'active') as active_sessions,
    (SELECT COUNT(*) FROM messages WHERE DATE(timestamp) = CURRENT_DATE) as today_messages,
    ARRAY(
      SELECT unnest(tags) as tag
      FROM messages
      WHERE tags IS NOT NULL
      GROUP BY tag
      ORDER BY COUNT(*) DESC
      LIMIT 10
    ) as top_tags;
END;
$$;

-- =====================================================
-- 8. Bot Health Check Function
-- =====================================================

CREATE OR REPLACE FUNCTION enable_pgvector()
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
  -- Check if vector extension exists and is enabled
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
    RETURN true;
  ELSE
    -- Try to enable vector extension
    BEGIN
      CREATE EXTENSION vector;
      RETURN true;
    EXCEPTION
      WHEN OTHERS THEN
        RETURN false;
    END;
  END IF;
END;
$$;

-- =====================================================
-- 9. Full-Text Search Indexes (for better text search)
-- =====================================================

-- Create full-text search index for message content
CREATE INDEX IF NOT EXISTS messages_content_search_idx 
ON messages USING gin(to_tsvector('english', content));

-- Create index for tag searches
CREATE INDEX IF NOT EXISTS messages_tags_idx 
ON messages USING gin(tags);

-- Create index for user message queries
CREATE INDEX IF NOT EXISTS messages_user_timestamp_idx 
ON messages (user_id, timestamp DESC);

-- =====================================================
-- 10. Row Level Security (RLS) Policies
-- =====================================================

-- Enable RLS on messages table
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own messages
CREATE POLICY "Users can view own messages" ON messages
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own messages" ON messages
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Enable RLS on sessions table
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions" ON sessions
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own sessions" ON sessions
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own sessions" ON sessions
  FOR UPDATE USING (auth.uid()::text = user_id::text);

-- =====================================================
-- 11. Performance Optimization
-- =====================================================

-- Set maintenance work memory for better index creation
SET maintenance_work_mem = '256MB';

-- Analyze tables for better query planning
ANALYZE messages;
ANALYZE sessions;
ANALYZE users;
ANALYZE birthdays;
ANALYZE reminders;

-- =====================================================
-- 12. Database Triggers for Automation
-- =====================================================

-- Function to automatically update user last_seen
CREATE OR REPLACE FUNCTION update_user_last_seen()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE users 
  SET last_seen = NOW() 
  WHERE id = NEW.user_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_seen when message is inserted
DROP TRIGGER IF EXISTS trigger_update_user_last_seen ON messages;
CREATE TRIGGER trigger_update_user_last_seen
  AFTER INSERT ON messages
  FOR EACH ROW
  EXECUTE FUNCTION update_user_last_seen();

-- =====================================================
-- Setup Complete! 🎉
-- =====================================================

-- Test the setup
SELECT 'pgvector setup complete!' as status, enable_pgvector() as pgvector_enabled;
