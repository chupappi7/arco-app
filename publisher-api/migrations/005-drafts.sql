-- Drafts, post groups, time zones, posting slots, failure emails, AI writing. Run once, after 004:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/005-drafts.sql
ALTER TABLE posts ADD COLUMN group_id TEXT;
CREATE INDEX IF NOT EXISTS posts_drafts ON posts(workspace_id, status, updated_at);
ALTER TABLE workspaces ADD COLUMN timezone TEXT;
ALTER TABLE workspaces ADD COLUMN slots TEXT;
ALTER TABLE brands ADD COLUMN slots TEXT;
ALTER TABLE posts ADD COLUMN created_by TEXT;
ALTER TABLE posts ADD COLUMN notified INTEGER NOT NULL DEFAULT 0;
-- Failures from before this migration are not emailed after it.
UPDATE posts SET notified = 1 WHERE status = 'failed';
ALTER TABLE brands ADD COLUMN voice TEXT;
CREATE TABLE IF NOT EXISTS ai_usage (
  workspace_id TEXT NOT NULL,
  day TEXT NOT NULL,
  count INTEGER NOT NULL,
  PRIMARY KEY (workspace_id, day)
);
