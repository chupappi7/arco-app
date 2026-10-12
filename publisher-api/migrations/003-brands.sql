-- Brands. Run once against the live database, after 002:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/003-brands.sql
CREATE TABLE IF NOT EXISTS brands (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS brands_ws ON brands(workspace_id);
ALTER TABLE accounts ADD COLUMN brand_id TEXT;
