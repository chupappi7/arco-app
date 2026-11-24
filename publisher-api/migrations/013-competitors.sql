-- Competitor channels a workspace follows, and one number per day for each,
-- so the page can show growth. Run once, after 012:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/013-competitors.sql
CREATE TABLE IF NOT EXISTS competitors (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  brand_id TEXT,
  platform TEXT NOT NULL DEFAULT 'youtube',
  channel_id TEXT NOT NULL,
  handle TEXT,
  title TEXT,
  avatar_url TEXT,
  subscribers INTEGER,
  views INTEGER,
  videos INTEGER,
  recent TEXT,
  stats_at INTEGER,
  created_at INTEGER NOT NULL,
  UNIQUE (workspace_id, platform, channel_id)
);
CREATE TABLE IF NOT EXISTS competitor_days (
  competitor_id TEXT NOT NULL,
  day TEXT NOT NULL,
  subscribers INTEGER,
  views INTEGER,
  PRIMARY KEY (competitor_id, day)
);
