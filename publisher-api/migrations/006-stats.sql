-- Numbers from the platforms: likes, comments, shares (and views where the
-- account allows it) per post, followers per account. Run once, after 005:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/006-stats.sql
ALTER TABLE posts ADD COLUMN stats TEXT;
ALTER TABLE posts ADD COLUMN stats_at INTEGER;
CREATE INDEX IF NOT EXISTS posts_stats ON posts(status, stats_at);
ALTER TABLE accounts ADD COLUMN followers INTEGER;
ALTER TABLE accounts ADD COLUMN stats_at INTEGER;
ALTER TABLE accounts ADD COLUMN insights_denied_at INTEGER;
CREATE TABLE IF NOT EXISTS follower_history (
  account_id TEXT NOT NULL,
  day TEXT NOT NULL,
  followers INTEGER NOT NULL,
  PRIMARY KEY (account_id, day)
);
