import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { resolveBackendProxyTarget } from '../lib/backend-proxy-target';

const testDir = dirname(fileURLToPath(import.meta.url));

describe('vite backend proxy config', () => {
  it('uses the explicit backend proxy target for local demo servers', () => {
    expect(resolveBackendProxyTarget({
      VITE_BACKEND_PROXY_TARGET: 'http://127.0.0.1:8081'
    })).toBe('http://127.0.0.1:8081');
  });

  it('keeps the Spring Boot default when no override is provided', () => {
    expect(resolveBackendProxyTarget({})).toBe('http://127.0.0.1:8080');
  });

  it('proxies OAuth login endpoints to the backend in local development', () => {
    const config = readFileSync(resolve(testDir, '../../vite.config.ts'), 'utf8');

    expect(config).toContain("'/oauth2'");
    expect(config).toContain("'/login/oauth2'");
  });

  it('allows public tunnel hostnames for OAuth callback demos', () => {
    const config = readFileSync(resolve(testDir, '../../vite.config.ts'), 'utf8');

    expect(config).toContain("'.trycloudflare.com'");
    expect(config).toContain("'.ngrok-free.dev'");
    expect(config).toContain("'.ngrok-free.app'");
  });
});
