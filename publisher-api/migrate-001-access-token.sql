-- Cache each account's access token so it is not refreshed on every call.
ALTER TABLE accounts ADD COLUMN access_token_enc TEXT;
ALTER TABLE accounts ADD COLUMN access_expires_at INTEGER;
