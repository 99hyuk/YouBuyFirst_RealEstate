import { describe, expect, it } from 'vitest';

import { resolveBackendProxyTarget } from '../lib/backend-proxy-target';

describe('vite backend proxy config', () => {
  it('uses the explicit backend proxy target for local demo servers', () => {
    expect(resolveBackendProxyTarget({
      VITE_BACKEND_PROXY_TARGET: 'http://127.0.0.1:8081'
    })).toBe('http://127.0.0.1:8081');
  });

  it('keeps the Spring Boot default when no override is provided', () => {
    expect(resolveBackendProxyTarget({})).toBe('http://localhost:8080');
  });
});
