-- Cute WhatsApp Bot - Additional Analytics Functions
-- Run this ONLY if you want extra analytics features
-- This is safe to run on top of your existing database_schema.sql

-- =====================================================
-- Text Search Function (fallback when no vectors)
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
    m.message_timestamp,
    ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', search_query)) as relevance
  FROM messages m
  WHERE m.user_id = search_messages_by_text.user_id
    AND (
      to_tsvector('english', m.content) @@ plainto_tsquery('english', search_query)
      OR m.content ILIKE '%' || search_query || '%'
    )
  ORDER BY relevance DESC, m.message_timestamp DESC
  LIMIT match_count;
END;
$$;

-- =====================================================
-- Advanced Analytics Functions
-- =====================================================

CREATE OR REPLACE FUNCTION get_user_activity_stats(
  user_id uuid,
  days_back int DEFAULT 30
)
RETURNS TABLE (
  total_messages bigint,
  notes_count bigint,
  reminders_count bigint,
  brain_dumps_count bigint,
  avg_messages_per_day numeric,
  most_active_day_of_week text,
  most_used_tags text[]
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH activity_data AS (
    SELECT 
      COUNT(*) as total_msgs,
      COUNT(*) FILTER (WHERE type = 'note') as notes,
      COUNT(*) FILTER (WHERE type = 'reminder') as reminders,
      COUNT(*) FILTER (WHERE type = 'brain_dump') as brain_dumps,
      EXTRACT(DOW FROM message_timestamp) as day_of_week,
      unnest(tags) as tag
    FROM messages m
    WHERE m.user_id = get_user_activity_stats.user_id
      AND m.message_timestamp >= NOW() - INTERVAL '1 day' * days_back
    GROUP BY EXTRACT(DOW FROM message_timestamp), unnest(tags)
  ),
  day_activity AS (
    SELECT 
      day_of_week,
      COUNT(*) as day_count,
      CASE day_of_week
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
      END as day_name
    FROM activity_data
    GROUP BY day_of_week
    ORDER BY day_count DESC
    LIMIT 1
  ),
  tag_popularity AS (
    SELECT array_agg(tag ORDER BY tag_count DESC) as popular_tags
    FROM (
      SELECT tag, COUNT(*) as tag_count
      FROM activity_data
      WHERE tag IS NOT NULL
      GROUP BY tag
      ORDER BY tag_count DESC
      LIMIT 5
    ) t
  )
  SELECT
    COALESCE(SUM(total_msgs), 0) as total_messages,
    COALESCE(SUM(notes), 0) as notes_count,
    COALESCE(SUM(reminders), 0) as reminders_count,
    COALESCE(SUM(brain_dumps), 0) as brain_dumps_count,
    ROUND(COALESCE(SUM(total_msgs), 0)::numeric / days_back, 2) as avg_messages_per_day,
    COALESCE((SELECT day_name FROM day_activity), 'N/A') as most_active_day_of_week,
    COALESCE((SELECT popular_tags FROM tag_popularity), '{}') as most_used_tags
  FROM activity_data;
END;
$$;

-- =====================================================
-- Reminder Analytics Function
-- =====================================================

CREATE OR REPLACE FUNCTION get_reminder_analytics(
  user_id uuid
)
RETURNS TABLE (
  total_reminders bigint,
  active_reminders bigint,
  completed_reminders bigint,
  overdue_reminders bigint,
  upcoming_24h bigint,
  completion_rate numeric
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*) as total_reminders,
    COUNT(*) FILTER (WHERE is_active = true AND completed_at IS NULL) as active_reminders,
    COUNT(*) FILTER (WHERE completed_at IS NOT NULL) as completed_reminders,
    COUNT(*) FILTER (WHERE is_active = true AND trigger_time < NOW() AND completed_at IS NULL) as overdue_reminders,
    COUNT(*) FILTER (WHERE is_active = true AND trigger_time BETWEEN NOW() AND NOW() + INTERVAL '24 hours') as upcoming_24h,
    CASE 
      WHEN COUNT(*) > 0 THEN 
        ROUND((COUNT(*) FILTER (WHERE completed_at IS NOT NULL))::numeric / COUNT(*) * 100, 1)
      ELSE 0
    END as completion_rate
  FROM reminders r
  WHERE r.user_id = get_reminder_analytics.user_id;
END;
$$;

-- =====================================================
-- Message Search with Combined Vector and Text
-- =====================================================

CREATE OR REPLACE FUNCTION smart_search_messages(
  user_id uuid,
  search_query text,
  query_embedding vector(1536) DEFAULT NULL,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  content text,
  tags text[],
  message_timestamp timestamptz,
  search_score float,
  search_type text
)
LANGUAGE plpgsql
AS $$
BEGIN
  -- If we have an embedding, use vector search
  IF query_embedding IS NOT NULL THEN
    RETURN QUERY
    SELECT
      m.id,
      m.content,
      m.tags,
      m.message_timestamp,
      1 - (m.vector_embedding <=> query_embedding) as search_score,
      'vector'::text as search_type
    FROM messages m
    WHERE m.user_id = smart_search_messages.user_id
      AND m.vector_embedding IS NOT NULL
    ORDER BY m.vector_embedding <=> query_embedding
    LIMIT match_count;
  ELSE
    -- Fallback to text search
    RETURN QUERY
    SELECT
      m.id,
      m.content,
      m.tags,
      m.message_timestamp,
      ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', search_query)) as search_score,
      'text'::text as search_type
    FROM messages m
    WHERE m.user_id = smart_search_messages.user_id
      AND (
        to_tsvector('english', m.content) @@ plainto_tsquery('english', search_query)
        OR m.content ILIKE '%' || search_query || '%'
      )
    ORDER BY search_score DESC, m.message_timestamp DESC
    LIMIT match_count;
  END IF;
END;
$$;

-- =====================================================
-- Full Text Search Index for better text search performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_messages_content_fts ON messages USING gin(to_tsvector('english', content));

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION search_messages_by_text(uuid, text, int) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_activity_stats(uuid, int) TO authenticated;
GRANT EXECUTE ON FUNCTION get_reminder_analytics(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION smart_search_messages(uuid, text, vector(1536), int) TO authenticated;
