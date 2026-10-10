import { defineWorkersConfig } from '@cloudflare/vitest-pool-workers/config';

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: './wrangler.toml' },
        miniflare: {
          bindings: {
            // 32 bytes, base64: "0123456789abcdef0123456789abcdef"
            TOKEN_KEY: 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=',
            INTERNAL_SECRET: 'test-internal-secret',
            TIKTOK_CLIENT_KEY: 'test-client-key',
            TIKTOK_CLIENT_SECRET: 'test-client-secret',
            META_APP_ID: 'test-meta-app',
            META_APP_SECRET: 'test-meta-secret',
          },
        },
      },
    },
  },
});
