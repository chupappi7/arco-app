import { env } from 'cloudflare:test';
import { describe, it, expect } from 'vitest';
import { randomToken, sha256Hex, encrypt, decrypt } from '../src/crypto.js';

describe('crypto', () => {
  it('sha256Hex matches the standard vector', async () => {
    expect(await sha256Hex('abc')).toBe(
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  });

  it('randomToken has the prefix and 2 hex chars per byte', () => {
    const t = randomToken('apk_', 16);
    expect(t).toMatch(/^apk_[0-9a-f]{32}$/);
    expect(randomToken('apk_', 16)).not.toBe(t);
  });

  it('encrypt/decrypt round-trips and never repeats ciphertext', async () => {
    const a = await encrypt('rft.secret', env.TOKEN_KEY);
    const b = await encrypt('rft.secret', env.TOKEN_KEY);
    expect(a).not.toBe(b);
    expect(a.startsWith('v1.')).toBe(true);
    expect(await decrypt(a, env.TOKEN_KEY)).toBe('rft.secret');
  });

  it('decrypt rejects tampered ciphertext', async () => {
    const a = await encrypt('rft.secret', env.TOKEN_KEY);
    const [v, iv, ct] = a.split('.');
    const flipped = ct.slice(0, -2) + (ct.slice(-2) === 'AA' ? 'AB' : 'AA');
    await expect(decrypt([v, iv, flipped].join('.'), env.TOKEN_KEY)).rejects.toThrow();
  });
});
