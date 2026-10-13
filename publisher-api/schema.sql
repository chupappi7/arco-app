CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL DEFAULT 'My workspace',
  timezone TEXT,                           -- IANA zone; NULL means the viewer's own
  slots TEXT,                              -- default posting times, JSON {days, times}
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
  brand_id TEXT,                           -- the brand it is grouped under, or NULL
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

-- Brands group a workspace's accounts the way Business Suite groups a Page
-- with its Instagram: "Client Bakery" = its TikTok, Instagram and Page.
CREATE TABLE IF NOT EXISTS brands (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  name TEXT NOT NULL,
  slots TEXT,                              -- posting times, JSON {days, times}; NULL = workspace default
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS brands_ws ON brands(workspace_id);

-- People. They sign in with email; TikTok, Instagram and Facebook are only
-- connections a workspace owns, never a way in.
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  created_at INTEGER NOT NULL,
  last_seen_at INTEGER
);

-- Who belongs to which workspace, as what. A member (not admin or owner) may
-- be limited to some brands: brand_ids is a JSON list, NULL meaning all.
CREATE TABLE IF NOT EXISTS memberships (
  workspace_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,                      -- owner | admin | member
  brand_ids TEXT,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS memberships_user ON memberships(user_id);

CREATE TABLE IF NOT EXISTS invites (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  email TEXT NOT NULL,
  role TEXT NOT NULL,
  brand_ids TEXT,
  token_hash TEXT NOT NULL UNIQUE,
  invited_by TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS invites_ws ON invites(workspace_id);

-- One-time sign-in codes, stored only as a keyed hash.
CREATE TABLE IF NOT EXISTS login_codes (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS login_codes_email ON login_codes(email, created_at);

CREATE TABLE IF NOT EXISTS sessions (
  id_hash TEXT PRIMARY KEY,
  workspace_id TEXT,
  user_id TEXT,                            -- NULL only for sessions from before email sign-in
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);

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
  group_id TEXT,                           -- posts made together (one composer submit)
  created_by TEXT,                         -- user who made it (told if it fails)
  notified INTEGER NOT NULL DEFAULT 0,     -- 1 once a failure has been emailed
  fail_reason TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS posts_due ON posts(status, next_attempt_at);
CREATE INDEX IF NOT EXISTS posts_ws ON posts(workspace_id, scheduled_at);
CREATE INDEX IF NOT EXISTS posts_drafts ON posts(workspace_id, status, updated_at);
