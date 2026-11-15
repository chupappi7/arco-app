-- Video posts: a post holds photos (image_keys) or one library video
-- (video_key), which it points at instead of copying. Run once, after 007:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/008-video.sql
ALTER TABLE posts ADD COLUMN video_key TEXT;
ALTER TABLE media ADD COLUMN duration_ms INTEGER;
ALTER TABLE media ADD COLUMN width INTEGER;
ALTER TABLE media ADD COLUMN height INTEGER;
CREATE INDEX IF NOT EXISTS posts_video ON posts(video_key);
