-- The library: photos uploaded ahead of time, kept until removed, picked from
-- when scheduling (each post gets its own copy). Run once, after 006:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/007-library.sql
ALTER TABLE media ADD COLUMN in_library INTEGER NOT NULL DEFAULT 0;
ALTER TABLE media ADD COLUMN brand_id TEXT;
ALTER TABLE media ADD COLUMN name TEXT;
CREATE INDEX IF NOT EXISTS media_library ON media(workspace_id, in_library);
