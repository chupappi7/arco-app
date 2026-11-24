-- The bell: wins and problems the cron notices, one row per event, and when
-- each person last opened the list. Run once, after 013:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/014-notifications.sql
CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  brand_id TEXT,
  key TEXT NOT NULL,
  kind TEXT NOT NULL,
  tone TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  post_id TEXT,
  account_id TEXT,
  url TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE (workspace_id, key)
);
CREATE INDEX IF NOT EXISTS notifications_ws ON notifications(workspace_id, created_at);
CREATE TABLE IF NOT EXISTS notification_seen (
  workspace_id TEXT NOT NULL,
  who TEXT NOT NULL,
  seen_at INTEGER NOT NULL,
  PRIMARY KEY (workspace_id, who)
);
