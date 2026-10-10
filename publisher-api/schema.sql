CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL,
  api_key_hash TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS workspaces_api_key ON workspaces(api_key_hash);

CREATE TABLE IF NOT EXISTS accounts (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  open_id TEXT NOT NULL UNIQUE,         -- TikTok open_id, or ig:<id> / fb:<page id>
  platform TEXT NOT NULL DEFAULT 'tiktok', -- tiktok | instagram | facebook
  meta_user_id TEXT,                       -- the Facebook user who connected it
  can_sign_in INTEGER NOT NULL DEFAULT 0,  -- 1 if signing in with it opens its workspace
  username TEXT NOT NULL DEFAULT '',
  display_name TEXT NOT NULL DEFAULT '',
  avatar_url TEXT NOT NULL DEFAULT '',
  refresh_token_enc TEXT NOT NULL,
  access_token_enc TEXT,
  access_expires_at INTEGER,
  needs_reconnect INTEGER NOT NULL DEFAULT 0,
  connected_at INTEGER NOT NULL,
  token_updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS accounts_ws ON accounts(workspace_id);
CREATE INDEX IF NOT EXISTS accounts_meta_user ON accounts(meta_user_id);

CREATE TABLE IF NOT EXISTS sessions (
  id_hash TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS media (
  key TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  content_type TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  post_id TEXT,
  delete_after INTEGER
);
CREATE INDEX IF NOT EXISTS media_ws ON media(workspace_id);
CREATE INDEX IF NOT EXISTS media_delete ON media(delete_after);

CREATE TABLE IF NOT EXISTS posts (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  caption TEXT NOT NULL DEFAULT '',
  image_keys TEXT NOT NULL,
  cover_index INTEGER NOT NULL DEFAULT 0,
  settings TEXT NOT NULL,
  scheduled_at INTEGER NOT NULL,
  next_attempt_at INTEGER NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  publish_id TEXT,
  public_post_id TEXT,
  post_url TEXT,
  fail_reason TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS posts_due ON posts(status, next_attempt_at);
CREATE INDEX IF NOT EXISTS posts_ws ON posts(workspace_id, scheduled_at);
