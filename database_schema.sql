-- Cute WhatsApp Bot Database Schema
-- Run this in your Supabase SQL editor to set up the database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number TEXT UNIQUE NOT NULL,
    platform TEXT DEFAULT 'whatsapp',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    CONSTRAINT users_phone_number_check CHECK (length(phone_number) >= 10)
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    type TEXT NOT NULL CHECK (type IN ('note', 'reminder', 'birthday', 'slash_command', 'brain_dump')),
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    session_id UUID,
    vector_embedding VECTOR(1536), -- OpenAI ada-002 embeddings
    transcription TEXT,
    source_type TEXT NOT NULL CHECK (source_type IN ('text', 'image', 'audio', 'document')),
    origin_message_id TEXT,
    media_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    trigger_time TIMESTAMP WITH TIME ZONE NOT NULL,
    repeat_type TEXT DEFAULT 'none' CHECK (repeat_type IN ('none', 'daily', 'weekly', 'monthly', 'yearly')),
    repeat_interval INTEGER DEFAULT 1,
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Birthdays table
CREATE TABLE IF NOT EXISTS birthdays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    person_name TEXT NOT NULL,
    birthdate DATE NOT NULL, -- Year can be 1900 if unknown
    tags TEXT[] DEFAULT '{}',
    notification_settings JSONB DEFAULT '{"days_before": [1, 7], "enabled": true}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table for brain dump tracking
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'brain_dump',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'timeout', 'cancelled')),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Files/Storage table for media management
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    filename TEXT NOT NULL, -- Generated filename in storage
    original_filename TEXT NOT NULL, -- Original filename from user
    file_type TEXT NOT NULL CHECK (file_type IN ('image', 'audio', 'document', 'video')),
    mime_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    storage_path TEXT NOT NULL, -- Full path: user_folders/{user_id}/{filename}
    storage_bucket TEXT DEFAULT 'user-media',
    upload_status TEXT DEFAULT 'uploading' CHECK (upload_status IN ('uploading', 'completed', 'failed', 'deleted')),
    transcription_status TEXT DEFAULT 'pending' CHECK (transcription_status IN ('pending', 'processing', 'completed', 'failed', 'not_applicable')),
    transcription_text TEXT,
    duration_seconds INTEGER, -- For audio/video files
    dimensions JSONB, -- For images/videos: {"width": 1920, "height": 1080}
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT files_size_check CHECK (file_size_bytes > 0 AND file_size_bytes <= 52428800) -- 50MB limit
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(message_timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);
CREATE INDEX IF NOT EXISTS idx_messages_tags ON messages USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_messages_vector ON messages USING ivfflat (vector_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_trigger_time ON reminders(trigger_time);
CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active);

CREATE INDEX IF NOT EXISTS idx_birthdays_user_id ON birthdays(user_id);
CREATE INDEX IF NOT EXISTS idx_birthdays_date ON birthdays(birthdate);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_message_id ON files(message_id);
CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_upload_status ON files(upload_status);
CREATE INDEX IF NOT EXISTS idx_files_transcription_status ON files(transcription_status);

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE birthdays ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view own messages" ON messages FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own messages" ON messages FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own messages" ON messages FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own reminders" ON reminders FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own reminders" ON reminders FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own reminders" ON reminders FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own birthdays" ON birthdays FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own birthdays" ON birthdays FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own birthdays" ON birthdays FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own sessions" ON sessions FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own sessions" ON sessions FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own sessions" ON sessions FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own files" ON files FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can insert own files" ON files FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own files" ON files FOR UPDATE USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can delete own files" ON files FOR DELETE USING (auth.uid()::text = user_id::text);

-- Helper functions
CREATE OR REPLACE FUNCTION search_messages_by_vector(
    user_id UUID,
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    tags TEXT[],
    message_timestamp TIMESTAMP WITH TIME ZONE,
    similarity FLOAT
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
        1 - (m.vector_embedding <=> query_embedding) AS similarity
    FROM messages m
    WHERE m.user_id = search_messages_by_vector.user_id
    AND m.vector_embedding IS NOT NULL
    AND 1 - (m.vector_embedding <=> query_embedding) > match_threshold
    ORDER BY m.vector_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION get_user_tag_counts(user_id UUID)
RETURNS TABLE(tag TEXT, count BIGINT)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        unnest(m.tags) AS tag,
        COUNT(*) AS count
    FROM messages m
    WHERE m.user_id = get_user_tag_counts.user_id
    AND array_length(m.tags, 1) > 0
    GROUP BY unnest(m.tags)
    ORDER BY count DESC;
END;
$$;

CREATE OR REPLACE FUNCTION get_upcoming_birthdays(
    user_id UUID,
    days_ahead INT DEFAULT 30
)
RETURNS TABLE(
    id UUID,
    person_name TEXT,
    birthdate DATE,
    days_until_birthday INT,
    tags TEXT[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id,
        b.person_name,
        b.birthdate,
        CASE 
            WHEN EXTRACT(DOY FROM b.birthdate) >= EXTRACT(DOY FROM CURRENT_DATE)
            THEN EXTRACT(DOY FROM b.birthdate)::INT - EXTRACT(DOY FROM CURRENT_DATE)::INT
            ELSE 365 - EXTRACT(DOY FROM CURRENT_DATE)::INT + EXTRACT(DOY FROM b.birthdate)::INT
        END AS days_until_birthday,
        b.tags
    FROM birthdays b
    WHERE b.user_id = get_upcoming_birthdays.user_id
    AND (
        CASE 
            WHEN EXTRACT(DOY FROM b.birthdate) >= EXTRACT(DOY FROM CURRENT_DATE)
            THEN EXTRACT(DOY FROM b.birthdate)::INT - EXTRACT(DOY FROM CURRENT_DATE)::INT
            ELSE 365 - EXTRACT(DOY FROM CURRENT_DATE)::INT + EXTRACT(DOY FROM b.birthdate)::INT
        END
    ) <= days_ahead
    ORDER BY days_until_birthday;
END;
$$;

-- File management functions
CREATE OR REPLACE FUNCTION generate_user_file_path(
    user_id UUID,
    file_extension TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    filename TEXT;
    timestamp_str TEXT;
BEGIN
    -- Generate timestamp-based filename to avoid conflicts
    timestamp_str := EXTRACT(EPOCH FROM NOW())::BIGINT::TEXT;
    filename := timestamp_str || '_' || SUBSTRING(gen_random_uuid()::TEXT FROM 1 FOR 8) || file_extension;
    
    -- Return path: user_folders/{user_id}/{filename}
    RETURN 'user_folders/' || user_id::TEXT || '/' || filename;
END;
$$;

CREATE OR REPLACE FUNCTION get_user_storage_stats(user_id UUID)
RETURNS TABLE(
    total_files BIGINT,
    total_size_bytes BIGINT,
    total_size_mb NUMERIC,
    images_count BIGINT,
    audio_count BIGINT,
    documents_count BIGINT,
    videos_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) AS total_files,
        COALESCE(SUM(f.file_size_bytes), 0) AS total_size_bytes,
        ROUND(COALESCE(SUM(f.file_size_bytes), 0) / 1048576.0, 2) AS total_size_mb,
        COUNT(*) FILTER (WHERE f.file_type = 'image') AS images_count,
        COUNT(*) FILTER (WHERE f.file_type = 'audio') AS audio_count,
        COUNT(*) FILTER (WHERE f.file_type = 'document') AS documents_count,
        COUNT(*) FILTER (WHERE f.file_type = 'video') AS videos_count
    FROM files f
    WHERE f.user_id = get_user_storage_stats.user_id
    AND f.upload_status = 'completed'
    AND f.deleted_at IS NULL;
END;
$$;

CREATE OR REPLACE FUNCTION cleanup_failed_uploads()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    -- Mark files as deleted if they've been in 'uploading' or 'failed' status for more than 1 hour
    UPDATE files 
    SET deleted_at = NOW()
    WHERE upload_status IN ('uploading', 'failed')
    AND created_at < NOW() - INTERVAL '1 hour'
    AND deleted_at IS NULL;
    
    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    RETURN cleaned_count;
END;
$$;

-- Trigger to automatically create user folder path on first file upload
CREATE OR REPLACE FUNCTION ensure_user_folder()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- The actual folder creation will be handled by the application
    -- This trigger just ensures the path follows the correct pattern
    IF NEW.storage_path IS NULL OR NEW.storage_path = '' THEN
        NEW.storage_path := generate_user_file_path(NEW.user_id, '.tmp');
    END IF;
    
    RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_ensure_user_folder
    BEFORE INSERT ON files
    FOR EACH ROW
    EXECUTE FUNCTION ensure_user_folder();

-- Update messages table to have a proper relationship with files
ALTER TABLE messages ADD COLUMN IF NOT EXISTS file_id UUID REFERENCES files(id);
CREATE INDEX IF NOT EXISTS idx_messages_file_id ON messages(file_id);

-- Sample data (optional - for testing)
/*
INSERT INTO users (phone_number, platform) VALUES ('+1234567890', 'whatsapp');

INSERT INTO messages (user_id, type, content, tags, source_type) 
SELECT id, 'note', 'This is a sample note about work tasks', '{"work", "tasks"}', 'text'
FROM users WHERE phone_number = '+1234567890';

INSERT INTO reminders (user_id, title, trigger_time, tags)
SELECT id, 'Sample reminder', NOW() + INTERVAL '1 day', '{"work"}'
FROM users WHERE phone_number = '+1234567890';

INSERT INTO birthdays (user_id, person_name, birthdate, tags)
SELECT id, 'John Doe', '1990-05-15', '{"family"}'
FROM users WHERE phone_number = '+1234567890';

-- Sample file upload (image)
INSERT INTO files (user_id, message_id, filename, original_filename, file_type, mime_type, file_size_bytes, storage_path, upload_status)
SELECT 
    u.id, 
    m.id,
    '1640995200_a1b2c3d4.jpg',
    'photo.jpg',
    'image',
    'image/jpeg',
    2048576,
    'user_folders/' || u.id::TEXT || '/1640995200_a1b2c3d4.jpg',
    'completed'
FROM users u, messages m 
WHERE u.phone_number = '+1234567890' 
AND m.user_id = u.id 
LIMIT 1;
*/

-- Grant necessary permissions (adjust based on your needs)
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
