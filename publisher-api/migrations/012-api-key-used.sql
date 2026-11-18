-- When the API key last signed something in, so the page can say an AI app
-- is connected. Run once, after 011:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/012-api-key-used.sql
ALTER TABLE workspaces ADD COLUMN api_key_used_at INTEGER;
