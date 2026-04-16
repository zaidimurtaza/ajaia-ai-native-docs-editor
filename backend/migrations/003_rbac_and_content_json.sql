-- RBAC: viewer | editor on shares and share links; TipTap JSON in content_json

ALTER TABLE ajaia.document_shares
    ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'editor';

ALTER TABLE ajaia.document_shares DROP CONSTRAINT IF EXISTS document_shares_role_check;
ALTER TABLE ajaia.document_shares
    ADD CONSTRAINT document_shares_role_check CHECK (role IN ('viewer', 'editor'));

ALTER TABLE ajaia.documents ADD COLUMN IF NOT EXISTS share_token TEXT UNIQUE;
ALTER TABLE ajaia.documents ADD COLUMN IF NOT EXISTS share_token_role TEXT;

ALTER TABLE ajaia.documents DROP CONSTRAINT IF EXISTS documents_share_token_role_check;
ALTER TABLE ajaia.documents
    ADD CONSTRAINT documents_share_token_role_check
    CHECK (share_token_role IS NULL OR share_token_role IN ('viewer', 'editor'));

ALTER TABLE ajaia.documents ADD COLUMN IF NOT EXISTS content_json JSONB;
