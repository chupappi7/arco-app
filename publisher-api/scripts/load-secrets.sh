#!/usr/bin/env bash
# Load ARCO Publisher secrets from ~/.config/arco/*.env into the Worker and
# Vercel. Values go through stdin only and are never printed.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source ~/.config/arco/instagram.env; source ~/.config/arco/publisher.env; set +a

missing=0
for v in META_APP_ID META_APP_SECRET IG_APP_ID IG_APP_SECRET RESEND_API_KEY MAIL_FROM; do
  if [ -z "${!v:-}" ]; then echo "EMPTY: $v"; missing=1; fi
done
[ "$missing" = 0 ] || { echo "Fill ~/.config/arco/publisher.env first."; exit 1; }

for v in META_APP_ID META_APP_SECRET IG_APP_ID IG_APP_SECRET RESEND_API_KEY MAIL_FROM; do
  printf '%s' "${!v}" | npx wrangler secret put "$v" >/dev/null 2>&1 && echo "worker: $v loaded" || { echo "worker: $v FAILED"; exit 1; }
done

cd ../publisher
for v in META_APP_ID IG_APP_ID; do
  npx vercel env rm "$v" production -y >/dev/null 2>&1 || true
  printf '%s' "${!v}" | npx vercel env add "$v" production >/dev/null 2>&1 && echo "vercel: $v loaded" || { echo "vercel: $v FAILED"; exit 1; }
done
echo "All secrets loaded."
