-- Drafts and post groups. Run once, after 004:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/005-drafts.sql
ALTER TABLE posts ADD COLUMN group_id TEXT;
CREATE INDEX IF NOT EXISTS posts_drafts ON posts(workspace_id, status, updated_at);
