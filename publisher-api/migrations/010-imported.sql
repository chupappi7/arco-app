-- Past posts: every connected account's own posts (made in the apps, or before
-- it was connected) are read in with their numbers, so totals cover the whole
-- account. Imported rows are read-only: no R2 media, never queued, edited,
-- cancelled or retried. Run once, after 009:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/010-imported.sql
ALTER TABLE posts ADD COLUMN imported INTEGER NOT NULL DEFAULT 0;
ALTER TABLE posts ADD COLUMN media_url TEXT;
ALTER TABLE posts ADD COLUMN thumb_url TEXT;
CREATE INDEX IF NOT EXISTS posts_remote ON posts(account_id, public_post_id);
ALTER TABLE accounts ADD COLUMN imported_at INTEGER;
ALTER TABLE accounts ADD COLUMN import_cursor TEXT;
