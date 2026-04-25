-- ─────────────────────────────────────────────────────────────────
--  SECOND BRAIN — PostgreSQL Schema
--  Run automatically on first docker compose up
--  or manually: psql $DATABASE_URL -f schema.sql
-- ─────────────────────────────────────────────────────────────────

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for fuzzy text search

-- ── Documents ─────────────────────────────────────────────────────
-- Tracks every file ingested into the system
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename        TEXT NOT NULL,
    file_type       TEXT NOT NULL,                    -- pdf, docx, txt, url, video
    source_url      TEXT,                             -- for web/video ingestion
    blob_path       TEXT,                             -- Azure Blob Storage path
    chunk_count     INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'pending',           -- pending, processing, complete, error
    error_message   TEXT,
    tags            TEXT[] DEFAULT '{}',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_status   ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_type     ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_created  ON documents(created_at DESC);

-- ── Conversations ─────────────────────────────────────────────────
-- Each conversation session
CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT,                             -- auto-generated summary title
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    message_count   INTEGER DEFAULT 0,
    summary         TEXT,                             -- post-session summary
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_conversations_started ON conversations(started_at DESC);

-- ── Messages ──────────────────────────────────────────────────────
-- Every message turn within a conversation
CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    token_count     INTEGER,
    retrieved_chunks JSONB DEFAULT '[]',             -- doc chunks used for this response
    langsmith_run_id TEXT,                            -- link to LangSmith trace
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_created      ON messages(created_at DESC);

-- ── User Profile ──────────────────────────────────────────────────
-- Extracted facts, preferences, and style notes about the user
CREATE TABLE IF NOT EXISTS user_profile (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category        TEXT NOT NULL,     -- preference, fact, style, goal, relationship
    key             TEXT NOT NULL,     -- e.g. "communication_style", "name", "timezone"
    value           TEXT NOT NULL,
    confidence      FLOAT DEFAULT 1.0, -- 0.0 to 1.0
    source_conv_id  UUID REFERENCES conversations(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, key)              -- one value per key, upserted on update
);

CREATE INDEX IF NOT EXISTS idx_profile_category ON user_profile(category);
CREATE INDEX IF NOT EXISTS idx_profile_key      ON user_profile(key);

-- ── Ingestion Jobs ────────────────────────────────────────────────
-- Queue for async ingestion tasks
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    job_type        TEXT NOT NULL,     -- embed, transcribe, crawl
    status          TEXT DEFAULT 'queued',  -- queued, running, done, failed
    attempts        INTEGER DEFAULT 0,
    last_error      TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON ingestion_jobs(status, created_at);

-- ── Auto-update updated_at ────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_profile_updated_at
    BEFORE UPDATE ON user_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
