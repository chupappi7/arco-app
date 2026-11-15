-- AI scheduling: library folders (one folder = one post), where each post
-- came from, the batch an agent made it in, and whether AI posts wait for a
-- person to approve them. Run once, after 008:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/009-ai.sql
CREATE TABLE IF NOT EXISTS library_folders (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  brand_id TEXT,
  name TEXT NOT NULL,
  note TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS library_folders_ws ON library_folders(workspace_id);
ALTER TABLE media ADD COLUMN folder_id TEXT;
ALTER TABLE media ADD COLUMN position INTEGER;
CREATE INDEX IF NOT EXISTS media_folder ON media(folder_id);
ALTER TABLE posts ADD COLUMN folder_id TEXT;
ALTER TABLE posts ADD COLUMN batch_id TEXT;
ALTER TABLE posts ADD COLUMN source TEXT;
CREATE INDEX IF NOT EXISTS posts_folder ON posts(folder_id);
CREATE INDEX IF NOT EXISTS posts_batch ON posts(batch_id);
ALTER TABLE workspaces ADD COLUMN ai_review INTEGER NOT NULL DEFAULT 1;
