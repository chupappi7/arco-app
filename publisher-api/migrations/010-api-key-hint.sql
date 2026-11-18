-- The API key's last four characters, so the page can tell keys apart
-- without keeping the key itself. Run once, after 009:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/010-api-key-hint.sql
ALTER TABLE workspaces ADD COLUMN api_key_hint TEXT;
