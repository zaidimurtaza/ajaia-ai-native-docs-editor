-- Ajaia collaborative docs — initial schema (isolated schema: ajaia)
-- Run in order via scripts/run_migrations.py

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS ajaia;

CREATE TABLE ajaia.users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ajaia.documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id     UUID NOT NULL REFERENCES ajaia.users (id) ON DELETE CASCADE,
    title        TEXT NOT NULL DEFAULT 'Untitled',
    yjs_state    BYTEA,
    initial_content TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_owner ON ajaia.documents (owner_id);

CREATE TABLE ajaia.document_shares (
    document_id UUID NOT NULL REFERENCES ajaia.documents (id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES ajaia.users (id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id, user_id)
);

CREATE INDEX idx_shares_user ON ajaia.document_shares (user_id);

CREATE TABLE ajaia.document_attachments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES ajaia.documents (id) ON DELETE CASCADE,
    filename     TEXT NOT NULL,
    content_type TEXT NOT NULL,
    byte_size    INTEGER NOT NULL,
    data         BYTEA NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attachments_doc ON ajaia.document_attachments (document_id);

-- Seeded demo users (password: demo — bcrypt cost 12)
INSERT INTO ajaia.users (email, display_name, password) VALUES
    (
        'alice@example.com',
        'Alice',
        '$2b$12$YgD8LOorjJAjmpFtK9.dquWyUuTiiBr/R0cKEVnT60RuQu6XcE2YC'
    ),
    (
        'bob@example.com',
        'Bob',
        '$2b$12$YgD8LOorjJAjmpFtK9.dquWyUuTiiBr/R0cKEVnT60RuQu6XcE2YC'
    );
