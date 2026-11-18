-- The API key encrypted (like account tokens), so the owner can copy it
-- again later, plus a name and when it was made. Run once, after 010:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/011-api-key-copy.sql
ALTER TABLE workspaces ADD COLUMN api_key_enc TEXT;
ALTER TABLE workspaces ADD COLUMN api_key_name TEXT;
ALTER TABLE workspaces ADD COLUMN api_key_at INTEGER;
