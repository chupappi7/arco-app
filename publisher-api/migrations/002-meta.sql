-- Instagram and Facebook accounts. Run once against the live database:
--   npx wrangler d1 execute arco-publisher --remote --file=migrations/002-meta.sql
-- (schema.sql already has these columns for a fresh database.)
ALTER TABLE accounts ADD COLUMN platform TEXT NOT NULL DEFAULT 'tiktok';
ALTER TABLE accounts ADD COLUMN meta_user_id TEXT;
ALTER TABLE posts ADD COLUMN post_url TEXT;
CREATE INDEX IF NOT EXISTS accounts_meta_user ON accounts(meta_user_id);
-- Only accounts that sign into their workspace may open it again; accounts
-- added to someone else's workspace may not. Existing accounts keep the
-- sign-in they have today.
ALTER TABLE accounts ADD COLUMN can_sign_in INTEGER NOT NULL DEFAULT 0;
UPDATE accounts SET can_sign_in = 1;
